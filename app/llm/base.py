"""Abstração da camada de LLM com saída estruturada."""

from abc import ABC, abstractmethod
from typing import Any, TypeVar

from pydantic import BaseModel

from app.config import Settings

T = TypeVar("T", bound=BaseModel)


class LLMProvider(ABC):
    """Contrato comum para provedores de LLM."""

    @abstractmethod
    async def complete_json(self, system: str, user: str, schema: type[T]) -> T:
        """Gera uma resposta estruturada conformando ao schema Pydantic informado."""


class ProviderFactory:
    """Seleciona o provedor com base na configuração."""

    @staticmethod
    def create(settings: Settings) -> LLMProvider:
        provider = settings.llm_provider.lower()
        if provider == "openai":
            from app.llm.providers.openai_provider import OpenAIProvider

            return OpenAIProvider(settings)
        if provider == "anthropic":
            from app.llm.providers.anthropic_provider import AnthropicProvider

            return AnthropicProvider(settings)
        if provider == "deepseek":
            from app.llm.providers.deepseek_provider import DeepSeekProvider

            return DeepSeekProvider(settings)
        from app.llm.providers.mock_provider import MockProvider

        return MockProvider(settings)
