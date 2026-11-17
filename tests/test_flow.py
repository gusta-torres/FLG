import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db import Base
from app.deps import get_graph
from app.domain.enums import Canal, ModeloNegocio
from app.schemas import FounderCreate
from app.services.flg_service import FLGService


@pytest.fixture
async def session_factory():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield factory
    await engine.dispose()


@pytest.fixture
def service():
    return FLGService(get_graph())


async def test_full_flow(session_factory, service):
    founder_create = FounderCreate(
        name="Fundador Teste",
        company_name="Empresa Teste",
        business_model=ModeloNegocio.B2B_SERVICOS,
        email="fundador@teste.com",
        password="secret123",
    )

    async with session_factory() as db:
        founder = await service.create_founder(db, founder_create)

        diagnostic_id, questions = await service.start_interview(db, founder.id)
        assert len(questions) > 0

        for answer in (
            {"problema_fundamental": "Falta de previsibilidade financeira."},
            {"icp_e_dor": "CEOs de PMEs que não medem resultado."},
            {"marcos_autoridade": "10 anos de mercado, 50 cases."},
            {"preferencia_comunicacional": "Escrita analítica profunda."},
            {"rotina_compartilhavel": "Disciplina e esportes."},
            {"temas_fora": "Política partidária."},
        ):
            await service.answer(db, diagnostic_id, answer)

        profile = await service.complete_profile(db, diagnostic_id)
        assert profile.dominant_archetype.value is not None

        grid_id = await service.generate_plan(
            db, founder.id, [Canal.INSTAGRAM, Canal.LINKEDIN]
        )

        grid = await service.get_grid(db, grid_id)
        assert grid is not None
        assert len(grid.items) == 49
        assert {i.channel for i in grid.items} <= {Canal.INSTAGRAM, Canal.LINKEDIN}
        assert {i.funnel_level.value for i in grid.items} == {"topo", "meio", "fundo"}
