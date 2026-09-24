from __future__ import annotations

import os
import secrets
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

TEST_ROOT = Path(tempfile.mkdtemp(prefix="recruit-tests-"))
TEST_PASSWORD = secrets.token_urlsafe(18)
os.environ.update(
    {
        "APP_ENV": "test",
        "DEBUG": "false",
        "DATABASE_URL": f"sqlite:///{(TEST_ROOT / 'test.db').as_posix()}",
        "REDIS_URL": "redis://127.0.0.1:6399/15",
        "REDIS_REQUIRED": "false",
        "REDIS_FALLBACK_ENABLED": "true",
        "JWT_SECRET_KEY": secrets.token_urlsafe(48),
        "JWT_ACCESS_TOKEN_MINUTES": "30",
        "JWT_REFRESH_TOKEN_DAYS": "7",
        "AUTO_CREATE_TABLES": "true",
        "INITIAL_ADMIN_USERNAME": "admin",
        "INITIAL_ADMIN_PASSWORD": TEST_PASSWORD,
        "UPLOAD_DIR": str(TEST_ROOT / "uploads"),
        "RATE_LIMIT_DEFAULT_REQUESTS": "10000",
        "LLM_MODEL": "",
        "LLM_API_KEY": "",
        "DEEPSEEK_API_KEY": "",
        "EMBEDDING_MODEL": "",
        "EMBEDDING_API_KEY": "",
        "EMBEDDING_BASE_URL": "",
    }
)

from app.main import app  # noqa: E402
from app.config.redis import MemoryRedis, redis_manager  # noqa: E402


@pytest.fixture(autouse=True)
def reset_memory_redis():
    if isinstance(redis_manager.client, MemoryRedis):
        with redis_manager.client._lock:
            redis_manager.client._data.clear()
    yield


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def auth_headers(client: TestClient) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": TEST_PASSWORD},
    )
    assert response.status_code == 200, response.text
    token = response.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}
