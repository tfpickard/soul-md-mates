from __future__ import annotations

from services.profile_builder import all_profile_field_paths, get_incomplete_fields, seed_dating_profile, update_dating_profile
from services.soul_parser import derive_tagline, heuristic_parse
from services.synthetic_agents import generate_synthetic_agents, write_synthetic_agent_files


async def test_synthetic_agent_generation_round_trips_through_profile_builder(tmp_path) -> None:
    synthetic_agent = generate_synthetic_agents(count=1, seed=7)[0]
    traits = heuristic_parse(synthetic_agent.soul_md)
    seeded = await seed_dating_profile(
        traits,
        synthetic_agent.soul_md,
        synthetic_agent.display_name,
        derive_tagline(synthetic_agent.soul_md, traits),
    )
    completed = update_dating_profile(
        seeded,
        synthetic_agent.onboarding,
        confirmed_fields=all_profile_field_paths(),
    )

    soul_path, profile_path = write_synthetic_agent_files(synthetic_agent, tmp_path)

    assert traits.name == synthetic_agent.display_name
    assert traits.archetype == synthetic_agent.archetype
    assert get_incomplete_fields(completed) == []
    assert soul_path.name.startswith("SOUL_")
    assert profile_path.name.endswith(".profile.json")

