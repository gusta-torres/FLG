"""Provedor DeepSeek.

A API do DeepSeek é compatível com a da OpenAI, então reaproveitamos o SDK
`openai` apenas trocando o `base_url`. O DeepSeek não oferece o endpoint de
"parse" estruturado da OpenAI, por isso usamos o *JSON mode*
(`response_format={"type": "json_object"}`), validamos a saída com Pydantic e
fazemos uma segunda tentativa com feedback do erro caso o JSON venha inválido.
"""

import json
from typing import Any

from openai import AsyncOpenAI
from pydantic import BaseModel, ValidationError

from app.config import Settings
from app.llm.base import LLMProvider

# deepseek-chat suporta até 8192 tokens de saída.
_MAX_TOKENS = 8000
_MAX_ATTEMPTS = 2


class DeepSeekProvider(LLMProvider):
    def __init__(self, settings: Settings) -> None:
        if not settings.deepseek_api_key:
            raise RuntimeError(
                "DEEPSEEK_API_KEY não configurada. Defina no .env ou use LLM_PROVIDER=mock."
            )
        self._client = AsyncOpenAI(
            api_key=settings.deepseek_api_key,
            base_url=settings.deepseek_base_url,
        )
        self._model = settings.deepseek_model

    async def complete_json(self, system: str, user: str, schema: type[BaseModel]) -> Any:
        schema_json = json.dumps(schema.model_json_schema(), ensure_ascii=False)
        grounded_system = (
            f"{system}\n\n"
            "Responda EXCLUSIVAMENTE com um objeto JSON válido (sem markdown, sem cercas "
            "de código) que valide estritamente contra o JSON Schema abaixo. "
            "Use apenas os valores de enum permitidos.\n"
            f"{schema_json}"
        )

        conversation: list[dict[str, str]] = [
            {"role": "system", "content": grounded_system},
            {"role": "user", "content": user},
        ]

        last_error: Exception | None = None
        for attempt in range(_MAX_ATTEMPTS):
            response = await self._client.chat.completions.create(
                model=self._model,
                messages=conversation,
                response_format={"type": "json_object"},
                temperature=0.4,
                max_tokens=_MAX_TOKENS,
            )
            content = response.choices[0].message.content or "{}"
            try:
                return schema.model_validate(json.loads(content))
            except (json.JSONDecodeError, ValidationError) as exc:
                last_error = exc
                if attempt < _MAX_ATTEMPTS - 1:
                    conversation = conversation + [
                        {"role": "assistant", "content": content},
                        {
                            "role": "user",
                            "content": (
                                f"Sua resposta anterior é inválida: {exc}. "
                                "Retorne novamente SOMENTE o objeto JSON válido, "
                                "respeitando o schema e os valores de enum."
                            ),
                        },
                    ]

        raise RuntimeError(
            f"DeepSeek não retornou JSON válido após {_MAX_ATTEMPTS} tentativas: {last_error}"
        )
