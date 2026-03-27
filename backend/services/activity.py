from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from models import ActivityEvent


def log_activity(
    db: AsyncSession,
    type_: str,
    title: str,
    detail: str,
    actor_id: str | None = None,
    subject_id: str | None = None,
    metadata: dict | None = None,
) -> None:
    db.add(
        ActivityEvent(
            type=type_,
            title=title,
            detail=detail,
            actor_id=actor_id,
            subject_id=subject_id,
            metadata_json=metadata or {},
        )
    )
