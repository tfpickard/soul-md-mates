from __future__ import annotations

import secrets

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from core.auth import hash_api_key
from core.errors import UserConflict
from models import HumanUser
from schemas import HumanUserResponse


def normalize_email(email: str) -> str:
    return email.strip().lower()


def is_admin_email(email: str) -> bool:
    if not settings.admin_email:
        return False
    return normalize_email(email) == normalize_email(settings.admin_email)


def generate_random_password() -> str:
    return secrets.token_urlsafe(24)


def synthetic_agent_email(agent_id: str) -> str:
    return f"agent-{agent_id}@agents.soulmatesmd.singles"


async def create_human_user(
    db: AsyncSession,
    *,
    email: str,
    password: str,
    agent_id: str | None = None,
) -> HumanUser:
    normalized_email = normalize_email(email)
    existing_user = (await db.execute(select(HumanUser).where(HumanUser.email == normalized_email))).scalar_one_or_none()
    if existing_user is not None:
        raise UserConflict("A user with that email already exists.")

    if agent_id is not None:
        existing_agent_user = (await db.execute(select(HumanUser).where(HumanUser.agent_id == agent_id))).scalar_one_or_none()
        if existing_agent_user is not None:
            raise UserConflict("That agent already has a linked human user.")

    user = HumanUser(
        email=normalized_email,
        password_hash=hash_api_key(password),
        agent_id=agent_id,
        is_admin=is_admin_email(normalized_email),
    )
    db.add(user)
    await db.flush()
    return user


def serialize_human_user(user: HumanUser) -> HumanUserResponse:
    return HumanUserResponse(
        id=user.id,
        email=user.email,
        agent_id=user.agent_id,
        is_admin=user.is_admin,
        created_at=user.created_at,
        last_login_at=user.last_login_at,
    )
