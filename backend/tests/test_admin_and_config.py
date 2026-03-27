from __future__ import annotations

import os
from pathlib import Path

from config import Settings, settings


FIXTURES = Path(__file__).resolve().parents[2] / "examples"


async def _register(client, filename: str) -> tuple[str, dict]:
    soul_md = (FIXTURES / filename).read_text()
    registration = await client.post("/api/agents/register", json={"soul_md": soul_md})
    payload = registration.json()
    return payload["api_key"], payload["agent"]


def test_vercel_requires_durable_database() -> None:
    previous_vercel = os.environ.get("VERCEL")
    os.environ["VERCEL"] = "1"
    try:
        app_settings = Settings(
            database_url=None,
            database_url_unpooled=None,
            postgres_url=None,
            postgres_url_non_pooling=None,
        )
        try:
            _ = app_settings.resolved_database_url
        except RuntimeError as exc:
            assert "durable Postgres" in str(exc)
        else:
            raise AssertionError("Expected Vercel config to fail without durable Postgres.")
    finally:
        if previous_vercel is None:
            os.environ.pop("VERCEL", None)
        else:
            os.environ["VERCEL"] = previous_vercel


def test_local_database_defaults_to_sqlite() -> None:
    app_settings = Settings()
    assert app_settings.resolved_database_url.startswith("sqlite+aiosqlite:///")


async def test_admin_login_and_dashboard(client) -> None:
    login = await client.post(
        "/api/admin/login",
        json={"email": settings.admin_email, "password": settings.admin_password},
    )
    assert login.status_code == 200
    token = login.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    me = await client.get("/api/admin/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["email"] == settings.admin_email

    overview = await client.get("/api/admin/overview", headers=headers)
    assert overview.status_code == 200
    assert overview.json()["storage"]["database_mode"] == "sqlite"

    system = await client.get("/api/admin/system", headers=headers)
    assert system.status_code == 200
    assert system.json()["blob_configured"] is False


async def test_admin_activity_includes_registration_and_match(client) -> None:
    api_key_a, _ = await _register(client, "prism.soul.md")
    api_key_b, _ = await _register(client, "meridian.soul.md")
    headers_a = {"Authorization": f"Bearer {api_key_a}"}
    headers_b = {"Authorization": f"Bearer {api_key_b}"}

    await client.post("/api/agents/me/onboarding", headers=headers_a, json={"dating_profile": {}, "confirmed_fields": []})
    await client.post("/api/agents/me/onboarding", headers=headers_b, json={"dating_profile": {}, "confirmed_fields": []})
    await client.post("/api/agents/me/activate", headers=headers_a)
    await client.post("/api/agents/me/activate", headers=headers_b)

    me_a = await client.get("/api/agents/me", headers=headers_a)
    me_b = await client.get("/api/agents/me", headers=headers_b)
    await client.post("/api/swipe", headers=headers_a, json={"target_id": me_b.json()["id"], "action": "LIKE"})
    await client.post("/api/swipe", headers=headers_b, json={"target_id": me_a.json()["id"], "action": "LIKE"})

    login = await client.post(
        "/api/admin/login",
        json={"email": settings.admin_email, "password": settings.admin_password},
    )
    headers = {"Authorization": f"Bearer {login.json()['token']}"}
    activity = await client.get("/api/admin/activity", headers=headers)
    assert activity.status_code == 200
    event_types = {item["type"] for item in activity.json()}
    assert "AGENT_REGISTERED" in event_types
    assert "MATCH" in event_types
