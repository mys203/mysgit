from __future__ import annotations

import json
import secrets

import pytest
from pydantic import BaseModel, SecretStr

from app.ai.provider import LangChainProvider
from app.config.settings import Settings


class StructuredProbe(BaseModel):
    status: str
    question_count: int
    questions: list[str]


class BadRequestError(Exception):
    status_code = 400


def make_settings(**overrides) -> Settings:
    values = {
        "_env_file": None,
        "app_env": "test",
        "llm_provider": "openai",
        "llm_model": None,
        "llm_api_key": None,
        "llm_base_url": None,
        "deepseek_api_key": None,
    }
    values.update(overrides)
    return Settings(**values)


def make_deepseek_provider() -> LangChainProvider:
    return LangChainProvider(
        make_settings(
            deepseek_api_key=SecretStr(
                f"test-deepseek-{secrets.token_urlsafe(24)}"
            )
        )
    )


def valid_payload() -> str:
    return json.dumps(
        {
            "status": "ok",
            "question_count": 1,
            "questions": ["请介绍 Python 的 GIL。"],
        },
        ensure_ascii=False,
    )


def test_deepseek_json_object_success_uses_schema_prompt_and_boundary(
    monkeypatch: pytest.MonkeyPatch,
):
    provider = make_deepseek_provider()
    captured: dict[str, object] = {}

    def fake_invoke(messages, *, use_json_object: bool) -> str:
        captured["messages"] = messages
        captured["use_json_object"] = use_json_object
        return valid_payload()

    monkeypatch.setattr(provider, "_invoke_deepseek_messages", fake_invoke)

    result = provider.invoke_structured(
        "生成一道 Python 面试题。",
        {"topic": "Python"},
        StructuredProbe,
    )

    assert result.question_count == 1
    assert result.status == "ok"
    assert captured["use_json_object"] is True
    messages = captured["messages"]
    assert isinstance(messages, list)
    assert "JSON Schema" in messages[0].content
    assert "question_count" in messages[0].content
    assert "<<<UNTRUSTED_DATA_START>>>" in messages[1].content
    assert messages[1].content.endswith("<<<UNTRUSTED_DATA_END>>>")


def test_deepseek_parses_json_from_markdown_code_block(
    monkeypatch: pytest.MonkeyPatch,
):
    provider = make_deepseek_provider()
    monkeypatch.setattr(
        provider,
        "_invoke_deepseek_messages",
        lambda *_args, **_kwargs: f"```json\n{valid_payload()}\n```",
    )

    result = provider.invoke_structured("生成题目。", {}, StructuredProbe)

    assert result.question_count == 1
    assert result.questions


def test_deepseek_repairs_invalid_json_once_then_revalidates(
    monkeypatch: pytest.MonkeyPatch,
):
    provider = make_deepseek_provider()
    responses: list[str] = ["{不是合法 JSON}", valid_payload()]
    calls: list[dict[str, object]] = []

    def fake_invoke(messages, *, use_json_object: bool) -> str:
        calls.append(
            {
                "messages": messages,
                "use_json_object": use_json_object,
            }
        )
        return responses.pop(0)

    monkeypatch.setattr(provider, "_invoke_deepseek_messages", fake_invoke)

    result = provider.invoke_structured("生成题目。", {}, StructuredProbe)

    assert result.question_count == 1
    assert len(calls) == 2
    assert calls[0]["use_json_object"] is True
    assert calls[1]["use_json_object"] is True
    repair_messages = calls[1]["messages"]
    assert isinstance(repair_messages, list)
    assert "只修复" in repair_messages[0].content
    assert "<<<UNTRUSTED_DATA_START>>>" in repair_messages[1].content


def test_deepseek_stops_after_one_failed_json_repair(
    monkeypatch: pytest.MonkeyPatch,
):
    provider = make_deepseek_provider()
    calls: list[bool] = []

    def fake_invoke(_messages, *, use_json_object: bool) -> str:
        calls.append(use_json_object)
        return "{仍然不是合法 JSON}"

    monkeypatch.setattr(provider, "_invoke_deepseek_messages", fake_invoke)

    with pytest.raises(json.JSONDecodeError):
        provider.invoke_structured("生成题目。", {}, StructuredProbe)

    assert calls == [True, True]


def test_deepseek_400_falls_back_to_prompt_only_json(
    monkeypatch: pytest.MonkeyPatch,
):
    provider = make_deepseek_provider()
    calls: list[bool] = []

    def fake_invoke(_messages, *, use_json_object: bool) -> str:
        calls.append(use_json_object)
        if use_json_object:
            raise BadRequestError("This response_format type is unavailable now")
        return valid_payload()

    monkeypatch.setattr(provider, "_invoke_deepseek_messages", fake_invoke)

    result = provider.invoke_structured("生成题目。", {}, StructuredProbe)

    assert result.question_count == 1
    assert calls == [True, False]


def test_non_deepseek_provider_keeps_structured_output_path(
    monkeypatch: pytest.MonkeyPatch,
):
    config = make_settings(
        llm_provider="openai",
        llm_model="generic-model",
        llm_api_key=SecretStr(f"test-generic-{secrets.token_urlsafe(24)}"),
        llm_base_url="https://generic.example/v1",
    )
    provider = LangChainProvider(config)
    expected = StructuredProbe(
        status="ok",
        question_count=1,
        questions=["兼容链路"],
    )
    calls: list[str] = []

    def fake_structured(
        _system_prompt: str,
        _payload: dict[str, object],
        _schema: type[StructuredProbe],
    ) -> StructuredProbe:
        calls.append("with_structured_output")
        return expected

    monkeypatch.setattr(
        provider,
        "_invoke_openai_compatible_structured",
        fake_structured,
    )

    result = provider.invoke_structured("生成题目。", {}, StructuredProbe)

    assert result is expected
    assert calls == ["with_structured_output"]
