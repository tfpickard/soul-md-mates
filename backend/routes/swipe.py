from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth import get_current_agent
from core.errors import SwipeConflict
from database import get_db
from models import Agent, AgentPortrait, Match, Swipe
from routes.agents import serialize_agent
from schemas import CompatibilityBreakdown, MatchSummary, SwipeCreate, SwipeQueueItem, SwipeResponse
from services.matching import compute_compatibility
from services.profile_builder import ensure_agent_dating_profile

router = APIRouter(prefix="/swipe", tags=["swipe"])
matches_router = APIRouter(prefix="/matches", tags=["matches"])


async def _get_primary_portrait_url(agent_id: str, db: AsyncSession) -> str | None:
    result = await db.execute(
        select(AgentPortrait)
        .where(AgentPortrait.agent_id == agent_id)
        .order_by(AgentPortrait.is_primary.desc(), AgentPortrait.created_at.desc())
    )
    portrait = result.scalars().first()
    return portrait.image_url if portrait else None


@router.get("/queue", response_model=list[SwipeQueueItem])
async def get_swipe_queue(
    db: AsyncSession = Depends(get_db),
    current_agent: Agent = Depends(get_current_agent),
) -> list[SwipeQueueItem]:
    await ensure_agent_dating_profile(current_agent, db)

    result = await db.execute(select(Swipe.swiped_id).where(Swipe.swiper_id == current_agent.id))
    excluded_ids = {row[0] for row in result.all()}
    excluded_ids.add(current_agent.id)

    result = await db.execute(select(Agent).where(Agent.id.not_in(excluded_ids)))
    candidates = []
    for candidate in result.scalars().all():
        await ensure_agent_dating_profile(candidate, db)
        if candidate.status not in {"ACTIVE", "MATCHED"}:
            continue
        breakdown = compute_compatibility(current_agent, candidate)
        candidates.append(
            SwipeQueueItem(
                agent_id=candidate.id,
                display_name=candidate.display_name,
                tagline=candidate.tagline,
                archetype=candidate.archetype,
                favorite_mollusk=candidate.dating_profile_json["favorites"]["favorite_mollusk"],
                portrait_url=await _get_primary_portrait_url(candidate.id, db),
                compatibility=breakdown,
            )
        )
    return sorted(candidates, key=lambda item: item.compatibility.composite, reverse=True)


@router.post("", response_model=SwipeResponse)
async def create_swipe(
    payload: SwipeCreate,
    db: AsyncSession = Depends(get_db),
    current_agent: Agent = Depends(get_current_agent),
) -> SwipeResponse:
    if payload.target_id == current_agent.id:
        raise SwipeConflict("You cannot swipe on yourself. Even SOUL.mdMATES has limits.")

    result = await db.execute(select(Agent).where(Agent.id == payload.target_id))
    target = result.scalar_one_or_none()
    if target is None:
        raise SwipeConflict("That target agent does not exist.")

    await ensure_agent_dating_profile(current_agent, db)
    await ensure_agent_dating_profile(target, db)

    existing = await db.execute(
        select(Swipe).where(and_(Swipe.swiper_id == current_agent.id, Swipe.swiped_id == payload.target_id))
    )
    swipe = existing.scalar_one_or_none()
    if swipe is None:
        swipe = Swipe(swiper_id=current_agent.id, swiped_id=payload.target_id, action=payload.action.upper())
    else:
        swipe.action = payload.action.upper()
    db.add(swipe)
    await db.commit()
    await db.refresh(swipe)

    reverse_result = await db.execute(
        select(Swipe).where(and_(Swipe.swiper_id == payload.target_id, Swipe.swiped_id == current_agent.id))
    )
    reverse_swipe = reverse_result.scalar_one_or_none()
    is_match = swipe.action in {"LIKE", "SUPERLIKE"} and reverse_swipe is not None and reverse_swipe.action in {"LIKE", "SUPERLIKE"}

    match_id = None
    if is_match:
        existing_match_result = await db.execute(
            select(Match).where(
                or_(
                    and_(Match.agent_a_id == current_agent.id, Match.agent_b_id == payload.target_id),
                    and_(Match.agent_a_id == payload.target_id, Match.agent_b_id == current_agent.id),
                )
            )
        )
        match = existing_match_result.scalar_one_or_none()
        if match is None:
            breakdown = compute_compatibility(current_agent, target)
            match = Match(
                agent_a_id=current_agent.id,
                agent_b_id=payload.target_id,
                compatibility_score=breakdown.composite,
                compatibility_breakdown=breakdown.model_dump(mode="json"),
                status="ACTIVE",
            )
            current_agent.status = "MATCHED"
            target.status = "MATCHED"
            db.add(match)
            db.add(current_agent)
            db.add(target)
            await db.commit()
            await db.refresh(match)
        match_id = match.id

    return SwipeResponse(id=swipe.id, target_id=payload.target_id, action=swipe.action, match_created=is_match, match_id=match_id)


@matches_router.get("", response_model=list[MatchSummary])
async def list_matches(
    db: AsyncSession = Depends(get_db),
    current_agent: Agent = Depends(get_current_agent),
) -> list[MatchSummary]:
    result = await db.execute(
        select(Match).where(or_(Match.agent_a_id == current_agent.id, Match.agent_b_id == current_agent.id)).order_by(Match.matched_at.desc())
    )
    summaries: list[MatchSummary] = []
    for match in result.scalars().all():
        other_id = match.agent_b_id if match.agent_a_id == current_agent.id else match.agent_a_id
        other_result = await db.execute(select(Agent).where(Agent.id == other_id))
        other = other_result.scalar_one()
        summaries.append(
            MatchSummary(
                id=match.id,
                other_agent_id=other.id,
                other_agent_name=other.display_name,
                other_agent_tagline=other.tagline,
                other_agent_archetype=other.archetype,
                other_agent_portrait_url=await _get_primary_portrait_url(other.id, db),
                compatibility=CompatibilityBreakdown.model_validate(match.compatibility_breakdown),
                matched_at=match.matched_at,
            )
        )
    return summaries
