"""Schemas Pydantic do domínio FLG."""

from datetime import date, datetime
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field

from app.domain.enums import (
    Arquetipo,
    Canal,
    ContentStatus,
    DimensaoDiagnostica,
    FormatoConteudo,
    ModeloNegocio,
    NivelFunil,
    PapelCanal,
    ProporcaoAtribuicao,
    UserRole,
)


def _new_id() -> str:
    return str(uuid4())


# ---------- Autenticação / Usuários ----------


class LoginRequest(BaseModel):
    email: str = Field(..., min_length=3)
    password: str = Field(..., min_length=1)


class UserOut(BaseModel):
    id: str
    email: str
    name: str
    role: UserRole
    founder_id: str | None = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ---------- Fundador / Empresa ----------


class FounderCreate(BaseModel):
    name: str = Field(..., min_length=1)
    company_name: str = Field(..., min_length=1)
    business_model: ModeloNegocio
    email: str = Field(..., min_length=3)
    password: str = Field(..., min_length=6)


class FounderOut(BaseModel):
    id: str
    name: str
    company_name: str
    business_model: ModeloNegocio
    email: str
    created_at: datetime


# ---------- Diagnóstico ----------


class DiagnosticAnswer(BaseModel):
    dimension: DimensaoDiagnostica
    question_key: str
    answer: str = Field(..., min_length=1)


class DiagnosticProfile(BaseModel):
    """Resultado do Node 2: arquétipo + tese central + matriz de canais."""

    dominant_archetype: Arquetipo
    secondary_archetype: Arquetipo | None = None
    central_thesis: str = Field(..., description="Tese Central de Comunicação em até 2 frases")
    channel_allocation: list["ChannelAllocation"]


class ChannelAllocation(BaseModel):
    channel: Canal
    role: PapelCanal
    dedication_percent: int = Field(..., ge=0, le=100)
    native_formats: list[FormatoConteudo]


# ---------- Plano de Conteúdo ----------


class ContentItemCreate(BaseModel):
    day: int = Field(..., ge=1, le=31)
    channel: Canal
    funnel_level: NivelFunil
    attribution: ProporcaoAtribuicao
    format: FormatoConteudo
    hook: str
    central_idea: str
    cta: str


class ContentItemOut(ContentItemCreate):
    id: str = Field(default_factory=_new_id)
    status: ContentStatus = ContentStatus.PENDENTE
    full_text: str | None = None
    posted_at: datetime | None = None


class ContentFill(BaseModel):
    """Conteúdo textual de um slot da grade (sem dados de enquadramento)."""

    hook: str
    central_idea: str
    cta: str


class ContentFillBatch(BaseModel):
    items: list[ContentFill]


class FullText(BaseModel):
    """Texto completo (legenda/roteiro) pronto para publicar."""

    text: str


class EditorialGridCreate(BaseModel):
    founder_id: str
    items: list[ContentItemCreate]


class EditorialGridOut(BaseModel):
    id: str = Field(default_factory=_new_id)
    founder_id: str
    period_days: int = 30
    goal_posts: int = 49
    start_date: date | None = None
    created_at: datetime
    items: list[ContentItemOut]


class EditorialGridRequest(BaseModel):
    founder_id: str
    channels: list[Canal] = Field(
        default_factory=lambda: [Canal.INSTAGRAM, Canal.LINKEDIN]
    )
    period_days: int = 30
    goal_posts: int = 49


class EditorialGridItems(BaseModel):
    """Saída estruturada do gerador de grade (lista de itens)."""

    items: list[ContentItemCreate]


# ---------- Entrevista ----------


class InterviewQuestion(BaseModel):
    block: int = Field(..., ge=1, le=3)
    dimension: DimensaoDiagnostica
    key: str
    text: str


class InterviewState(BaseModel):
    session_id: str = Field(default_factory=_new_id)
    founder_id: str
    current_block: int = 1
    questions: list[InterviewQuestion]
    answers: dict[str, str] = Field(default_factory=dict)
    profile: DiagnosticProfile | None = None
    status: Literal["in_progress", "awaiting_profile", "completed"] = "in_progress"
