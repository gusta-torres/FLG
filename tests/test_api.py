import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db import Base, get_session
from app.domain.enums import UserRole
from app.main import app
from app.models import User
from app.security import hash_password

ANSWERS = [
    {"problema_fundamental": "Falta de previsibilidade financeira."},
    {"icp_e_dor": "CEOs de PMEs que não medem resultado."},
    {"marcos_autoridade": "10 anos de mercado, 50 cases."},
    {"preferencia_comunicacional": "Escrita analítica profunda."},
    {"rotina_compartilhavel": "Disciplina e esportes."},
    {"temas_fora": "Política partidária."},
]


@pytest.fixture
async def client():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with factory() as seed:
        seed.add(
            User(
                email="marketing@test.com",
                password_hash=hash_password("secret123"),
                name="Equipe MKT",
                role=UserRole.MARKETING,
            )
        )
        await seed.commit()

    async def override_session():
        async with factory() as session:
            yield session

    app.dependency_overrides[get_session] = override_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()
    await engine.dispose()


async def _login(client, email: str, password: str) -> dict:
    res = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    )
    assert res.status_code == 200, res.text
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


async def test_auth_required(client):
    res = await client.get("/api/v1/founders")
    assert res.status_code == 401


async def test_api_flow(client):
    headers = await _login(client, "marketing@test.com", "secret123")

    me = await client.get("/api/v1/auth/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["role"] == "marketing"

    founder_res = await client.post(
        "/api/v1/founders",
        headers=headers,
        json={
            "name": "Ana Ribeiro",
            "company_name": "Ribeiro Consultoria",
            "business_model": "b2b_servicos_executivos",
            "email": "ana@teste.com",
            "password": "secret123",
        },
    )
    assert founder_res.status_code == 201, founder_res.text
    founder = founder_res.json()

    listed = await client.get("/api/v1/founders", headers=headers)
    assert listed.status_code == 200
    assert any(f["id"] == founder["id"] for f in listed.json())

    start = await client.post(
        "/api/v1/diagnostics/session",
        headers=headers,
        json={"founder_id": founder["id"]},
    )
    diagnostic_id = start.json()["diagnostic_id"]

    status = "in_progress"
    for answer in ANSWERS:
        res = await client.post(
            f"/api/v1/diagnostics/{diagnostic_id}/answer",
            headers=headers,
            json={"answers": answer},
        )
        status = res.json()["status"]
    assert status == "completed"

    profile = await client.post(
        f"/api/v1/diagnostics/{diagnostic_id}/complete", headers=headers
    )
    assert profile.status_code == 200
    assert profile.json()["dominant_archetype"]

    grid_res = await client.post(
        "/api/v1/editorial-grids",
        headers=headers,
        json={
            "founder_id": founder["id"],
            "channels": ["instagram", "linkedin"],
            "period_days": 30,
            "goal_posts": 49,
        },
    )
    assert grid_res.status_code == 201, grid_res.text
    grid_id = grid_res.json()["grid_id"]

    grid = await client.get(f"/api/v1/editorial-grids/{grid_id}", headers=headers)
    body = grid.json()
    assert body["goal_posts"] == 49
    assert len(body["items"]) == 49
    assert {i["channel"] for i in body["items"]} <= {"instagram", "linkedin"}

    item = body["items"][0]
    patched = await client.patch(
        f"/api/v1/content-items/{item['id']}/status",
        headers=headers,
        json={"status": "postado"},
    )
    assert patched.status_code == 200
    assert patched.json()["status"] == "postado"

    text = await client.post(
        f"/api/v1/content-items/{item['id']}/generate-text", headers=headers
    )
    assert text.status_code == 200
    assert text.json()["full_text"]

    board = await client.get("/api/v1/leaderboard", headers=headers)
    assert board.status_code == 200
    entry = next(b for b in board.json() if b["founder_id"] == founder["id"])
    assert entry["posted_posts"] == 1
    assert entry["streak"] == 1
    assert entry["xp"] >= 10
