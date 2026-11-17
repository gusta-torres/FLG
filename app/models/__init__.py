"""Modelos ORM do domínio FLG."""

from datetime import date, datetime
from uuid import uuid4

from sqlalchemy import (
    JSON,
    Date,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.domain.enums import (
    Canal,
    ContentStatus,
    FormatoConteudo,
    ModeloNegocio,
    NivelFunil,
    ProporcaoAtribuicao,
    UserRole,
)


def _enum(enum_cls):
    return SAEnum(
        enum_cls,
        native_enum=False,
        values_callable=lambda e: [m.value for m in e],
        validate_strings=True,
    )


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    name: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(_enum(UserRole))
    founder_id: Mapped[str | None] = mapped_column(
        ForeignKey("founders.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    founder: Mapped["Founder | None"] = relationship(back_populates="user")


class Founder(Base):
    __tablename__ = "founders"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String(255))
    company_name: Mapped[str] = mapped_column(String(255))
    business_model: Mapped[ModeloNegocio] = mapped_column(_enum(ModeloNegocio))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user: Mapped["User | None"] = relationship(back_populates="founder", uselist=False)
    diagnostics: Mapped[list["Diagnostic"]] = relationship(back_populates="founder")
    grids: Mapped[list["EditorialGrid"]] = relationship(back_populates="founder")


class Diagnostic(Base):
    __tablename__ = "diagnostics"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    founder_id: Mapped[str] = mapped_column(ForeignKey("founders.id"))
    answers: Mapped[dict] = mapped_column(JSON, default=dict)
    profile: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="in_progress")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    founder: Mapped[Founder] = relationship(back_populates="diagnostics")


class EditorialGrid(Base):
    """Representa um plano de conteúdo (ex.: 49 posts em 30 dias)."""

    __tablename__ = "editorial_grids"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    founder_id: Mapped[str] = mapped_column(ForeignKey("founders.id"))
    period_days: Mapped[int] = mapped_column(Integer, default=30)
    goal_posts: Mapped[int] = mapped_column(Integer, default=49)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    founder: Mapped[Founder] = relationship(back_populates="grids")
    items: Mapped[list["ContentItem"]] = relationship(
        back_populates="grid", cascade="all, delete-orphan"
    )


class ContentItem(Base):
    __tablename__ = "content_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    grid_id: Mapped[str] = mapped_column(ForeignKey("editorial_grids.id"))
    day: Mapped[int] = mapped_column(Integer)
    channel: Mapped[Canal] = mapped_column(_enum(Canal))
    funnel_level: Mapped[NivelFunil] = mapped_column(_enum(NivelFunil))
    attribution: Mapped[ProporcaoAtribuicao] = mapped_column(_enum(ProporcaoAtribuicao))
    format: Mapped[FormatoConteudo] = mapped_column(_enum(FormatoConteudo))
    hook: Mapped[str] = mapped_column(String(2000))
    central_idea: Mapped[str] = mapped_column(String(4000))
    cta: Mapped[str] = mapped_column(String(2000))
    status: Mapped[ContentStatus] = mapped_column(
        _enum(ContentStatus), default=ContentStatus.PENDENTE
    )
    full_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    posted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    grid: Mapped[EditorialGrid] = relationship(back_populates="items")
