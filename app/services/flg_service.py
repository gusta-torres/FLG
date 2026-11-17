"""Serviço de orquestração do fluxo FLG (fundadores, entrevista, plano)."""

from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.enums import Canal, ContentStatus, ModeloNegocio, UserRole
from app.graph.flg_graph import FLGGraph
from app.models import ContentItem, Diagnostic, EditorialGrid, Founder, User
from app.prompts import INTERVIEW_BLOCKS
from app.schemas import (
    ContentItemCreate,
    DiagnosticProfile,
    FounderCreate,
    FounderOut,
)
from app.security import hash_password


def _blocks_done(answers: dict[str, str]) -> bool:
    return all(
        q["key"] in answers
        for block in INTERVIEW_BLOCKS
        for q in block["questions"]
    )


def _next_block(answers: dict[str, str]) -> list[dict] | None:
    for block in INTERVIEW_BLOCKS:
        pending = [q for q in block["questions"] if q["key"] not in answers]
        if pending:
            return pending
    return None


class FLGService:
    def __init__(self, graph: FLGGraph) -> None:
        self._graph = graph

    # ---------- Fundador ----------

    async def create_founder(self, db: AsyncSession, payload: FounderCreate) -> FounderOut:
        email = payload.email.lower().strip()
        existing = await db.execute(select(User).where(User.email == email))
        if existing.scalar_one_or_none() is not None:
            raise ValueError("Já existe um usuário com este email.")

        founder = Founder(
            name=payload.name,
            company_name=payload.company_name,
            business_model=payload.business_model,
        )
        db.add(founder)
        await db.flush()

        user = User(
            email=email,
            password_hash=hash_password(payload.password),
            name=payload.name,
            role=UserRole.FOUNDER,
            founder_id=founder.id,
        )
        db.add(user)
        await db.commit()
        await db.refresh(founder)

        return FounderOut(
            id=founder.id,
            name=founder.name,
            company_name=founder.company_name,
            business_model=founder.business_model,
            email=email,
            created_at=founder.created_at,
        )

    async def get_founder(self, db: AsyncSession, founder_id: str) -> Founder | None:
        return await db.get(Founder, founder_id)

    async def get_founder_out(self, db: AsyncSession, founder_id: str) -> FounderOut | None:
        result = await db.execute(
            select(Founder)
            .options(selectinload(Founder.user))
            .where(Founder.id == founder_id)
        )
        founder = result.scalar_one_or_none()
        if founder is None:
            return None
        return FounderOut(
            id=founder.id,
            name=founder.name,
            company_name=founder.company_name,
            business_model=founder.business_model,
            email=founder.user.email if founder.user else "",
            created_at=founder.created_at,
        )

    async def latest_grid(self, db: AsyncSession, founder_id: str) -> EditorialGrid | None:
        result = await db.execute(
            select(EditorialGrid)
            .where(EditorialGrid.founder_id == founder_id)
            .order_by(EditorialGrid.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def list_founders(self, db: AsyncSession) -> list[FounderOut]:
        result = await db.execute(
            select(Founder).options(selectinload(Founder.user)).order_by(Founder.name)
        )
        founders = result.scalars().all()
        return [
            FounderOut(
                id=f.id,
                name=f.name,
                company_name=f.company_name,
                business_model=f.business_model,
                email=f.user.email if f.user else "",
                created_at=f.created_at,
            )
            for f in founders
        ]

    # ---------- Entrevista ----------

    async def start_interview(self, db: AsyncSession, founder_id: str) -> tuple[str, list[dict]]:
        diagnostic = Diagnostic(founder_id=founder_id, answers={}, status="in_progress")
        db.add(diagnostic)
        await db.commit()
        await db.refresh(diagnostic)
        return diagnostic.id, _next_block({}) or []

    async def answer(
        self,
        db: AsyncSession,
        diagnostic_id: str,
        answers: dict[str, str],
    ) -> dict:
        diagnostic = await db.get(Diagnostic, diagnostic_id)
        if diagnostic is None:
            raise ValueError("Diagnóstico não encontrado.")

        merged = {**diagnostic.answers, **answers}
        diagnostic.answers = merged
        if _blocks_done(merged):
            diagnostic.status = "completed"
        await db.commit()

        return {
            "status": diagnostic.status,
            "next_questions": None if _blocks_done(merged) else _next_block(merged),
        }

    async def complete_profile(self, db: AsyncSession, diagnostic_id: str) -> DiagnosticProfile:
        diagnostic = await db.get(Diagnostic, diagnostic_id)
        if diagnostic is None:
            raise ValueError("Diagnóstico não encontrado.")
        founder = await db.get(Founder, diagnostic.founder_id)
        if founder is None:
            raise ValueError("Fundador não encontrado.")

        profile = await self._graph.build_profile(
            business_model=ModeloNegocio(founder.business_model),
            answers=diagnostic.answers,
        )
        diagnostic.profile = profile.model_dump(mode="json")
        await db.commit()
        return profile

    # ---------- Plano de conteúdo ----------

    async def latest_profile(
        self, db: AsyncSession, founder_id: str
    ) -> DiagnosticProfile:
        result = await db.execute(
            select(Diagnostic)
            .where(Diagnostic.founder_id == founder_id, Diagnostic.profile.isnot(None))
            .order_by(Diagnostic.created_at.desc())
            .limit(1)
        )
        diagnostic = result.scalar_one_or_none()
        if diagnostic is None or diagnostic.profile is None:
            raise ValueError("Nenhum perfil concluído para este fundador.")
        return DiagnosticProfile.model_validate(diagnostic.profile)

    async def generate_plan(
        self,
        db: AsyncSession,
        founder_id: str,
        channels: list[Canal],
        period_days: int = 30,
        goal: int = 49,
    ) -> str:
        founder = await db.get(Founder, founder_id)
        if founder is None:
            raise ValueError("Fundador não encontrado.")

        profile = await self.latest_profile(db, founder_id)
        items = await self._graph.generate_plan(
            business_model=ModeloNegocio(founder.business_model),
            channels=channels,
            profile=profile,
            period_days=period_days,
            goal=goal,
        )

        grid = EditorialGrid(
            founder_id=founder_id,
            period_days=period_days,
            goal_posts=goal,
            start_date=date.today(),
        )
        grid.items = [self._to_item_model(it) for it in items]
        db.add(grid)
        await db.commit()
        await db.refresh(grid)
        return grid.id

    async def get_grid(self, db: AsyncSession, grid_id: str) -> EditorialGrid | None:
        result = await db.execute(
            select(EditorialGrid)
            .options(selectinload(EditorialGrid.items))
            .where(EditorialGrid.id == grid_id)
        )
        return result.scalar_one_or_none()

    async def get_item(self, db: AsyncSession, item_id: str) -> ContentItem | None:
        return await db.get(ContentItem, item_id)

    async def update_item_status(
        self, db: AsyncSession, item_id: str, status: ContentStatus
    ) -> ContentItem:
        item = await db.get(ContentItem, item_id)
        if item is None:
            raise ValueError("Post não encontrado.")
        item.status = status
        if status == ContentStatus.POSTADO and item.posted_at is None:
            item.posted_at = datetime.now(timezone.utc).replace(tzinfo=None)
        await db.commit()
        await db.refresh(item)
        return item

    async def generate_item_text(self, db: AsyncSession, item_id: str) -> ContentItem:
        item = await db.get(ContentItem, item_id)
        if item is None:
            raise ValueError("Post não encontrado.")
        grid = await db.get(EditorialGrid, item.grid_id)
        if grid is None:
            raise ValueError("Plano não encontrado.")
        founder = await db.get(Founder, grid.founder_id)
        if founder is None:
            raise ValueError("Fundador não encontrado.")

        profile = await self.latest_profile(db, grid.founder_id)
        text = await self._graph.generate_full_text(
            profile=profile,
            business_model=ModeloNegocio(founder.business_model),
            channel=item.channel,
            fmt=item.format,
            funnel_level=item.funnel_level,
            hook=item.hook,
            central_idea=item.central_idea,
            cta=item.cta,
        )
        item.full_text = text
        await db.commit()
        await db.refresh(item)
        return item

    # ---------- Competição / estatísticas ----------

    @staticmethod
    def _streak(dates: set[date], today: date) -> int:
        if today in dates:
            cursor = today
        elif (today - timedelta(days=1)) in dates:
            cursor = today - timedelta(days=1)
        else:
            return 0
        streak = 0
        while cursor in dates:
            streak += 1
            cursor -= timedelta(days=1)
        return streak

    async def leaderboard(self, db: AsyncSession) -> list[dict]:
        """Placar interno (ofensiva, XP, conclusão) por founder — todos veem tudo."""
        result = await db.execute(
            select(Founder).options(selectinload(Founder.user)).order_by(Founder.name)
        )
        founders = result.scalars().all()
        today = date.today()
        board: list[dict] = []

        for founder in founders:
            grid_res = await db.execute(
                select(EditorialGrid)
                .options(selectinload(EditorialGrid.items))
                .where(EditorialGrid.founder_id == founder.id)
                .order_by(EditorialGrid.created_at.desc())
                .limit(1)
            )
            grid = grid_res.scalar_one_or_none()
            items = grid.items if grid else []

            posted = [i for i in items if i.status == ContentStatus.POSTADO]
            posted_dates = {
                (i.posted_at.date() if i.posted_at else None) for i in posted
            }
            posted_dates.discard(None)
            streak = self._streak(posted_dates, today)

            total = len(items)
            done = len(posted)
            xp = done * 10 + streak * 5

            board.append(
                {
                    "founder_id": founder.id,
                    "name": founder.name,
                    "company_name": founder.company_name,
                    "goal_posts": grid.goal_posts if grid else 0,
                    "total_posts": total,
                    "posted_posts": done,
                    "completion_pct": round((done / total) * 100) if total else 0,
                    "streak": streak,
                    "xp": xp,
                }
            )

        board.sort(key=lambda row: (row["xp"], row["posted_posts"]), reverse=True)
        return board

    @staticmethod
    def _to_item_model(item: ContentItemCreate) -> ContentItem:
        return ContentItem(
            day=item.day,
            channel=item.channel,
            funnel_level=item.funnel_level,
            attribution=item.attribution,
            format=item.format,
            hook=item.hook,
            central_idea=item.central_idea,
            cta=item.cta,
            status=ContentStatus.PENDENTE,
        )
