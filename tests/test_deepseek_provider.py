import json
from types import SimpleNamespace

import pytest

from app.config import Settings
from app.llm.providers.deepseek_provider import DeepSeekProvider
from app.schemas import DiagnosticProfile

PROFILE_PAYLOAD = {
    "dominant_archetype": "nerd_rico_analitico",
    "secondary_archetype": "professor_low_profile",
    "central_thesis": "Previsibilidade nasce de método e dados, não de achismo.",
    "channel_allocation": [
        {
            "channel": "linkedin",
            "role": "primario",
            "dedication_percent": 70,
            "native_formats": ["artigo_linkedin", "carrossel"],
        },
        {
            "channel": "youtube",
            "role": "secundario",
            "dedication_percent": 30,
            "native_formats": ["video_longo"],
        },
    ],
}


def _provider() -> DeepSeekProvider:
    return DeepSeekProvider(Settings(llm_provider="deepseek", deepseek_api_key="fake"))


def _fake_response(content: str):
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=content))]
    )


async def test_deepseek_parses_valid_profile(monkeypatch):
    provider = _provider()

    async def fake_create(**kwargs):
        return _fake_response(json.dumps(PROFILE_PAYLOAD))

    monkeypatch.setattr(provider._client.chat.completions, "create", fake_create)

    profile = await provider.complete_json("sys", "user", DiagnosticProfile)
    assert profile.dominant_archetype.value == "nerd_rico_analitico"
    assert profile.secondary_archetype.value == "professor_low_profile"
    assert len(profile.channel_allocation) == 2


async def test_deepseek_retries_on_invalid_json(monkeypatch):
    provider = _provider()
    calls = {"n": 0}

    async def fake_create(**kwargs):
        calls["n"] += 1
        if calls["n"] == 1:
            return _fake_response(json.dumps({"dominant_archetype": "invalido"}))
        return _fake_response(json.dumps(PROFILE_PAYLOAD))

    monkeypatch.setattr(provider._client.chat.completions, "create", fake_create)

    profile = await provider.complete_json("sys", "user", DiagnosticProfile)
    assert calls["n"] == 2
    assert profile.dominant_archetype.value == "nerd_rico_analitico"


async def test_deepseek_raises_after_two_invalid_attempts(monkeypatch):
    provider = _provider()

    async def fake_create(**kwargs):
        return _fake_response("não é json")

    monkeypatch.setattr(provider._client.chat.completions, "create", fake_create)

    with pytest.raises(RuntimeError):
        await provider.complete_json("sys", "user", DiagnosticProfile)
