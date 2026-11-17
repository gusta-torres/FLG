"""Orquestração FLG: classificação de perfil e geração do plano de conteúdo.

A geração do plano é determinística no enquadramento (dias, canais, funil,
atribuição e formato) e usa o LLM apenas para preencher o conteúdo de cada
slot, em blocos (`ContentFillBatch`), o que mantém a meta exata de posts e
evita respostas gigantes em uma única chamada.
"""

from app.domain.enums import Canal, FormatoConteudo, ModeloNegocio, NivelFunil
from app.graph.schedule import build_schedule
from app.llm.base import LLMProvider
from app.prompts import FULL_TEXT_PROMPT, PLAN_FILL_PROMPT, PROFILE_SYSTEM_PROMPT
from app.schemas import (
    ContentFill,
    ContentFillBatch,
    ContentItemCreate,
    DiagnosticProfile,
    FullText,
)

_CHUNK_SIZE = 12


def _serialize_answers(answers: dict[str, str]) -> str:
    return "\n".join(f"- {k}: {v}" for k, v in answers.items())


class FLGGraph:
    """Encapsula o provedor de LLM e o pipeline de geração."""

    def __init__(self, llm: LLMProvider) -> None:
        self._llm = llm

    async def build_profile(
        self,
        business_model: ModeloNegocio,
        answers: dict[str, str],
    ) -> DiagnosticProfile:
        """Classifica arquétipo e monta o perfil + matriz de canais."""
        user = (
            f"Modelo de negócio: {business_model.value}\n\n"
            f"Respostas do diagnóstico:\n{_serialize_answers(answers)}"
        )
        return await self._llm.complete_json(
            PROFILE_SYSTEM_PROMPT, user, DiagnosticProfile
        )

    async def generate_plan(
        self,
        business_model: ModeloNegocio,
        channels: list[Canal],
        profile: DiagnosticProfile,
        period_days: int = 30,
        goal: int = 49,
    ) -> list[ContentItemCreate]:
        """Gera o plano completo (ex.: 49 posts em 30 dias) preenchendo os slots."""
        schedule = build_schedule(
            business_model=business_model,
            channels=channels,
            archetype=profile.dominant_archetype,
            period_days=period_days,
            goal=goal,
        )

        secondary = (
            profile.secondary_archetype.value
            if profile.secondary_archetype
            else "nenhum"
        )

        items: list[ContentItemCreate] = []
        for start in range(0, len(schedule), _CHUNK_SIZE):
            chunk = schedule[start : start + _CHUNK_SIZE]
            slots_text = "\n".join(
                f"{idx + 1}. Dia {slot.day} | {slot.channel.value} | "
                f"{slot.funnel_level.value} | {slot.attribution.value} | {slot.format.value}"
                for idx, slot in enumerate(chunk)
            )
            user = (
                f"Arquétipo dominante: {profile.dominant_archetype.value}\n"
                f"Arquétipo secundário: {secondary}\n"
                f"Modelo de negócio: {business_model.value}\n"
                f"Tese central: {profile.central_thesis}\n\n"
                f"Preencha o conteúdo dos {len(chunk)} slots abaixo, na MESMA ordem. "
                f"Retorne exatamente {len(chunk)} itens em 'items':\n{slots_text}"
            )
            result = await self._llm.complete_json(
                PLAN_FILL_PROMPT, user, ContentFillBatch
            )

            for idx, slot in enumerate(chunk):
                fill = (
                    result.items[idx]
                    if idx < len(result.items)
                    else ContentFill(
                        hook="[preencher gancho]",
                        central_idea="[preencher ideia central]",
                        cta="[preencher CTA]",
                    )
                )
                items.append(
                    ContentItemCreate(
                        day=slot.day,
                        channel=slot.channel,
                        funnel_level=slot.funnel_level,
                        attribution=slot.attribution,
                        format=slot.format,
                        hook=fill.hook,
                        central_idea=fill.central_idea,
                        cta=fill.cta,
                    )
                )

        return items

    async def generate_full_text(
        self,
        *,
        profile: DiagnosticProfile,
        business_model: ModeloNegocio,
        channel: Canal,
        fmt: FormatoConteudo,
        funnel_level: NivelFunil,
        hook: str,
        central_idea: str,
        cta: str,
    ) -> str:
        """Gera o texto completo (legenda/roteiro) de um único post."""
        secondary = (
            profile.secondary_archetype.value
            if profile.secondary_archetype
            else "nenhum"
        )
        user = (
            f"Arquétipo dominante: {profile.dominant_archetype.value}\n"
            f"Arquétipo secundário: {secondary}\n"
            f"Modelo de negócio: {business_model.value}\n"
            f"Tese central: {profile.central_thesis}\n\n"
            f"Canal: {channel.value} | Formato: {fmt.value} | "
            f"Funil: {funnel_level.value}\n"
            f"Gancho: {hook}\n"
            f"Ideia central: {central_idea}\n"
            f"CTA: {cta}\n\n"
            "Escreva o texto completo do post."
        )
        result = await self._llm.complete_json(FULL_TEXT_PROMPT, user, FullText)
        return result.text

