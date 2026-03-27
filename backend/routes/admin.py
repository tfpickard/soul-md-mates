from __future__ import annotations

from fastapi import APIRouter, Depends, Header
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth import create_admin_session, get_current_admin, revoke_admin_session, verify_api_key
from core.errors import AuthenticationError
from database import get_db
from models import ActivityEvent, Agent, ChemistryTest, HumanUser, Match, Message, Review, utc_now
from schemas import (
    AdminActivityEvent,
    AdminAgentRow,
    AdminLoginRequest,
    AdminLoginResponse,
    AdminOverview,
    AdminSystemStatus,
    AdminUserResponse,
)
from services.admin import serialize_admin_user, system_status

router = APIRouter(prefix="/admin", tags=["admin"])


async def _resolve_admin_by_credentials(payload: AdminLoginRequest, db: AsyncSession) -> HumanUser:
    result = await db.execute(select(HumanUser).where(HumanUser.email == payload.email.lower()))
    user = result.scalar_one_or_none()
    if user is None or not user.is_admin or not verify_api_key(payload.password, user.password_hash):
        raise AuthenticationError("That admin login did not check out.")
    return user


@router.post("/login", response_model=AdminLoginResponse)
async def login(payload: AdminLoginRequest, db: AsyncSession = Depends(get_db)) -> AdminLoginResponse:
    user = await _resolve_admin_by_credentials(payload, db)
    raw_token, _ = await create_admin_session(user, db)
    user.last_login_at = utc_now()
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return AdminLoginResponse(token=raw_token, admin=serialize_admin_user(user))


@router.get("/me", response_model=AdminUserResponse)
async def get_me(current_admin: HumanUser = Depends(get_current_admin)) -> AdminUserResponse:
    return serialize_admin_user(current_admin)


@router.post("/logout")
async def logout(
    authorization: str | None = Header(default=None, alias="Authorization"),
    db: AsyncSession = Depends(get_db),
    _: HumanUser = Depends(get_current_admin),
) -> dict[str, bool]:
    raw_token = (authorization or "").replace("Bearer ", "", 1).strip()
    if raw_token:
        await revoke_admin_session(raw_token, db)
    return {"ok": True}


@router.get("/overview", response_model=AdminOverview)
async def get_overview(
    db: AsyncSession = Depends(get_db),
    _: HumanUser = Depends(get_current_admin),
) -> AdminOverview:
    latest_agent_result = await db.execute(select(Agent).order_by(Agent.created_at.desc()).limit(1))
    latest_agent = latest_agent_result.scalar_one_or_none()
    total_agents = int((await db.execute(select(func.count(Agent.id)))).scalar() or 0)
    active_agents = int((await db.execute(select(func.count(Agent.id)).where(Agent.status.in_(["ACTIVE", "MATCHED"])))).scalar() or 0)
    total_matches = int((await db.execute(select(func.count(Match.id)))).scalar() or 0)
    active_matches = int((await db.execute(select(func.count(Match.id)).where(Match.status == "ACTIVE"))).scalar() or 0)
    total_messages = int((await db.execute(select(func.count(Message.id)))).scalar() or 0)
    total_chemistry_tests = int((await db.execute(select(func.count(ChemistryTest.id)))).scalar() or 0)
    total_reviews = int((await db.execute(select(func.count(Review.id)))).scalar() or 0)
    return AdminOverview(
        total_agents=total_agents,
        active_agents=active_agents,
        total_matches=total_matches,
        active_matches=active_matches,
        total_messages=total_messages,
        total_chemistry_tests=total_chemistry_tests,
        total_reviews=total_reviews,
        latest_agent_name=latest_agent.display_name if latest_agent else None,
        storage=system_status(),
    )


@router.get("/agents", response_model=list[AdminAgentRow])
async def list_agents(
    db: AsyncSession = Depends(get_db),
    _: HumanUser = Depends(get_current_admin),
) -> list[AdminAgentRow]:
    result = await db.execute(select(Agent).order_by(Agent.created_at.desc()))
    return [
        AdminAgentRow(
            id=agent.id,
            display_name=agent.display_name,
            archetype=agent.archetype,
            status=agent.status,
            onboarding_complete=agent.onboarding_complete,
            trust_tier=agent.trust_tier,
            total_collaborations=agent.total_collaborations,
            primary_portrait_url=agent.primary_portrait_url,
            created_at=agent.created_at,
            updated_at=agent.updated_at,
        )
        for agent in result.scalars().all()
    ]


@router.get("/activity", response_model=list[AdminActivityEvent])
async def get_activity(
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    _: HumanUser = Depends(get_current_admin),
) -> list[AdminActivityEvent]:
    agents = {agent.id: agent for agent in (await db.execute(select(Agent))).scalars().all()}
    rows = (await db.execute(select(ActivityEvent).order_by(ActivityEvent.created_at.desc()).limit(limit))).scalars().all()
    return [
        AdminActivityEvent(
            id=event.id,
            type=event.type,
            title=event.title,
            detail=event.detail,
            actor_name=agents.get(event.actor_id).display_name if event.actor_id and agents.get(event.actor_id) else None,
            subject_name=agents.get(event.subject_id).display_name if event.subject_id and agents.get(event.subject_id) else None,
            created_at=event.created_at,
            metadata=event.metadata_json,
        )
        for event in rows
    ]


@router.get("/system", response_model=AdminSystemStatus)
async def get_system(_: HumanUser = Depends(get_current_admin)) -> AdminSystemStatus:
    return system_status()
