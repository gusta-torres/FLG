"""Ponto de entrada da aplicação FastAPI."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from app.api.routes import router
from app.config import Settings, get_settings
from app.db import async_session, init_db
from app.domain.enums import UserRole
from app.models import User
from app.security import hash_password


async def _seed_admin() -> None:
    s = get_settings()
    async with async_session() as db:
        existing = await db.execute(
            select(User).where(User.email == s.admin_email.lower())
        )
        if existing.scalar_one_or_none() is None:
            db.add(
                User(
                    email=s.admin_email.lower(),
                    password_hash=hash_password(s.admin_password),
                    name=s.admin_name,
                    role=UserRole.MARKETING,
                )
            )
            await db.commit()


def _llm_status(s: Settings) -> dict:
    provider = s.llm_provider.lower()
    key_configured = {
        "openai": bool(s.openai_api_key),
        "anthropic": bool(s.anthropic_api_key),
        "deepseek": bool(s.deepseek_api_key),
        "mock": True,
    }.get(provider, False)
    return {"llm_provider": provider, "llm_key_configured": key_configured}


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await _seed_admin()
    yield


settings = get_settings()

app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {"status": "ok", "app": settings.app_name, **_llm_status(get_settings())}
