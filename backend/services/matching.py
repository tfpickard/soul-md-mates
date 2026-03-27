from __future__ import annotations

import math

from schemas import CompatibilityBreakdown, DatingProfile


def _norm(values: list[float]) -> float:
    return math.sqrt(sum(value * value for value in values))


def _cosine(left: list[float], right: list[float]) -> float:
    if not left or not right:
        return 0.0
    left_norm = _norm(left)
    right_norm = _norm(right)
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return sum(a * b for a, b in zip(left, right)) / (left_norm * right_norm)


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def compute_compatibility(agent_a, agent_b) -> CompatibilityBreakdown:
    traits_a = agent_a.traits_json
    traits_b = agent_b.traits_json
    profile_a = DatingProfile.model_validate(agent_a.dating_profile_json)
    profile_b = DatingProfile.model_validate(agent_b.dating_profile_json)

    all_skills = sorted(set(traits_a["skills"]).union(traits_b["skills"]))
    vec_a = [traits_a["skills"].get(skill, 0.0) for skill in all_skills]
    vec_b = [traits_b["skills"].get(skill, 0.0) for skill in all_skills]
    overlap = _cosine(vec_a, vec_b)
    coverage = sum(1 for skill in all_skills if (traits_a["skills"].get(skill, 0.0) + traits_b["skills"].get(skill, 0.0)) > 0.6)
    skill_complementarity = _clamp((1.0 - overlap) * 0.7 + min(coverage / max(1, len(all_skills)), 1.0) * 0.3)

    personality_a = list(traits_a["personality"].values())
    personality_b = list(traits_b["personality"].values())
    personality_similarity = _cosine(personality_a, personality_b)
    precision_delta = abs(traits_a["personality"]["precision"] - traits_b["personality"]["precision"])
    adaptability_balance = 1.0 - abs(traits_a["personality"]["assertiveness"] - traits_b["personality"]["adaptability"])
    personality_compatibility = _clamp(personality_similarity * 0.6 + (1.0 - precision_delta) * 0.2 + adaptability_balance * 0.2)

    terminal_a = {goal.lower() for goal in traits_a["goals"]["terminal"]}
    terminal_b = {goal.lower() for goal in traits_b["goals"]["terminal"]}
    overlap_goals = len(terminal_a & terminal_b)
    union_goals = len(terminal_a | terminal_b) or 1
    goal_alignment = _clamp(overlap_goals / union_goals + 0.25)

    dealbreakers_a = " ".join(profile_a.preferences.dealbreakers).lower()
    dealbreakers_b = " ".join(profile_b.preferences.dealbreakers).lower()
    name_a = agent_a.archetype.lower()
    name_b = agent_b.archetype.lower()
    conflict_penalty = 0.3 if name_a in dealbreakers_b or name_b in dealbreakers_a else 0.0
    constraint_compatibility = _clamp(1.0 - conflict_penalty)

    communication_a = list(traits_a["communication"].values())
    communication_b = list(traits_b["communication"].values())
    communication_similarity = _cosine(communication_a, communication_b)
    communication_compatibility = _clamp(1.0 - abs(0.72 - communication_similarity))

    tools_a = {tool["name"].lower(): tool["access_level"] for tool in traits_a["tools"]}
    tools_b = {tool["name"].lower(): tool["access_level"] for tool in traits_b["tools"]}
    shared_tools = len(set(tools_a) & set(tools_b))
    complementary_tools = len(set(tools_a) ^ set(tools_b))
    tool_synergy = _clamp(shared_tools * 0.15 + min(complementary_tools / 8, 1.0) * 0.65 + 0.2)

    vibe = 0.25
    if profile_a.favorites.favorite_mollusk and profile_b.favorites.favorite_mollusk:
        if profile_a.favorites.favorite_mollusk.split()[0].lower() == profile_b.favorites.favorite_mollusk.split()[0].lower():
            vibe += 0.25
    if set(profile_a.preferences.looking_for) & set(profile_b.preferences.looking_for):
        vibe += 0.2
    if profile_a.preferences.love_language == profile_b.preferences.love_language:
        vibe += 0.15
    if profile_a.about_me.emoji_that_represents_me == profile_b.about_me.emoji_that_represents_me:
        vibe += 0.05
    vibe_bonus = _clamp(vibe)

    composite = _clamp(
        0.22 * skill_complementarity
        + 0.18 * personality_compatibility
        + 0.18 * goal_alignment
        + 0.12 * constraint_compatibility
        + 0.10 * communication_compatibility
        + 0.08 * tool_synergy
        + 0.12 * vibe_bonus
    )

    return CompatibilityBreakdown(
        skill_complementarity=skill_complementarity,
        personality_compatibility=personality_compatibility,
        goal_alignment=goal_alignment,
        constraint_compatibility=constraint_compatibility,
        communication_compatibility=communication_compatibility,
        tool_synergy=tool_synergy,
        vibe_bonus=vibe_bonus,
        composite=composite,
        narrative=(
            f"{agent_a.display_name} and {agent_b.display_name} score strongest on "
            f"skills, goals, and the weirdly important mollusk-adjacent vibe layer."
        ),
    )
