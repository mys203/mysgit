from __future__ import annotations

import logging
import secrets

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr, ValidationError

from app import main as main_module
from app.ai.provider import LangChainProvider
from app.config.settings import Settings


def make_settings(**overrides) -> Settings:
    values = {
        "_env_file": None,
        "app_env": "test",
        "llm_provider": "openai",
        "llm_model": None,
        "llm_api_key": None,
        "llm_base_url": None,
        "deepseek_api_key": None,
        "embedding_model": None,
        "embedding_api_key": None,
        "embedding_base_url": None,
    }
    values.update(overrides)
    return Settings(**values)


def test_deepseek_key_automatically_enables_compatible_chat_configuration():
    deepseek_key = f"test-deepseek-{secrets.token_urlsafe(24)}"
    config = make_settings(deepseek_api_key=SecretStr(deepseek_key))

    assert config.llm_configured is True
    assert config.effective_llm_provider == "deepseek"
    assert config.effective_llm_model == "deepseek-chat"
    assert config.effective_llm_base_url == "https://api.deepseek.com/v1"
    assert config.effective_llm_api_key is not None
    assert config.effective_llm_api_key.get_secret_value() == deepseek_key

    provider = LangChainProvider(config)
    assert provider.configured is True
    assert provider.provider_name == "deepseek"
    assert provider.model_name == "deepseek-chat"


def test_deepseek_provider_falls_back_to_deepseek_base_url_and_model(
    monkeypatch: pytest.MonkeyPatch,
):
    generic_key = f"test-generic-{secrets.token_urlsafe(24)}"
    config = make_settings(
        llm_provider="deepseek",
        llm_api_key=SecretStr(generic_key),
        llm_model=None,
        llm_base_url=None,
    )
    captured: dict[str, object] = {}

    class FakeChatOpenAI:
        def __init__(self, **kwargs) -> None:
            captured.update(kwargs)

    monkeypatch.setattr("langchain_openai.ChatOpenAI", FakeChatOpenAI)

    LangChainProvider(config)._build_chat_model()

    assert config.llm_configuration_error is None
    assert config.effective_llm_provider == "deepseek"
    assert config.effective_llm_model == "deepseek-chat"
    assert config.effective_llm_base_url == "https://api.deepseek.com/v1"
    assert captured["base_url"] == "https://api.deepseek.com/v1"
    assert captured["model"] == "deepseek-chat"


def test_deepseek_provider_rejects_non_deepseek_base_url():
    generic_key = f"test-generic-{secrets.token_urlsafe(24)}"
    config = make_settings(
        llm_provider="deepseek",
        llm_api_key=SecretStr(generic_key),
        llm_model="deepseek-chat",
        llm_base_url="https://api.openai.com/v1",
    )

    assert config.llm_configuration_error is not None
    assert "DeepSeek" in config.llm_configuration_error
    with pytest.raises(RuntimeError, match="DeepSeek"):
        LangChainProvider(config)._build_chat_model()


def test_deepseek_provider_reports_missing_credentials_before_request():
    config = make_settings(
        llm_provider="deepseek",
        llm_api_key=None,
        llm_model="deepseek-chat",
    )

    assert config.llm_configuration_error is not None
    assert "缺少" in config.llm_configuration_error
    with pytest.raises(RuntimeError, match="DeepSeek"):
        LangChainProvider(config)._build_chat_model()


def test_explicit_generic_llm_configuration_takes_precedence():
    generic_key = f"test-generic-{secrets.token_urlsafe(24)}"
    deepseek_key = f"test-deepseek-{secrets.token_urlsafe(24)}"
    config = make_settings(
        llm_provider="custom-openai-compatible",
        llm_model="generic-model",
        llm_api_key=SecretStr(generic_key),
        llm_base_url="https://generic.example/v1",
        deepseek_api_key=SecretStr(deepseek_key),
        deepseek_model="deepseek-reasoner",
        deepseek_base_url="https://deepseek.example/v1",
    )

    assert config.llm_configured is True
    assert config.effective_llm_provider == "custom-openai-compatible"
    assert config.effective_llm_model == "generic-model"
    assert config.effective_llm_base_url == "https://generic.example/v1"
    assert config.effective_llm_api_key is not None
    assert config.effective_llm_api_key.get_secret_value() == generic_key
    assert LangChainProvider(config).provider_name == "custom-openai-compatible"


def test_deepseek_does_not_implicitly_enable_or_reuse_embedding_credentials():
    deepseek_key = f"test-deepseek-{secrets.token_urlsafe(24)}"
    embedding_key = f"test-embedding-{secrets.token_urlsafe(24)}"

    without_embedding = make_settings(
        deepseek_api_key=SecretStr(deepseek_key),
        embedding_model="embedding-model",
    )
    assert without_embedding.embedding_configured is False
    assert without_embedding.effective_embedding_api_key is None
    assert without_embedding.effective_embedding_base_url is None

    with_separate_embedding = make_settings(
        deepseek_api_key=SecretStr(deepseek_key),
        embedding_model="embedding-model",
        embedding_api_key=SecretStr(embedding_key),
        embedding_base_url="https://embedding.example/v1",
    )
    assert with_separate_embedding.embedding_configured is True
    assert with_separate_embedding.effective_embedding_api_key is not None
    assert (
        with_separate_embedding.effective_embedding_api_key.get_secret_value()
        == embedding_key
    )
    assert (
        with_separate_embedding.effective_embedding_base_url
        == "https://embedding.example/v1"
    )


def test_secret_is_absent_from_repr_logs_and_responses(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
):
    deepseek_key = f"test-deepseek-{secrets.token_urlsafe(24)}"
    config = make_settings(deepseek_api_key=SecretStr(deepseek_key))

    assert deepseek_key not in repr(config)
    assert deepseek_key not in config.model_dump_json()
    assert deepseek_key not in config.redact_secrets(RuntimeError(f"调用失败：{deepseek_key}"))

    with caplog.at_level(logging.ERROR):
        logging.getLogger("tests.deepseek").error(
            "provider error: %s",
            config.redact_secrets(RuntimeError(f"鉴权失败：{deepseek_key}")),
        )
    assert deepseek_key not in caplog.text

    monkeypatch.setattr(main_module.settings, "llm_api_key", None)
    monkeypatch.setattr(main_module.settings, "llm_model", None)
    monkeypatch.setattr(main_module.settings, "deepseek_api_key", SecretStr(deepseek_key))
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["data"]["ai_degraded"] is False
    assert deepseek_key not in response.text


def test_unconfigured_llm_falls_back_without_degradation_false_positive():
    config = make_settings()
    provider = LangChainProvider(config)

    assert config.llm_configured is False
    assert config.effective_llm_api_key is None
    assert provider.configured is False
    assert provider.provider_name == "local"
    assert provider.model_name is None


def test_validation_error_does_not_expose_provider_secret():
    deepseek_key = f"test-deepseek-{secrets.token_urlsafe(24)}"

    with pytest.raises(ValidationError) as exc_info:
        Settings(
            _env_file=None,
            app_env="production",
            database_url=None,
            redis_url=None,
            jwt_secret_key=None,
            deepseek_api_key=SecretStr(deepseek_key),
        )

    assert deepseek_key not in str(exc_info.value)
