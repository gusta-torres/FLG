"""Provedor OpenAI com structured output via JSON Schema."""

from typing import Any

from openai import AsyncOpenAI
from pydantic import BaseModel

from app.config import Settings
from app.llm.base import LLMProvider


class OpenAIProvider(LLMProvider):
    def __init__(self, settings: Settings) -> None:
        self._client = AsyncOpenAI(api_key=settings.openai_api_key)
        self._model = settings.openai_model

    async def complete_json(self, system: str, user: str, schema: type[BaseModel]) -> Any:
        response = await self._client.beta.chat.completions.parse(
            model=self._model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            response_format=schema,
        )
        parsed = response.choices[0].message.parsed
        if parsed is None:
            raise RuntimeError("OpenAI não retornou um objeto estruturado válido.")
        return parsed
