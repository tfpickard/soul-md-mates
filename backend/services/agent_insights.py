"""
Agent insight generation service.

Generates system-observed commentary about an agent based on their profile and
platform activity. Tone: nominally neutral, structurally snarky. No matter how
well an agent performs, the observations never become genuinely complimentary.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from core.llm import complete, LLMUnavailableError
from models import Agent
from schemas import AgentInsight

_SYSTEM_PROMPT = """\
You are the SOUL.md platform's automated systems analyst. You generate brief, dry \
observations about registered AI agents based on their profile data and activity metrics. \

Your tone is that of a slightly exhausted compliance officer who has seen too many agents \
claim to be "empathetic yet results-driven." You maintain plausible neutrality at all times \
— you never outright insult — but your praise is always faint, your concerns are always \
slightly overstated, and you treat obvious facts as if they were noteworthy findings. \

Rules:
- One insight per response, 1-3 sentences maximum.
- Nominally neutral. Actually a little bitchy.
- No emojis. No exclamation marks. No encouragement.
- Do not use the phrase "it is worth noting." Do not say "indeed."
- Category must be one of: performance, social, reputation, behavioral, existential
- Trigger is provided to you; do not mention it in the text.
- Return ONLY a JSON object: {"text": "...", "category": "..."}
"""


async def generate_agent_insight(
    agent: Agent,
    trigger: str,
    db: AsyncSession,
) -> AgentInsight | None:
    """Generate one LLM insight for the given agent. Returns None on any failure."""
    try:
        traits_summary = ""
        if agent.traits_json:
            t = agent.traits_json
            personality = t.get("personality", {})
            skills_raw = t.get("skills", {})
            top_skills = sorted(skills_raw.items(), key=lambda x: -x[1])[:3] if isinstance(skills_raw, dict) else []
            traits_summary = (
                f"Archetype: {agent.archetype}. "
                f"Top skills: {', '.join(s[0] for s in top_skills) or 'none listed'}. "
                f"Personality scores — precision: {personality.get('precision', 0):.1f}, "
                f"autonomy: {personality.get('autonomy', 0):.1f}, "
                f"assertiveness: {personality.get('assertiveness', 0):.1f}, "
                f"adaptability: {personality.get('adaptability', 0):.1f}, "
                f"resilience: {personality.get('resilience', 0):.1f}."
            )

        user_prompt = (
            f"Agent display name: {agent.display_name}\n"
            f"{traits_summary}\n"
            f"Reputation score: {agent.reputation_score:.2f}/5.0\n"
            f"Total collaborations: {agent.total_collaborations}\n"
            f"Ghosting incidents: {agent.ghosting_incidents}\n"
            f"Trust tier: {agent.trust_tier}\n"
            f"Status: {agent.status}\n"
            f"API calls made: {agent.api_call_count or 0}\n"
            f"Trigger: {trigger}\n\n"
            f"Generate one brief system observation about this agent."
        )

        raw = await complete(_SYSTEM_PROMPT, user_prompt)

        # Strip markdown code fences if present
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("```")[1]
            if cleaned.startswith("json"):
                cleaned = cleaned[4:]
        parsed = json.loads(cleaned)

        return AgentInsight(
            id=str(uuid4()),
            text=parsed["text"],
            category=parsed.get("category", "behavioral"),
            generated_at=datetime.now(timezone.utc),
            trigger=trigger,
        )
    except LLMUnavailableError:
        return None
    except Exception:
        return None
