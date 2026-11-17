"""Construção determinística do cronograma do plano (49 posts / 30 dias).

O cronograma garante a meta de posts e o equilíbrio por funil e pela matriz
70-20-8-2. O LLM apenas preenche o conteúdo (gancho, ideia, CTA) de cada slot.
"""

from dataclasses import dataclass

from app.domain.enums import (
    Arquetipo,
    Canal,
    FormatoConteudo,
    ModeloNegocio,
    NivelFunil,
    ProporcaoAtribuicao,
)

_CHANNEL_FORMATS: dict[Canal, list[FormatoConteudo]] = {
    Canal.LINKEDIN: [
        FormatoConteudo.ARTIGO_LINKEDIN,
        FormatoConteudo.CARROSSEL,
        FormatoConteudo.FOTO_TEXTO,
    ],
    Canal.INSTAGRAM: [
        FormatoConteudo.CARROSSEL,
        FormatoConteudo.REELS_SHORTS,
        FormatoConteudo.FOTO_TEXTO,
    ],
}

_LINKEDIN_PRIMARY_MODELS = {ModeloNegocio.B2B_SERVICOS, ModeloNegocio.SOFTWARE_SAAS}


@dataclass
class Slot:
    day: int
    channel: Canal
    funnel_level: NivelFunil
    attribution: ProporcaoAtribuicao
    format: FormatoConteudo


def _primary_channel(business_model: ModeloNegocio, channels: list[Canal]) -> Canal:
    preferred = (
        Canal.LINKEDIN
        if business_model in _LINKEDIN_PRIMARY_MODELS
        else Canal.INSTAGRAM
    )
    if preferred in channels:
        return preferred
    return channels[0]


def _funnel_and_attribution(goal: int) -> list[tuple[NivelFunil, ProporcaoAtribuicao]]:
    topo = round(0.30 * goal)
    meio = round(0.50 * goal)
    fundo = goal - topo - meio

    assunto = round(0.70 * goal)
    autoridade = round(0.20 * goal)
    humanizacao = round(0.08 * goal)
    comercial = goal - assunto - autoridade - humanizacao

    remaining = {
        ProporcaoAtribuicao.ASSUNTO_INDUSTRIA: assunto,
        ProporcaoAtribuicao.AUTORIDADE_TECNICA: autoridade,
        ProporcaoAtribuicao.HUMANIZACAO: humanizacao,
        ProporcaoAtribuicao.COMERCIAL_DIRETO: comercial,
    }

    # Ordem de preferência de atribuição por nível de funil.
    preference = {
        NivelFunil.TOPO: [
            ProporcaoAtribuicao.HUMANIZACAO,
            ProporcaoAtribuicao.ASSUNTO_INDUSTRIA,
        ],
        NivelFunil.MEIO: [
            ProporcaoAtribuicao.ASSUNTO_INDUSTRIA,
            ProporcaoAtribuicao.AUTORIDADE_TECNICA,
        ],
        NivelFunil.FUNDO: [
            ProporcaoAtribuicao.COMERCIAL_DIRETO,
            ProporcaoAtribuicao.AUTORIDADE_TECNICA,
        ],
    }

    def take(funnel: NivelFunil) -> ProporcaoAtribuicao:
        for attr in preference[funnel]:
            if remaining[attr] > 0:
                remaining[attr] -= 1
                return attr
        # fallback: qualquer atribuição restante
        for attr, count in remaining.items():
            if count > 0:
                remaining[attr] -= 1
                return attr
        return ProporcaoAtribuicao.ASSUNTO_INDUSTRIA

    result: list[tuple[NivelFunil, ProporcaoAtribuicao]] = []
    for _ in range(topo):
        result.append((NivelFunil.TOPO, take(NivelFunil.TOPO)))
    for _ in range(meio):
        result.append((NivelFunil.MEIO, take(NivelFunil.MEIO)))
    for _ in range(fundo):
        result.append((NivelFunil.FUNDO, take(NivelFunil.FUNDO)))
    return result


def build_schedule(
    business_model: ModeloNegocio,
    channels: list[Canal],
    archetype: Arquetipo | None = None,
    period_days: int = 30,
    goal: int = 49,
) -> list[Slot]:
    """Gera `goal` slots distribuídos em `period_days`, só com os canais informados."""
    channels = [c for c in channels if c in (Canal.INSTAGRAM, Canal.LINKEDIN)] or [
        Canal.INSTAGRAM,
        Canal.LINKEDIN,
    ]
    primary = _primary_channel(business_model, channels)
    secondary = next((c for c in channels if c != primary), primary)

    funnel_attr = _funnel_and_attribution(goal)

    slots: list[Slot] = []
    for i, (funnel, attribution) in enumerate(funnel_attr):
        day = min(period_days, (i * period_days) // goal + 1)
        # ~60% no canal primário, ~40% no secundário
        channel = primary if i % 5 < 3 else secondary
        formats = _CHANNEL_FORMATS[channel]
        fmt = formats[i % len(formats)]
        slots.append(
            Slot(
                day=day,
                channel=channel,
                funnel_level=funnel,
                attribution=attribution,
                format=fmt,
            )
        )

    slots.sort(key=lambda s: s.day)
    return slots
