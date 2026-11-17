"""Provedor mock determinístico para desenvolvimento e testes sem chave de API."""

from typing import Any

from pydantic import BaseModel

from app.config import Settings
from app.domain.enums import (
    Arquetipo,
    Canal,
    FormatoConteudo,
    PapelCanal,
)
from app.llm.base import LLMProvider


class MockProvider(LLMProvider):
    """Retorna respostas estruturadas válidas e previsíveis, sem depender de rede."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def complete_json(self, system: str, user: str, schema: type[BaseModel]) -> Any:
        name = schema.__name__
        if name == "DiagnosticProfile":
            return self._profile(schema)
        if name == "ContentFillBatch":
            return self._fills(schema)
        if name == "FullText":
            from app.schemas import FullText

            return FullText(
                text="[Texto de exemplo] Este é o conteúdo completo gerado pelo modo mock. "
                "Em produção, o LLM escreve a legenda na voz do fundador."
            )
        return schema.model_validate(self._defaults(schema))

    def _fills(self, schema: type[BaseModel]) -> Any:
        from app.schemas import ContentFill, ContentFillBatch

        fills = [
            ContentFill(
                hook=f"Gancho de exemplo {i + 1}: a verdade sobre gestão e dados.",
                central_idea=f"Desenvolvimento sintético do slot {i + 1} com um case real.",
                cta="Comente 'quero' para receber o material.",
            )
            for i in range(12)
        ]
        return ContentFillBatch(items=fills)

    def _profile(self, schema: type[BaseModel]) -> Any:
        from app.schemas import ChannelAllocation, DiagnosticProfile

        return DiagnosticProfile(
            dominant_archetype=Arquetipo.NERD_RICO_ANALITICO,
            secondary_archetype=Arquetipo.PROFESSOR_LOW_PROFILE,
            central_thesis=(
                "O mercado de gestão é dominado por achismo, e não por dados. "
                "A previsibilidade financeira nasce de métodos estruturados e análise rigorosa."
            ),
            channel_allocation=[
                ChannelAllocation(
                    channel=Canal.LINKEDIN,
                    role=PapelCanal.PRIMARIO,
                    dedication_percent=70,
                    native_formats=[
                        FormatoConteudo.ARTIGO_LINKEDIN,
                        FormatoConteudo.CARROSSEL,
                    ],
                ),
                ChannelAllocation(
                    channel=Canal.INSTAGRAM,
                    role=PapelCanal.SECUNDARIO,
                    dedication_percent=30,
                    native_formats=[
                        FormatoConteudo.CARROSSEL,
                        FormatoConteudo.REELS_SHORTS,
                    ],
                ),
            ],
        )

    @staticmethod
    def _defaults(schema: type[BaseModel]) -> dict[str, Any]:
        return {}
