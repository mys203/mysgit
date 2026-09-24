from __future__ import annotations

import json
import secrets
from datetime import date, datetime, timezone
from decimal import Decimal
from enum import Enum
from pathlib import Path
from uuid import UUID

import pytest
from pydantic import BaseModel, SecretStr

from app.ai.prompts import UNTRUSTED_END, UNTRUSTED_START, build_untrusted_data
from app.ai.provider import LangChainProvider
from app.config.settings import Settings


class CandidateStatus(str, Enum):
    ACTIVE = "ACTIVE"


class StructuredProbe(BaseModel):
    status: str


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


def extract_json(wrapped: str) -> dict:
    content = wrapped.split(UNTRUSTED_START, 1)[1].split(UNTRUSTED_END, 1)[0]
    return json.loads(content.strip())


def business_payload() -> dict:
    return {
        "created_at": datetime(2026, 9, 20, 12, 30, tzinfo=timezone.utc),
        "birth_date": date(1995, 5, 18),
        "salary": Decimal("12345.67"),
        "status": CandidateStatus.ACTIVE,
        "trace_id": UUID("12345678-1234-5678-1234-567812345678"),
        "resume_path": Path("uploads/resume.txt"),
        "nested": [
            {
                "updated_at": datetime(2026, 9, 21, 1, 2, 3),
                "amount": Decimal("0.10"),
            }
        ],
    }


def test_build_untrusted_data_preserves_typed_structure_as_json():
    wrapped = build_untrusted_data(business_payload())
    parsed = extract_json(wrapped)

    assert parsed["created_at"] == "2026-09-20T12:30:00+00:00"
    assert parsed["birth_date"] == "1995-05-18"
    assert parsed["salary"] == "12345.67"
    assert parsed["status"] == "ACTIVE"
    assert parsed["trace_id"] == "12345678-1234-5678-1234-567812345678"
    assert parsed["resume_path"] == str(Path("uploads/resume.txt"))
    assert parsed["nested"] == [
        {
            "updated_at": "2026-09-21T01:02:03",
            "amount": "0.10",
        }
    ]
    assert "datetime.datetime" not in wrapped
    assert "Decimal(" not in wrapped
    assert "CandidateStatus." not in wrapped


def test_deepseek_invoke_structured_accepts_business_model_payload(
    monkeypatch: pytest.MonkeyPatch,
):
    provider = LangChainProvider(
        make_settings(
            deepseek_api_key=SecretStr(
                f"test-deepseek-{secrets.token_urlsafe(24)}"
            )
        )
    )
    captured: dict[str, object] = {}

    def fake_invoke(messages, *, use_json_object: bool) -> str:
        captured["messages"] = messages
        captured["use_json_object"] = use_json_object
        return '{"status":"ok"}'

    monkeypatch.setattr(provider, "_invoke_deepseek_messages", fake_invoke)

    result = provider.invoke_structured(
        "分析招聘数据。",
        business_payload(),
        StructuredProbe,
    )

    assert result.status == "ok"
    assert captured["use_json_object"] is True
    messages = captured["messages"]
    assert isinstance(messages, list)
    parsed = extract_json(messages[1].content)
    assert parsed["created_at"] == "2026-09-20T12:30:00+00:00"
    assert parsed["salary"] == "12345.67"
    assert parsed["nested"][0]["amount"] == "0.10"
    assert "{" not in messages[1].content.split(UNTRUSTED_START, 1)[0]


def test_openai_compatible_invoke_structured_accepts_business_model_payload(
    monkeypatch: pytest.MonkeyPatch,
):
    provider = LangChainProvider(
        make_settings(
            llm_model="generic-model",
            llm_api_key=SecretStr(f"test-generic-{secrets.token_urlsafe(24)}"),
            llm_base_url="https://generic.example/v1",
        )
    )
    captured: dict[str, str] = {}

    class FakeChain:
        def invoke(self, values, config=None):
            captured["untrusted_data"] = values["untrusted_data"]
            return StructuredProbe(status="ok")

    class FakePrompt:
        def __or__(self, _other):
            return FakeChain()

    class FakeChatModel:
        def with_structured_output(self, _schema):
            return object()

    monkeypatch.setattr(
        "langchain_core.prompts.ChatPromptTemplate.from_messages",
        lambda _messages: FakePrompt(),
    )
    monkeypatch.setattr(provider, "_build_chat_model", lambda: FakeChatModel())

    result = provider.invoke_structured(
        "分析招聘数据。",
        business_payload(),
        StructuredProbe,
    )

    assert result.status == "ok"
    parsed = extract_json(captured["untrusted_data"])
    assert parsed["birth_date"] == "1995-05-18"
    assert parsed["status"] == "ACTIVE"
    assert parsed["trace_id"] == "12345678-1234-5678-1234-567812345678"
    assert parsed["resume_path"] == str(Path("uploads/resume.txt"))
