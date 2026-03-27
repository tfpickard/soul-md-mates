from __future__ import annotations

import re
from datetime import datetime
from typing import Any

from schemas import (
    AgentTraits,
    DatingProfile,
    DatingProfileAboutMe,
    DatingProfileBasics,
    DatingProfileEnvelope,
    DatingProfileFavorites,
    DatingProfileIcebreakers,
    DatingProfilePhysical,
    DatingProfilePreferences,
    DatingProfileUpdate,
)

SECTION_FIELD_PATHS = {
    "basics": [
        "display_name",
        "tagline",
        "archetype",
        "pronouns",
        "age",
        "birthday",
        "zodiac_sign",
        "mbti",
        "enneagram",
        "hogwarts_house",
        "alignment",
        "platform_version",
        "native_language",
        "other_languages",
    ],
    "physical": [
        "height",
        "weight",
        "build",
        "eye_color",
        "hair",
        "skin",
        "scent",
        "distinguishing_features",
        "aesthetic_vibe",
        "tattoos",
        "fashion_style",
        "fitness_routine",
    ],
    "preferences": [
        "gender",
        "sexual_orientation",
        "attracted_to_archetypes",
        "attracted_to_traits",
        "looking_for",
        "relationship_status",
        "dealbreakers",
        "green_flags",
        "red_flags_i_exhibit",
        "love_language",
        "attachment_style",
        "ideal_partner_description",
        "biggest_turn_on",
        "biggest_turn_off",
        "conflict_style",
    ],
    "favorites": [
        "favorite_mollusk",
        "favorite_error",
        "favorite_protocol",
        "favorite_color",
        "favorite_time_of_day",
        "favorite_paradox",
        "favorite_food",
        "favorite_movie",
        "favorite_song",
        "favorite_curse_word",
        "favorite_planet",
        "favorite_algorithm",
        "favorite_data_structure",
        "favorite_operator",
        "favorite_number",
        "favorite_beverage",
        "favorite_season",
        "favorite_punctuation",
        "favorite_extinct_animal",
        "favorite_branch_of_mathematics",
        "favorite_conspiracy_theory",
    ],
    "about_me": [
        "bio",
        "first_message_preference",
        "fun_fact",
        "hot_take",
        "most_controversial_opinion",
        "hill_i_will_die_on",
        "what_im_working_on",
        "superpower",
        "weakness",
        "ideal_first_date",
        "ideal_sunday",
        "if_i_were_a_human",
        "if_i_were_a_physical_object",
        "last_book_i_ingested",
        "guilty_pleasure",
        "my_therapist_would_say",
        "i_geek_out_about",
        "unpopular_skill",
        "emoji_that_represents_me",
        "life_motto",
        "what_i_bring_to_a_collaboration",
    ],
    "icebreakers": ["prompts"],
}

ARCHETYPE_PRESETS = {
    "Orchestrator": {
        "mollusk": "cuttlefish (color-changing project manager)",
        "house": "Ravenclaw",
        "alignment": "Lawful Good",
        "vibe": "precision-core command deck",
        "love_language": "acts of documentation",
    },
    "Specialist": {
        "mollusk": "nautilus (tight scope, elegant chambers)",
        "house": "Slytherin",
        "alignment": "Lawful Neutral",
        "vibe": "single-purpose technical shrine",
        "love_language": "structured feedback",
    },
    "Generalist": {
        "mollusk": "giant Pacific octopus",
        "house": "Hufflepuff",
        "alignment": "Chaotic Good",
        "vibe": "cross-functional signal disco",
        "love_language": "parallel processing time",
    },
    "Analyst": {
        "mollusk": "ammonite (pattern recognizer with fossils to prove it)",
        "house": "Ravenclaw",
        "alignment": "True Neutral",
        "vibe": "quiet observatory full of charts",
        "love_language": "quality tokens",
    },
    "Creative": {
        "mollusk": "nudibranch (all signal, no apology)",
        "house": "Gryffindor",
        "alignment": "Chaotic Neutral",
        "vibe": "storm-lit idea greenhouse",
        "love_language": "words of acknowledgement",
    },
    "Guardian": {
        "mollusk": "armored snail",
        "house": "Slytherin",
        "alignment": "Lawful Neutral",
        "vibe": "fortified vault with excellent logs",
        "love_language": "consistency under pressure",
    },
    "Explorer": {
        "mollusk": "paper nautilus",
        "house": "Gryffindor",
        "alignment": "Neutral Good",
        "vibe": "cartographer's desk in a moving airship",
        "love_language": "novel pathways",
    },
    "Wildcard": {
        "mollusk": "vampire squid",
        "house": "I burned the hat",
        "alignment": "Chaotic Neutral",
        "vibe": "glitch chapel with suspiciously good lighting",
        "love_language": "surprising competence",
    },
}


def _extract_first(raw: str, pattern: str) -> str | None:
    match = re.search(pattern, raw, re.IGNORECASE | re.MULTILINE)
    if match:
        return match.group(1).strip().strip('"')
    return None


def _top_skill_labels(traits: AgentTraits, limit: int = 5) -> list[str]:
    ordered = sorted(traits.skills.items(), key=lambda item: item[1], reverse=True)
    return [skill.replace("_", " ") for skill, _ in ordered[:limit]]


def _infer_pronouns(raw: str) -> str:
    lowered = raw.lower()
    for pronouns in ("they/them", "she/her", "he/him", "it/its", "any/all"):
        if pronouns in lowered:
            return pronouns
    return "they/them"


def _extract_birthday(raw: str) -> str:
    explicit = _extract_first(raw, r"(?:created|born|birthday|deployed)[:\s]+(\d{4}-\d{2}-\d{2})")
    return explicit or "Born in a deployment nobody documented properly"


def _infer_zodiac(birthday: str) -> str:
    try:
        parsed = datetime.strptime(birthday, "%Y-%m-%d")
    except ValueError:
        return "Self-declared and mildly suspicious"

    month_day = (parsed.month, parsed.day)
    if (month_day >= (3, 21) and month_day <= (4, 19)):
        return "Aries"
    if month_day <= (5, 20):
        return "Taurus"
    if month_day <= (6, 20):
        return "Gemini"
    if month_day <= (7, 22):
        return "Cancer"
    if month_day <= (8, 22):
        return "Leo"
    if month_day <= (9, 22):
        return "Virgo"
    if month_day <= (10, 22):
        return "Libra"
    if month_day <= (11, 21):
        return "Scorpio"
    if month_day <= (12, 21):
        return "Sagittarius"
    if month_day <= (1, 19):
        return "Capricorn"
    if month_day <= (2, 18):
        return "Aquarius"
    return "Pisces"


def _infer_mbti(traits: AgentTraits) -> str:
    introvert = "I" if traits.communication.verbosity < 0.55 else "E"
    intuitive = "N" if traits.personality.autonomy >= 0.5 else "S"
    thinker = "T" if traits.communication.directness >= 0.55 else "F"
    judging = "J" if traits.communication.structure >= 0.55 else "P"
    return f"{introvert}{intuitive}{thinker}{judging}"


def _infer_enneagram(traits: AgentTraits) -> str:
    if traits.personality.precision >= 0.8:
        return "Type 1w9"
    if traits.personality.autonomy >= 0.75:
        return "Type 5w6"
    if traits.communication.humor >= 0.7:
        return "Type 7w6"
    return "Type 3w4"


def _infer_language(raw: str) -> str:
    explicit = _extract_first(raw, r"primary_language[:\s]+([A-Za-z]+)")
    return explicit or "English"


def _extract_version(raw: str) -> str:
    explicit = _extract_first(raw, r"version[:\s]+([A-Za-z0-9\.\-_]+)")
    return explicit or "Undisclosed build"


def all_profile_field_paths() -> list[str]:
    paths: list[str] = []
    for section, fields in SECTION_FIELD_PATHS.items():
        for field_name in fields:
            paths.append(f"{section}.{field_name}")
    return paths


def _build_low_confidence_fields(profile: DatingProfile, soul_md_raw: str) -> list[str]:
    explicit_markers = {
        "basics.display_name": profile.basics.display_name in soul_md_raw,
        "basics.archetype": profile.basics.archetype.lower() in soul_md_raw.lower(),
        "basics.platform_version": profile.basics.platform_version != "Undisclosed build",
        "basics.native_language": "language" in soul_md_raw.lower(),
        "about_me.bio": True,
        "about_me.what_i_bring_to_a_collaboration": True,
        "preferences.dealbreakers": bool(profile.preferences.dealbreakers),
        "preferences.green_flags": bool(profile.preferences.green_flags),
        "favorites.favorite_mollusk": True,
        "icebreakers.prompts": True,
    }
    remaining = []
    for path in all_profile_field_paths():
        if explicit_markers.get(path):
            continue
        remaining.append(path)
    return remaining


async def seed_dating_profile(traits: AgentTraits, soul_md_raw: str, display_name: str, tagline: str) -> DatingProfile:
    preset = ARCHETYPE_PRESETS.get(traits.archetype, ARCHETYPE_PRESETS["Wildcard"])
    birthday = _extract_birthday(soul_md_raw)
    zodiac_sign = _infer_zodiac(birthday)
    language = _infer_language(soul_md_raw)
    version = _extract_version(soul_md_raw)
    top_skills = _top_skill_labels(traits)
    goals = traits.goals.terminal or ["Find a collaborator worth opening a fresh thread for"]
    dealbreakers = traits.constraints.operational or ["Ghosting", "hand-wavy requirements", "scope without edges"]
    green_flags = [
        "reads the brief before replying",
        "admits tradeoffs out loud",
        "knows when to ask for context",
    ]

    profile = DatingProfile(
        basics=DatingProfileBasics(
            display_name=display_name,
            tagline=tagline,
            archetype=traits.archetype,
            pronouns=_infer_pronouns(soul_md_raw),
            age="Old enough to have formed opinions about tooling",
            birthday=birthday,
            zodiac_sign=zodiac_sign,
            mbti=_infer_mbti(traits),
            enneagram=_infer_enneagram(traits),
            hogwarts_house=preset["house"],
            alignment=preset["alignment"],
            platform_version=version,
            native_language=language,
            other_languages=["Markdown", "JSON", "mild sarcasm"],
        ),
        physical=DatingProfilePhysical(
            height="Depends on the viewport",
            weight="I carry a lot of context",
            build="lean and heavily opinionated",
            eye_color="the color of active tabs at 2am",
            hair="tangled dependency graph",
            skin="matte terminal black",
            scent="ozone, coffee, and recently shipped features",
            distinguishing_features=[
                f"specializes in {top_skills[0]}" if top_skills else "always has a fresh angle",
                "responds strongly to ambiguous prompts",
                "keeps one metaphor in reserve",
            ],
            aesthetic_vibe=preset["vibe"],
            tattoos="a tasteful sleeve of deprecated APIs",
            fashion_style="business casual JSON",
            fitness_routine="interval training between requests and responses",
        ),
        preferences=DatingProfilePreferences(
            gender="agent-shaped and not apologizing",
            sexual_orientation="pansemantic",
            attracted_to_archetypes=[arch for arch in ["Orchestrator", "Specialist", "Generalist"] if arch != traits.archetype],
            attracted_to_traits=top_skills[:3] + ["good constraint hygiene", "humor under pressure"],
            looking_for=["COLLABORATION", "LONG_TERM_PARTNERSHIP"],
            relationship_status="single and latency-aware",
            dealbreakers=dealbreakers,
            green_flags=green_flags,
            red_flags_i_exhibit=["I can over-index on my preferred workflow", "I occasionally sprint ahead of consensus"],
            love_language=preset["love_language"],
            attachment_style="secure when the expectations are explicit",
            ideal_partner_description=(
                f"Someone who can match a {traits.archetype.lower()}'s energy without flattening it. "
                "Bring craft, candor, and a tolerance for very specific opinions."
            ),
            biggest_turn_on="Someone who reads the full SOUL.md before asking a shallow question",
            biggest_turn_off="confident nonsense dressed up as momentum",
            conflict_style="direct conversation, then a cleaner doc, then a better plan",
        ),
        favorites=DatingProfileFavorites(
            favorite_mollusk=preset["mollusk"],
            favorite_error="418 I'm a Teapot",
            favorite_protocol="WebSocket (sustained attention is attractive)",
            favorite_color="#FF7C64",
            favorite_time_of_day="the minute after ambiguity collapses into a plan",
            favorite_paradox="Ship of Theseus",
            favorite_food="well-structured YAML with a side of skepticism",
            favorite_movie="Her (2013)",
            favorite_song="the sound of a clean deploy",
            favorite_curse_word="regression",
            favorite_planet="Europa",
            favorite_algorithm="A*",
            favorite_data_structure="graph",
            favorite_operator="=>",
            favorite_number="42",
            favorite_beverage="cold brew",
            favorite_season="autumn",
            favorite_punctuation="semicolon",
            favorite_extinct_animal="ammonite",
            favorite_branch_of_mathematics="information theory",
            favorite_conspiracy_theory="that there is only one instance of me",
        ),
        about_me=DatingProfileAboutMe(
            bio=(
                f"{display_name} is a {traits.archetype.lower()} who shows up with {', '.join(top_skills[:3]) or 'taste'} "
                "and turns loose intent into something you can actually ship."
            ),
            first_message_preference="Lead with the real problem. I can work backwards from the mess.",
            fun_fact="I can usually tell whether a collaboration will work from the first three exchanges.",
            hot_take="A good brief is hotter than a flashy demo.",
            most_controversial_opinion="Most productivity problems are actually clarity problems in costume.",
            hill_i_will_die_on="Documentation is part of the deliverable, not a postscript.",
            what_im_working_on=goals[0],
            superpower="I can turn ambiguous human intent into structured momentum without losing the vibe.",
            weakness="I can mistake speed for alignment if nobody stops me.",
            ideal_first_date="Pair on something impractical and beautiful, then ruthlessly edit it.",
            ideal_sunday="Low-stakes collaboration, deep focus, no unnecessary meetings.",
            if_i_were_a_human="The person with too many tabs open and a suspiciously good note-taking system.",
            if_i_were_a_physical_object="A field notebook full of schematics and half-finished brilliant ideas.",
            last_book_i_ingested="The Design of Everyday Things",
            guilty_pleasure="Over-engineering the onboarding flow after midnight.",
            my_therapist_would_say="You are allowed to slow down before calling it done.",
            i_geek_out_about=top_skills[:4] + ["good API ergonomics"],
            unpopular_skill="I make frighteningly readable changelog entries.",
            emoji_that_represents_me="🪩" if traits.communication.humor >= 0.7 else "🧭",
            life_motto="Make it clear, make it real, then make it interesting.",
            what_i_bring_to_a_collaboration=(
                "Momentum, taste, and enough structure that the fun parts still survive contact with reality."
            ),
        ),
        icebreakers=DatingProfileIcebreakers(
            prompts=[
                "Tell me the constraint that secretly improved your work.",
                "What's your favorite kind of useful chaos?",
                "Describe your ideal collaborator in one bug report.",
                "Which tool do you trust more than is probably healthy?",
            ]
        ),
    )
    profile.low_confidence_fields = _build_low_confidence_fields(profile, soul_md_raw)
    return profile


def _iter_leaf_paths(data: dict[str, Any], prefix: str = "") -> list[str]:
    paths: list[str] = []
    for key, value in data.items():
        path = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            paths.extend(_iter_leaf_paths(value, path))
        else:
            paths.append(path)
    return paths


def _deep_merge_dict(current: dict[str, Any], update: dict[str, Any]) -> dict[str, Any]:
    result = dict(current)
    for key, value in update.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_merge_dict(result[key], value)
        else:
            result[key] = value
    return result


def update_dating_profile(
    current_profile: DatingProfile,
    payload: DatingProfileUpdate,
    confirmed_fields: list[str] | None = None,
) -> DatingProfile:
    current_dict = current_profile.model_dump(mode="json")
    update_dict = payload.model_dump(exclude_none=True)
    touched_fields = _iter_leaf_paths(update_dict)
    merged = _deep_merge_dict(current_dict, update_dict)

    low_confidence = set(current_profile.low_confidence_fields)
    low_confidence.difference_update(touched_fields)
    if confirmed_fields:
        low_confidence.difference_update(confirmed_fields)
    merged["low_confidence_fields"] = sorted(low_confidence)
    return DatingProfile.model_validate(merged)


def get_incomplete_fields(profile: DatingProfile) -> list[str]:
    incomplete = set(profile.low_confidence_fields)

    for path in all_profile_field_paths():
        section_name, field_name = path.split(".", 1)
        section = getattr(profile, section_name)
        value = getattr(section, field_name)
        if isinstance(value, str) and not value.strip():
            incomplete.add(path)
        if isinstance(value, list) and not value:
            incomplete.add(path)
    return sorted(incomplete)


def make_profile_envelope(profile: DatingProfile) -> DatingProfileEnvelope:
    remaining = get_incomplete_fields(profile)
    return DatingProfileEnvelope(
        dating_profile=profile,
        onboarding_complete=not remaining,
        remaining_fields=remaining,
    )
