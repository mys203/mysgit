from __future__ import annotations

import re
import secrets
import string
import warnings
from functools import lru_cache
from pathlib import Path
from typing import Literal
from urllib.parse import urlparse

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]
UNSAFE_SECRET_MARKERS = (
    "请通过",
    "请修改",
    "change-me",
    "changeme",
    "example",
    "placeholder",
    "your-secret",
    "your-password",
    "admin123",
    "password",
)


def _plain_secret(value: SecretStr | None) -> str:
    return value.get_secret_value().strip() if value else ""


def _validate_jwt_secret(secret: str) -> None:
    lowered = secret.lower()
    if len(secret) < 48:
        raise ValueError("JWT_SECRET_KEY 长度不能少于 48 个字符")
    if len(set(secret)) < 16:
        raise ValueError("JWT_SECRET_KEY 字符多样性不足，疑似低熵或重复值")
    if any(marker in lowered for marker in UNSAFE_SECRET_MARKERS):
        raise ValueError("JWT_SECRET_KEY 包含示例或不安全占位内容")
    classes = sum(
        bool(regex.search(secret))
        for regex in (
            re.compile(r"[a-z]"),
            re.compile(r"[A-Z]"),
            re.compile(r"\d"),
            re.compile(rf"[{re.escape(string.punctuation)}]"),
        )
    )
    if classes < 3:
        raise ValueError("JWT_SECRET_KEY 必须至少包含大小写字母、数字、符号中的三类")


def _validate_admin_password(password: str, username: str | None) -> None:
    if not password:
        return
    lowered = password.lower()
    if len(password) < 12:
        raise ValueError("INITIAL_ADMIN_PASSWORD 长度不能少于 12 个字符")
    if username and password.lower() == username.lower():
        raise ValueError("INITIAL_ADMIN_PASSWORD 不能与管理员用户名相同")
    if any(marker in lowered for marker in UNSAFE_SECRET_MARKERS):
        raise ValueError("INITIAL_ADMIN_PASSWORD 包含示例或不安全占位内容")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        hide_input_in_errors=True,
    )

    app_name: str = "智能招聘系统"
    app_env: Literal["production", "development", "test"] = "production"
    debug: bool = False
    api_prefix: str = "/api/v1"

    database_url: str | None = None
    redis_url: str | None = None
    redis_required: bool = True
    redis_fallback_enabled: bool = False
    auto_create_tables: bool = False

    jwt_secret_key: SecretStr | None = None
    jwt_algorithm: str = "HS256"
    jwt_access_token_minutes: int = Field(default=30, ge=5, le=1440)
    jwt_refresh_token_days: int = Field(default=7, ge=1, le=30)
    jwt_issuer: str = "smart-recruitment"

    initial_admin_username: str | None = None
    initial_admin_password: SecretStr | None = None

    upload_dir: Path = BACKEND_DIR / "uploads"
    max_upload_mb: int = Field(default=10, ge=1, le=100)

    llm_provider: str = "openai"
    llm_model: str | None = None
    llm_api_key: SecretStr | None = None
    llm_base_url: str | None = None
    llm_timeout_seconds: int = Field(default=30, ge=5, le=180)
    llm_max_retries: int = Field(default=3, ge=1, le=6)
    embedding_model: str | None = None
    embedding_api_key: SecretStr | None = None
    embedding_base_url: str | None = None

    deepseek_api_key: SecretStr | None = None
    deepseek_model: str = "deepseek-chat"
    deepseek_base_url: str = "https://api.deepseek.com/v1"

    ai_prompt_version: str = "v1"
    ai_algorithm_version: str = "v1"
    ai_stale_task_seconds: int = Field(default=3600, ge=60, le=86400)

    cache_ttl_seconds: int = Field(default=60, ge=1, le=3600)
    ai_cache_ttl_seconds: int = Field(default=600, ge=30, le=86400)
    rate_limit_window_seconds: int = Field(default=60, ge=1, le=3600)
    rate_limit_default_requests: int = Field(default=120, ge=1, le=100000)

    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    @model_validator(mode="after")
    def validate_runtime_secrets(self) -> "Settings":
        jwt_secret = _plain_secret(self.jwt_secret_key)
        admin_password = _plain_secret(self.initial_admin_password)
        if self.app_env == "production":
            missing: list[str] = []
            if not self.database_url:
                missing.append("DATABASE_URL")
            if not self.redis_url:
                missing.append("REDIS_URL")
            if not jwt_secret:
                missing.append("JWT_SECRET_KEY")
            if missing:
                raise ValueError(f"生产环境缺少必要配置：{', '.join(missing)}")
            _validate_jwt_secret(jwt_secret)
            _validate_admin_password(admin_password, self.initial_admin_username)
        elif jwt_secret:
            _validate_jwt_secret(jwt_secret)
            _validate_admin_password(admin_password, self.initial_admin_username)

        if not self.database_url:
            self.database_url = "sqlite:///./recruit_local.db"
        if not self.redis_url:
            self.redis_url = "redis://127.0.0.1:6379/0"
        if not jwt_secret:
            self.jwt_secret_key = SecretStr(secrets.token_urlsafe(48))
            warnings.warn(
                "未设置 JWT_SECRET_KEY，已在开发或测试模式生成进程级临时密钥。",
                RuntimeWarning,
                stacklevel=2,
            )
        return self

    @property
    def sqlalchemy_database_url(self) -> str:
        if not self.database_url:
            raise RuntimeError("DATABASE_URL 未配置")
        if self.database_url.startswith("mysql://"):
            return self.database_url.replace("mysql://", "mysql+pymysql://", 1)
        return self.database_url

    @property
    def allowed_origins(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]

    @property
    def _has_generic_llm_key(self) -> bool:
        return bool(_plain_secret(self.llm_api_key))

    @property
    def _has_deepseek_llm_key(self) -> bool:
        return bool(_plain_secret(self.deepseek_api_key))

    @property
    def _normalized_llm_provider(self) -> str:
        return self.llm_provider.strip().lower() or "openai"

    @property
    def effective_llm_provider(self) -> str:
        if self._has_generic_llm_key:
            return self._normalized_llm_provider
        if self._has_deepseek_llm_key:
            return "deepseek"
        return self._normalized_llm_provider

    @property
    def effective_llm_model(self) -> str | None:
        if self.effective_llm_provider == "deepseek":
            configured_model = self.llm_model if self._has_generic_llm_key else None
            return (
                (configured_model or "").strip()
                or self.deepseek_model.strip()
                or "deepseek-chat"
            )
        if self._has_generic_llm_key:
            return self.llm_model
        return self.llm_model

    @property
    def effective_llm_base_url(self) -> str | None:
        if self.effective_llm_provider == "deepseek":
            configured_base_url = self.llm_base_url if self._has_generic_llm_key else None
            return (
                (configured_base_url or "").strip()
                or self.deepseek_base_url.strip()
                or "https://api.deepseek.com/v1"
            )
        if self._has_generic_llm_key:
            return self.llm_base_url
        return self.llm_base_url

    @property
    def effective_llm_api_key(self) -> SecretStr | None:
        if self._has_generic_llm_key:
            return self.llm_api_key
        if self._has_deepseek_llm_key:
            return self.deepseek_api_key
        return None

    @property
    def uses_deepseek_endpoint(self) -> bool:
        if self.effective_llm_provider == "deepseek":
            return True
        base_url = self.effective_llm_base_url or ""
        return "api.deepseek.com" in base_url.lower()

    @staticmethod
    def _is_deepseek_url(base_url: str) -> bool:
        parsed = urlparse(base_url)
        hostname = (parsed.hostname or "").lower()
        return parsed.scheme in {"http", "https"} and (
            hostname == "api.deepseek.com" or hostname.endswith(".deepseek.com")
        )

    @property
    def llm_configuration_error(self) -> str | None:
        if self.effective_llm_provider != "deepseek":
            return None
        if not self.effective_llm_api_key:
            return "DeepSeek 配置缺少 LLM_API_KEY 或 DEEPSEEK_API_KEY"
        if not self.effective_llm_model:
            return "DeepSeek 配置缺少 LLM_MODEL 和 DEEPSEEK_MODEL"
        base_url = self.effective_llm_base_url
        if not base_url:
            return "DeepSeek 配置缺少 LLM_BASE_URL 和 DEEPSEEK_BASE_URL"
        if not self._is_deepseek_url(base_url):
            return "DeepSeek provider 的 base_url 必须指向 DeepSeek 官方域名"
        return None

    @property
    def effective_embedding_api_key(self) -> SecretStr | None:
        if not self.embedding_model:
            return None
        if _plain_secret(self.embedding_api_key):
            return self.embedding_api_key
        if self.uses_deepseek_endpoint:
            return None
        return self.llm_api_key if self._has_generic_llm_key else None

    @property
    def effective_embedding_base_url(self) -> str | None:
        if not self.embedding_model:
            return None
        if self.embedding_base_url:
            return self.embedding_base_url
        if self.uses_deepseek_endpoint:
            return None
        return self.llm_base_url if self._has_generic_llm_key else None

    @property
    def embedding_configured(self) -> bool:
        return bool(self.embedding_model and self.effective_embedding_api_key)

    @property
    def llm_configured(self) -> bool:
        return bool(self.effective_llm_model and self.effective_llm_api_key)

    def redact_secrets(self, value: object) -> str:
        text = str(value)
        secrets_to_hide = {
            _plain_secret(self.llm_api_key),
            _plain_secret(self.deepseek_api_key),
            _plain_secret(self.embedding_api_key),
        }
        for secret in sorted((item for item in secrets_to_hide if item), key=len, reverse=True):
            text = text.replace(secret, "***")
        return text

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
