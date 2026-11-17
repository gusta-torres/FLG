import pytest

from app.config import Settings
from app.llm.base import ProviderFactory
from app.llm.providers.deepseek_provider import DeepSeekProvider


def test_factory_returns_deepseek_provider():
    settings = Settings(llm_provider="deepseek", deepseek_api_key="fake-key")
    provider = ProviderFactory.create(settings)
    assert isinstance(provider, DeepSeekProvider)


def test_deepseek_requires_api_key():
    settings = Settings(llm_provider="deepseek", deepseek_api_key="")
    with pytest.raises(RuntimeError):
        ProviderFactory.create(settings)


def test_factory_defaults_to_mock():
    from app.llm.providers.mock_provider import MockProvider

    settings = Settings(llm_provider="mock")
    assert isinstance(ProviderFactory.create(settings), MockProvider)
