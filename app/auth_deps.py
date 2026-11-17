"""Dependências de autenticação (extrai o usuário a partir do token JWT)."""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.domain.enums import UserRole
from app.models import User
from app.security import decode_token

_bearer = HTTPBearer(auto_error=False)

_UNAUTHORIZED = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Não autenticado.",
    headers={"WWW-Authenticate": "Bearer"},
)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: AsyncSession = Depends(get_session),
) -> User:
    if credentials is None:
        raise _UNAUTHORIZED
    try:
        payload = decode_token(credentials.credentials)
    except Exception:  # noqa: BLE001
        raise _UNAUTHORIZED
    user = await db.get(User, payload.get("sub"))
    if user is None:
        raise _UNAUTHORIZED
    return user


async def require_marketing(user: User = Depends(get_current_user)) -> User:
    if user.role != UserRole.MARKETING:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Ação restrita à equipe de marketing.",
        )
    return user
