from __future__ import annotations

import logging
import threading
import time
from typing import Any

import redis

from app.config.settings import settings

logger = logging.getLogger(__name__)


class MemoryRedis:
    """开发与测试模式的进程内 Redis 等价实现，所有写入必须显式提供 TTL。"""

    def __init__(self) -> None:
        self._data: dict[str, tuple[float | None, Any]] = {}
        self._lock = threading.RLock()

    def _purge_if_expired(self, key: str) -> None:
        item = self._data.get(key)
        if item and item[0] is not None and item[0] <= time.time():
            self._data.pop(key, None)

    def get(self, key: str) -> Any:
        with self._lock:
            self._purge_if_expired(key)
            item = self._data.get(key)
            return item[1] if item else None

    def set(self, key: str, value: Any, ex: int | None = None) -> bool:
        if ex is None or ex <= 0:
            raise ValueError("Redis 写入必须设置正数 TTL")
        with self._lock:
            self._data[key] = (time.time() + ex, value)
        return True

    def set_nx(self, key: str, value: Any, ex: int) -> bool:
        if ex <= 0:
            raise ValueError("Redis 写入必须设置正数 TTL")
        with self._lock:
            self._purge_if_expired(key)
            if key in self._data:
                return False
            self._data[key] = (time.time() + ex, value)
            return True

    def delete(self, *keys: str) -> int:
        with self._lock:
            count = 0
            for key in keys:
                count += int(self._data.pop(key, None) is not None)
            return count

    def exists(self, key: str) -> int:
        with self._lock:
            self._purge_if_expired(key)
            return int(key in self._data)

    def incr(self, key: str) -> int:
        return self.increment_with_ttl(key, 60)

    def increment_with_ttl(self, key: str, ttl: int) -> int:
        if ttl <= 0:
            raise ValueError("Redis TTL 必须为正数")
        with self._lock:
            self._purge_if_expired(key)
            item = self._data.get(key)
            if item:
                current = int(item[1]) + 1
                expires_at = item[0] if item[0] is not None else time.time() + ttl
            else:
                current = 1
                expires_at = time.time() + ttl
            self._data[key] = (expires_at, current)
            return current

    def expire(self, key: str, seconds: int) -> bool:
        if seconds <= 0:
            raise ValueError("Redis TTL 必须为正数")
        with self._lock:
            self._purge_if_expired(key)
            item = self._data.get(key)
            if not item:
                return False
            self._data[key] = (time.time() + seconds, item[1])
            return True

    def ttl(self, key: str) -> int:
        with self._lock:
            self._purge_if_expired(key)
            item = self._data.get(key)
            if not item:
                return -2
            if item[0] is None:
                return -1
            return max(0, int(item[0] - time.time()))

    def ping(self) -> bool:
        return True


class RedisManager:
    def __init__(self) -> None:
        self._client: redis.Redis | MemoryRedis | None = None
        self.degraded = False

    @property
    def client(self) -> redis.Redis | MemoryRedis:
        if self._client is None:
            self.initialize()
        if self._client is None:
            raise RuntimeError("Redis 尚未初始化")
        return self._client

    def initialize(self) -> None:
        if self._client is not None:
            return
        try:
            client = redis.Redis.from_url(
                settings.redis_url,
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=2,
                health_check_interval=30,
            )
            client.ping()
            self._client = client
            logger.info("Redis 连接成功")
        except Exception as exc:
            if settings.is_production or settings.redis_required:
                raise RuntimeError("生产或强制模式下 Redis 不可用，服务拒绝启动") from exc
            if not settings.redis_fallback_enabled:
                raise RuntimeError("Redis 不可用且未开启开发降级") from exc
            self._client = MemoryRedis()
            self.degraded = True
            logger.warning("Redis 不可用，开发或测试模式已降级为进程内存储：%s", exc)

    def close(self) -> None:
        client = self._client
        if client is not None and hasattr(client, "close"):
            client.close()
        self._client = None

    def get(self, key: str) -> str | None:
        value = self.client.get(key)
        return str(value) if value is not None else None

    def set(self, key: str, value: str, ttl: int) -> bool:
        if ttl <= 0:
            raise ValueError("Redis TTL 必须为正数")
        return bool(self.client.set(key, value, ex=ttl))

    def set_nx(self, key: str, value: str, ttl: int) -> bool:
        if ttl <= 0:
            raise ValueError("Redis TTL 必须为正数")
        if isinstance(self.client, MemoryRedis):
            return self.client.set_nx(key, value, ex=ttl)
        return bool(self.client.set(key, value, ex=ttl, nx=True))

    def delete(self, *keys: str) -> int:
        return int(self.client.delete(*keys))

    def exists(self, key: str) -> bool:
        return bool(self.client.exists(key))

    def increment(self, key: str, ttl: int) -> int:
        if ttl <= 0:
            raise ValueError("Redis TTL 必须为正数")
        if isinstance(self.client, MemoryRedis):
            return self.client.increment_with_ttl(key, ttl)
        script = """
local current = redis.call('INCR', KEYS[1])
local current_ttl = redis.call('TTL', KEYS[1])
if current == 1 or current_ttl < 0 then
  redis.call('EXPIRE', KEYS[1], ARGV[1])
end
return current
"""
        return int(self.client.eval(script, 1, key, ttl))


redis_manager = RedisManager()
