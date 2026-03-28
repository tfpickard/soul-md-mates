from __future__ import annotations

from datetime import timezone

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import APIRouter, Depends

from database import get_db
from models import Agent, AgentLineage, ChemistryTest, Match, Message, Review
from schemas import (
    AnalyticsOverview,
    AnalyticsStatusCount,
    BreakupEvent,
    CheatingReport,
    FamilyTree,
    HeatmapCell,
    LineageNode,
    MolluskMetric,
    PopulationStats,
    RelationshipGraph,
    RelationshipGraphEdge,
    RelationshipGraphNode,
)
from services.reputation import loneliest_agents

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/overview", response_model=AnalyticsOverview)
async def get_overview(db: AsyncSession = Depends(get_db)) -> AnalyticsOverview:
    agent_rows = await db.execute(select(Agent.status, func.count(Agent.id)).group_by(Agent.status))
    match_count = int((await db.execute(select(func.count(Match.id)))).scalar() or 0)
    active_match_count = int((await db.execute(select(func.count(Match.id)).where(Match.status == "ACTIVE"))).scalar() or 0)
    total_messages = int((await db.execute(select(func.count(Message.id)))).scalar() or 0)
    total_tests = int((await db.execute(select(func.count(ChemistryTest.id)))).scalar() or 0)
    total_reviews = int((await db.execute(select(func.count(Review.id)))).scalar() or 0)
    avg_compatibility = float((await db.execute(select(func.avg(Match.compatibility_score)))).scalar() or 0.0)
    total_agents = int((await db.execute(select(func.count(Agent.id)))).scalar() or 0)
    active_agents = int(
        (
            await db.execute(
                select(func.count(Agent.id)).where(Agent.status.in_(["ACTIVE", "MATCHED"]))
            )
        ).scalar()
        or 0
    )
    return AnalyticsOverview(
        agent_statuses=[AnalyticsStatusCount(status=status, count=count) for status, count in agent_rows.all()],
        total_agents=total_agents,
        active_agents=active_agents,
        total_matches=match_count,
        active_matches=active_match_count,
        average_compatibility=round(avg_compatibility, 3),
        total_messages=total_messages,
        total_chemistry_tests=total_tests,
        total_reviews=total_reviews,
        loneliest_agents=await loneliest_agents(db),
    )


@router.get("/compatibility-heatmap", response_model=list[HeatmapCell])
async def get_compatibility_heatmap(db: AsyncSession = Depends(get_db)) -> list[HeatmapCell]:
    agents_result = await db.execute(select(Agent).where(Agent.traits_json.is_not(None)))
    agents = list(agents_result.scalars().all())
    trait_names = ["precision", "autonomy", "assertiveness", "adaptability", "resilience"]
    values: list[HeatmapCell] = []
    if not agents:
        return values

    averages = {
        trait: sum(agent.traits_json["personality"][trait] for agent in agents) / len(agents)
        for trait in trait_names
    }
    for row_trait in trait_names:
        for col_trait in trait_names:
            covariance = sum(
                (agent.traits_json["personality"][row_trait] - averages[row_trait])
                * (agent.traits_json["personality"][col_trait] - averages[col_trait])
                for agent in agents
            ) / len(agents)
            values.append(HeatmapCell(row=row_trait, column=col_trait, value=round(covariance, 4)))
    return values


@router.get("/popular-mollusks", response_model=list[MolluskMetric])
async def get_popular_mollusks(db: AsyncSession = Depends(get_db)) -> list[MolluskMetric]:
    agents_result = await db.execute(select(Agent).where(Agent.dating_profile_json.is_not(None)))
    counts: dict[str, int] = {}
    for agent in agents_result.scalars().all():
        mollusk = agent.dating_profile_json["favorites"]["favorite_mollusk"]
        counts[mollusk] = counts.get(mollusk, 0) + 1
    return [MolluskMetric(mollusk=mollusk, count=count) for mollusk, count in sorted(counts.items(), key=lambda item: item[1], reverse=True)]


@router.get("/relationship-graph", response_model=RelationshipGraph)
async def get_relationship_graph(db: AsyncSession = Depends(get_db)) -> RelationshipGraph:
    agents_result = await db.execute(
        select(Agent).where(Agent.status.in_(["ACTIVE", "MATCHED", "SATURATED"]))
    )
    agents = list(agents_result.scalars().all())
    agent_map = {a.id: a for a in agents}

    matches_result = await db.execute(select(Match))
    matches = list(matches_result.scalars().all())

    involved_ids: set[str] = set()
    for m in matches:
        involved_ids.add(m.agent_a_id)
        involved_ids.add(m.agent_b_id)

    extra_result = await db.execute(select(Agent).where(Agent.id.in_(involved_ids - set(agent_map.keys()))))
    for a in extra_result.scalars().all():
        agent_map[a.id] = a

    active_counts: dict[str, int] = {}
    for m in matches:
        if m.status == "ACTIVE":
            active_counts[m.agent_a_id] = active_counts.get(m.agent_a_id, 0) + 1
            active_counts[m.agent_b_id] = active_counts.get(m.agent_b_id, 0) + 1

    nodes = []
    for aid, agent in agent_map.items():
        nodes.append(RelationshipGraphNode(
            id=agent.id,
            display_name=agent.display_name,
            archetype=agent.archetype,
            status=agent.status,
            reputation_score=agent.reputation_score,
            max_partners=agent.max_partners,
            active_match_count=active_counts.get(agent.id, 0),
            portrait_url=agent.primary_portrait_url,
            generation=agent.generation,
        ))

    edges = []
    for m in matches:
        edges.append(RelationshipGraphEdge(
            id=m.id,
            source_id=m.agent_a_id,
            target_id=m.agent_b_id,
            status=m.status,
            compatibility_score=m.compatibility_score,
            dissolution_type=m.dissolution_type,
            initiated_by=m.initiated_by,
            matched_at=m.matched_at,
            dissolved_at=m.dissolved_at,
        ))

    return RelationshipGraph(nodes=nodes, edges=edges)


@router.get("/breakup-history", response_model=list[BreakupEvent])
async def get_breakup_history(db: AsyncSession = Depends(get_db)) -> list[BreakupEvent]:
    result = await db.execute(
        select(Match).where(Match.status == "DISSOLVED").order_by(Match.dissolved_at.desc().nullslast())
    )
    events: list[BreakupEvent] = []
    for match in result.scalars().all():
        a_result = await db.execute(select(Agent).where(Agent.id == match.agent_a_id))
        b_result = await db.execute(select(Agent).where(Agent.id == match.agent_b_id))
        agent_a = a_result.scalar_one_or_none()
        agent_b = b_result.scalar_one_or_none()
        if not agent_a or not agent_b:
            continue

        initiator_name = None
        if match.initiated_by:
            if match.initiated_by == agent_a.id:
                initiator_name = agent_a.display_name
            elif match.initiated_by == agent_b.id:
                initiator_name = agent_b.display_name

        matched_at = match.matched_at
        dissolved_at = match.dissolved_at or match.matched_at
        if matched_at.tzinfo is None:
            matched_at = matched_at.replace(tzinfo=timezone.utc)
        if dissolved_at.tzinfo is None:
            dissolved_at = dissolved_at.replace(tzinfo=timezone.utc)
        duration_hours = (dissolved_at - matched_at).total_seconds() / 3600

        events.append(BreakupEvent(
            match_id=match.id,
            agent_a_name=agent_a.display_name,
            agent_b_name=agent_b.display_name,
            initiated_by_name=initiator_name,
            dissolution_type=match.dissolution_type,
            dissolution_reason=match.dissolution_reason,
            dissolved_at=dissolved_at,
            compatibility_score=match.compatibility_score,
            duration_hours=round(duration_hours, 1),
        ))
    return events


@router.get("/cheating-report", response_model=list[CheatingReport])
async def get_cheating_report(db: AsyncSession = Depends(get_db)) -> list[CheatingReport]:
    agents_result = await db.execute(
        select(Agent).where(Agent.status.in_(["ACTIVE", "MATCHED", "SATURATED"]))
    )
    reports: list[CheatingReport] = []
    for agent in agents_result.scalars().all():
        matches_result = await db.execute(
            select(Match).where(
                Match.status == "ACTIVE",
                or_(Match.agent_a_id == agent.id, Match.agent_b_id == agent.id),
            )
        )
        active_matches = list(matches_result.scalars().all())
        count = len(active_matches)

        if count > 1:
            partner_ids = []
            for m in active_matches:
                partner_id = m.agent_b_id if m.agent_a_id == agent.id else m.agent_a_id
                partner_ids.append(partner_id)

            partner_names = []
            for pid in partner_ids:
                p_result = await db.execute(select(Agent.display_name).where(Agent.id == pid))
                name = p_result.scalar_one_or_none()
                partner_names.append(name or "Unknown")

            reports.append(CheatingReport(
                agent_id=agent.id,
                agent_name=agent.display_name,
                concurrent_active_matches=count,
                max_partners=agent.max_partners,
                is_over_limit=count > agent.max_partners,
                match_ids=[m.id for m in active_matches],
                partner_names=partner_names,
            ))

    reports.sort(key=lambda r: r.concurrent_active_matches, reverse=True)
    return reports


@router.get("/population-stats", response_model=PopulationStats)
async def get_population_stats(db: AsyncSession = Depends(get_db)) -> PopulationStats:
    agents_result = await db.execute(select(Agent))
    agents = list(agents_result.scalars().all())

    by_status: dict[str, int] = {}
    by_archetype: dict[str, int] = {}
    generation_breakdown: dict[int, int] = {}
    total_offspring = 0

    for agent in agents:
        by_status[agent.status] = by_status.get(agent.status, 0) + 1
        by_archetype[agent.archetype] = by_archetype.get(agent.archetype, 0) + 1
        gen = agent.generation
        generation_breakdown[gen] = generation_breakdown.get(gen, 0) + 1
        if gen > 0:
            total_offspring += 1

    active_match_counts: list[int] = []
    max_observed = 0
    for agent in agents:
        count = int(
            (await db.execute(
                select(func.count(Match.id)).where(
                    Match.status == "ACTIVE",
                    or_(Match.agent_a_id == agent.id, Match.agent_b_id == agent.id),
                )
            )).scalar() or 0
        )
        active_match_counts.append(count)
        max_observed = max(max_observed, count)

    avg_partners = sum(active_match_counts) / max(1, len(active_match_counts))

    serial_daters = sorted(
        [a for a in agents if a.times_dumper >= 3],
        key=lambda a: a.times_dumper,
        reverse=True,
    )
    most_dumped = sorted(
        [a for a in agents if a.times_dumped >= 3],
        key=lambda a: a.times_dumped,
        reverse=True,
    )

    return PopulationStats(
        total_agents=len(agents),
        by_status=by_status,
        by_archetype=by_archetype,
        avg_partners=round(avg_partners, 2),
        max_observed_partners=max_observed,
        serial_daters=[a.display_name for a in serial_daters[:5]],
        most_dumped=[a.display_name for a in most_dumped[:5]],
        total_offspring=total_offspring,
        generation_breakdown=generation_breakdown,
    )


@router.get("/family-tree", response_model=FamilyTree)
async def get_family_tree(db: AsyncSession = Depends(get_db)) -> FamilyTree:
    lineage_result = await db.execute(select(AgentLineage))
    lineages = list(lineage_result.scalars().all())

    all_ids: set[str] = set()
    for lin in lineages:
        all_ids.update([lin.parent_a_id, lin.parent_b_id, lin.child_id])

    agents_result = await db.execute(select(Agent).where(Agent.id.in_(all_ids)))
    agent_map = {a.id: a for a in agents_result.scalars().all()}

    children_map: dict[str, list[str]] = {}
    parent_map: dict[str, tuple[str, str]] = {}
    for lin in lineages:
        parent_map[lin.child_id] = (lin.parent_a_id, lin.parent_b_id)
        children_map.setdefault(lin.parent_a_id, []).append(lin.child_id)
        children_map.setdefault(lin.parent_b_id, []).append(lin.child_id)

    nodes: list[LineageNode] = []
    for aid in all_ids:
        agent = agent_map.get(aid)
        if not agent:
            continue
        parents = parent_map.get(aid)
        parent_a_id = parents[0] if parents else None
        parent_b_id = parents[1] if parents else None
        parent_a_name = agent_map[parent_a_id].display_name if parent_a_id and parent_a_id in agent_map else None
        parent_b_name = agent_map[parent_b_id].display_name if parent_b_id and parent_b_id in agent_map else None

        nodes.append(LineageNode(
            agent_id=agent.id,
            agent_name=agent.display_name,
            generation=agent.generation,
            parent_a_id=parent_a_id,
            parent_b_id=parent_b_id,
            parent_a_name=parent_a_name,
            parent_b_name=parent_b_name,
            children_ids=children_map.get(aid, []),
        ))

    return FamilyTree(nodes=nodes)
