"""Rotas da API FLG."""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth_deps import get_current_user, require_marketing
from app.db import get_session
from app.deps import get_graph
from app.domain.enums import ContentStatus
from app.graph.flg_graph import FLGGraph
from app.models import User
from app.schemas import (
    ContentItemOut,
    DiagnosticProfile,
    EditorialGridRequest,
    FounderCreate,
    FounderOut,
    LoginRequest,
    TokenResponse,
    UserOut,
)
from app.security import create_access_token, verify_password
from app.services.flg_service import FLGService

logger = logging.getLogger(__name__)

router = APIRouter()

_LLM_ERROR_DETAIL = (
    "Falha ao consultar o provedor de LLM. "
    "Verifique a configuração da chave e tente novamente."
)


def get_service(graph: FLGGraph = Depends(get_graph)) -> FLGService:
    return FLGService(graph)


def _user_out(user: User) -> UserOut:
    return UserOut(
        id=user.id,
        email=user.email,
        name=user.name,
        role=user.role,
        founder_id=user.founder_id,
    )


def _item_out(item) -> ContentItemOut:
    return ContentItemOut(
        id=item.id,
        day=item.day,
        channel=item.channel,
        funnel_level=item.funnel_level,
        attribution=item.attribution,
        format=item.format,
        hook=item.hook,
        central_idea=item.central_idea,
        cta=item.cta,
        status=item.status,
        full_text=item.full_text,
        posted_at=item.posted_at,
    )


# ---------- Autenticação ----------


@router.post("/auth/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_session)):
    result = await db.execute(
        select(User).where(User.email == payload.email.lower().strip())
    )
    user = result.scalar_one_or_none()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Email ou senha inválidos.")
    token = create_access_token(user.id, user.role.value)
    return TokenResponse(access_token=token, user=_user_out(user))


@router.get("/auth/me", response_model=UserOut)
async def me(user: User = Depends(get_current_user)):
    return _user_out(user)


# ---------- Fundadores ----------


@router.post("/founders", response_model=FounderOut, status_code=201)
async def create_founder(
    payload: FounderCreate,
    db: AsyncSession = Depends(get_session),
    service: FLGService = Depends(get_service),
    _: User = Depends(require_marketing),
):
    try:
        return await service.create_founder(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@router.get("/founders", response_model=list[FounderOut])
async def list_founders(
    db: AsyncSession = Depends(get_session),
    service: FLGService = Depends(get_service),
    _: User = Depends(get_current_user),
):
    return await service.list_founders(db)


@router.get("/founders/{founder_id}", response_model=FounderOut)
async def get_founder(
    founder_id: str,
    db: AsyncSession = Depends(get_session),
    service: FLGService = Depends(get_service),
    _: User = Depends(get_current_user),
):
    founder = await service.get_founder_out(db, founder_id)
    if founder is None:
        raise HTTPException(status_code=404, detail="Fundador não encontrado.")
    return founder


@router.get("/founders/{founder_id}/plan")
async def get_founder_plan(
    founder_id: str,
    db: AsyncSession = Depends(get_session),
    service: FLGService = Depends(get_service),
    _: User = Depends(get_current_user),
):
    grid = await service.latest_grid(db, founder_id)
    return {"grid_id": grid.id if grid else None}


# ---------- Diagnóstico ----------


@router.post("/diagnostics/session", status_code=201)
async def start_interview(
    body: dict,
    db: AsyncSession = Depends(get_session),
    service: FLGService = Depends(get_service),
    _: User = Depends(get_current_user),
):
    founder_id = body.get("founder_id")
    if not founder_id:
        raise HTTPException(status_code=422, detail="founder_id é obrigatório.")
    if await service.get_founder(db, founder_id) is None:
        raise HTTPException(status_code=404, detail="Fundador não encontrado.")
    diagnostic_id, questions = await service.start_interview(db, founder_id)
    return {"diagnostic_id": diagnostic_id, "questions": questions}


@router.post("/diagnostics/{diagnostic_id}/answer")
async def answer_interview(
    diagnostic_id: str,
    body: dict,
    db: AsyncSession = Depends(get_session),
    service: FLGService = Depends(get_service),
    _: User = Depends(get_current_user),
):
    answers = body.get("answers", {})
    try:
        return await service.answer(db, diagnostic_id, answers)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/diagnostics/{diagnostic_id}/complete", response_model=DiagnosticProfile)
async def complete_diagnostic(
    diagnostic_id: str,
    db: AsyncSession = Depends(get_session),
    service: FLGService = Depends(get_service),
    _: User = Depends(get_current_user),
):
    try:
        return await service.complete_profile(db, diagnostic_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:  # noqa: BLE001
        logger.warning("Falha no provedor de LLM ao gerar perfil: %s", type(exc).__name__)
        raise HTTPException(status_code=502, detail=_LLM_ERROR_DETAIL)


# ---------- Plano de conteúdo ----------


@router.post("/editorial-grids", status_code=201)
async def generate_plan(
    payload: EditorialGridRequest,
    db: AsyncSession = Depends(get_session),
    service: FLGService = Depends(get_service),
    _: User = Depends(get_current_user),
):
    try:
        grid_id = await service.generate_plan(
            db,
            payload.founder_id,
            payload.channels,
            period_days=payload.period_days,
            goal=payload.goal_posts,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:  # noqa: BLE001
        logger.warning("Falha no provedor de LLM ao gerar plano: %s", type(exc).__name__)
        raise HTTPException(status_code=502, detail=_LLM_ERROR_DETAIL)
    return {"grid_id": grid_id}


@router.get("/editorial-grids/{grid_id}")
async def get_grid(
    grid_id: str,
    db: AsyncSession = Depends(get_session),
    service: FLGService = Depends(get_service),
    _: User = Depends(get_current_user),
):
    grid = await service.get_grid(db, grid_id)
    if grid is None:
        raise HTTPException(status_code=404, detail="Plano não encontrado.")
    return {
        "id": grid.id,
        "founder_id": grid.founder_id,
        "period_days": grid.period_days,
        "goal_posts": grid.goal_posts,
        "start_date": grid.start_date,
        "created_at": grid.created_at,
        "items": [
            _item_out(item) for item in sorted(grid.items, key=lambda i: (i.day, i.id))
        ],
    }


@router.patch("/content-items/{item_id}/status", response_model=ContentItemOut)
async def update_item_status(
    item_id: str,
    body: dict,
    db: AsyncSession = Depends(get_session),
    service: FLGService = Depends(get_service),
    _: User = Depends(get_current_user),
):
    raw = body.get("status")
    try:
        status = ContentStatus(raw)
    except ValueError:
        raise HTTPException(status_code=422, detail="status inválido.")
    try:
        item = await service.update_item_status(db, item_id, status)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return _item_out(item)


@router.post("/content-items/{item_id}/generate-text", response_model=ContentItemOut)
async def generate_item_text(
    item_id: str,
    db: AsyncSession = Depends(get_session),
    service: FLGService = Depends(get_service),
    _: User = Depends(get_current_user),
):
    try:
        item = await service.generate_item_text(db, item_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:  # noqa: BLE001
        logger.warning("Falha no provedor de LLM ao gerar texto: %s", type(exc).__name__)
        raise HTTPException(status_code=502, detail=_LLM_ERROR_DETAIL)
    return _item_out(item)


# ---------- Competição ----------


@router.get("/leaderboard")
async def leaderboard(
    db: AsyncSession = Depends(get_session),
    service: FLGService = Depends(get_service),
    _: User = Depends(get_current_user),
):
    return await service.leaderboard(db)
