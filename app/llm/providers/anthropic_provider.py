"""Provedor Anthropic (Claude) com saída estruturada via tool use."""

import json
from typing import Any

from anthropic import AsyncAnthropic
from pydantic import BaseModel

from app.config import Settings
from app.llm.base import LLMProvider


class AnthropicProvider(LLMProvider):
    def __init__(self, settings: Settings) -> None:
        self._client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        self._model = settings.anthropic_model

    async def complete_json(self, system: str, user: str, schema: type[BaseModel]) -> Any:
        schema_json = schema.model_json_schema()
        response = await self._client.messages.create(
            model=self._model,
            max_tokens=4096,
            system=system,
            messages=[{"role": "user", "content": user}],
            tools=[
                {
                    "name": "respond_with_json",
                    "description": "Retorna o resultado estruturado conforme o schema.",
                    "input_schema": schema_json,
                }
            ],
            tool_choice={"type": "tool", "name": "respond_with_json"},
        )
        for block in response.content:
            if block.type == "tool_use":
                return schema.model_validate(json.loads(block.input))
        raise RuntimeError("Anthropic não retornou tool_use estruturado.")
