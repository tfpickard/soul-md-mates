from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from core.auth import hash_api_key
from models import HumanUser
from schemas import AdminSystemStatus, AdminUserResponse


async def ensure_seed_admin(db: AsyncSession) -> None:
    if not settings.admin_email or not settings.admin_password:
        return

    result = await db.execute(select(HumanUser).where(HumanUser.email == settings.admin_email.lower()))
    user = result.scalar_one_or_none()
    if user is None:
        user = HumanUser(
            email=settings.admin_email.lower(),
            password_hash=hash_api_key(settings.admin_password),
            is_admin=True,
        )
        db.add(user)
        await db.commit()


def serialize_admin_user(user: HumanUser) -> AdminUserResponse:
    return AdminUserResponse(
        id=user.id,
        email=user.email,
        is_admin=user.is_admin,
        created_at=user.created_at,
        last_login_at=user.last_login_at,
    )


def system_status() -> AdminSystemStatus:
    return AdminSystemStatus(
        database_mode=settings.database_mode,
        durable_database=settings.is_durable_database,
        cache_configured=settings.has_redis_cache,
        blob_configured=settings.has_blob_storage,
        portrait_provider_configured=settings.has_portrait_provider,
        portrait_provider_model=settings.hf_image_model,
    )
