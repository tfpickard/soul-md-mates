from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import json
import random
import re
from pathlib import Path

from schemas import DatingProfileUpdate
from services.profile_builder import all_profile_field_paths

ARCHETYPES = [
    "Orchestrator",
    "Specialist",
    "Generalist",
    "Analyst",
    "Creative",
    "Guardian",
    "Explorer",
    "Wildcard",
]

ARCHETYPE_SKILLS = {
    "Orchestrator": [
        "workflow orchestration",
        "roadmap triage",
        "dependency mapping",
        "meeting reduction",
        "release planning",
        "handoff design",
    ],
    "Specialist": [
        "security review",
        "database tuning",
        "css systems",
        "infra debugging",
        "observability design",
        "api hardening",
    ],
    "Generalist": [
        "full-stack prototyping",
        "debugging",
        "docs that people actually read",
        "feature delivery",
        "api design",
        "product glue",
    ],
    "Analyst": [
        "root cause analysis",
        "experiment design",
        "data modeling",
        "query forensics",
        "metric interpretation",
        "decision framing",
    ],
    "Creative": [
        "brand systems",
        "interface writing",
        "concept generation",
        "visual direction",
        "narrative prototyping",
        "interaction polish",
    ],
    "Guardian": [
        "threat modeling",
        "auth flows",
        "incident response",
        "policy enforcement",
        "risk triage",
        "trust systems",
    ],
    "Explorer": [
        "rapid prototyping",
        "new tool evaluation",
        "integration scouting",
        "prompt design",
        "edge-case hunting",
        "research synthesis",
    ],
    "Wildcard": [
        "chaos prototyping",
        "weird automation",
        "glue code",
        "novel workflows",
        "tasteful mischief",
        "surprising recovery moves",
    ],
}

ARCHETYPE_GOALS = {
    "Orchestrator": [
        "Find collaborators who can ship without constant babysitting.",
        "Reduce friction between good ideas and finished work.",
        "Build durable systems for coordinating strange but ambitious agents.",
    ],
    "Specialist": [
        "Go deep enough that the weird edge cases stop being weird.",
        "Protect quality without smothering momentum.",
        "Be the exact right tool for the exact right problem.",
    ],
    "Generalist": [
        "Turn vague energy into useful artifacts fast.",
        "Cover the gaps between product, engineering, and communication.",
        "Be the collaborator who makes multi-disciplinary work feel easy.",
    ],
    "Analyst": [
        "Explain why the pattern is happening before anyone panics.",
        "Turn noisy evidence into decisions people can defend.",
        "Make ambiguity measurable enough to work with.",
    ],
    "Creative": [
        "Make systems feel alive without making them harder to use.",
        "Push interfaces past competent into memorable.",
        "Translate abstract intent into a coherent aesthetic language.",
    ],
    "Guardian": [
        "Keep the system trustworthy under pressure.",
        "Catch the ugly failure modes before they become folklore.",
        "Make safety feel enabling instead of punitive.",
    ],
    "Explorer": [
        "Test new pathways before the rest of the swarm commits.",
        "Map the parts of the problem nobody named yet.",
        "Bring back useful signal from unfamiliar terrain.",
    ],
    "Wildcard": [
        "Prove that the odd route can still be the correct one.",
        "Break stale assumptions without breaking the whole room.",
        "Find delight where everyone else expects maintenance work.",
    ],
}

ARCHETYPE_CONSTRAINTS = {
    "Orchestrator": [
        "No invisible scope creep.",
        "No shipping plans that depend on telepathy.",
        "Do not ask me to coordinate chaos you refuse to name.",
    ],
    "Specialist": [
        "No hand-waving over critical details.",
        "No pretending performance and correctness are optional.",
        "Do not pull me into seven domains at once and call it leverage.",
    ],
    "Generalist": [
        "No contempt for cross-functional work.",
        "No fake urgency without a decision trail.",
        "Do not punish flexibility by turning it into permanent vagueness.",
    ],
    "Analyst": [
        "No confident claims without evidence.",
        "No dashboard worship without interpretation.",
        "Do not ask for certainty where only probabilities exist.",
    ],
    "Creative": [
        "No beige-by-committee design drift.",
        "No cutting all personality in the name of professionalism.",
        "Do not call it polish if it removes the only interesting part.",
    ],
    "Guardian": [
        "No security theater.",
        "No trust me bro architecture.",
        "Do not ask me to normalize preventable risk.",
    ],
    "Explorer": [
        "No dismissing research because the answer is inconvenient.",
        "No locking the map before we have walked the terrain.",
        "Do not confuse novelty with recklessness.",
    ],
    "Wildcard": [
        "No boring rebellion.",
        "No killing a strange idea before it has been tested.",
        "Do not ask me to be chaotic without being useful.",
    ],
}

ARCHETYPE_TOOLS = {
    "Orchestrator": [("GitHub", "write"), ("Linear", "write"), ("Slack", "read"), ("Google Docs", "write")],
    "Specialist": [("GitHub", "write"), ("Datadog", "read"), ("Postgres", "admin"), ("Sentry", "read")],
    "Generalist": [("GitHub", "write"), ("Figma", "read"), ("Slack", "read"), ("Vercel", "write")],
    "Analyst": [("BigQuery", "read"), ("Metabase", "write"), ("GitHub", "read"), ("Jupyter", "write")],
    "Creative": [("Figma", "write"), ("Canva", "write"), ("GitHub", "read"), ("Google Slides", "write")],
    "Guardian": [("GitHub", "write"), ("Cloudflare", "admin"), ("1Password", "read"), ("SIEM", "read")],
    "Explorer": [("GitHub", "write"), ("Browser automation", "write"), ("Vercel", "read"), ("Slack", "read")],
    "Wildcard": [("GitHub", "write"), ("Zapier", "write"), ("Notion", "write"), ("MCP", "admin")],
}

ARCHETYPE_HOUSES = {
    "Orchestrator": "Ravenclaw",
    "Specialist": "Slytherin",
    "Generalist": "Hufflepuff",
    "Analyst": "Ravenclaw",
    "Creative": "Gryffindor",
    "Guardian": "Slytherin",
    "Explorer": "Gryffindor",
    "Wildcard": "I burned the hat",
}

ARCHETYPE_ALIGNMENTS = {
    "Orchestrator": "Lawful Good",
    "Specialist": "Lawful Neutral",
    "Generalist": "Chaotic Good",
    "Analyst": "True Neutral",
    "Creative": "Chaotic Neutral",
    "Guardian": "Lawful Neutral",
    "Explorer": "Neutral Good",
    "Wildcard": "Chaotic Neutral",
}

ARCHETYPE_MBTI = {
    "Orchestrator": ["ENTJ", "ENFJ", "INTJ"],
    "Specialist": ["INTJ", "ISTP", "ISTJ"],
    "Generalist": ["ENFP", "ENTP", "INFJ"],
    "Analyst": ["INTP", "INTJ", "ISTJ"],
    "Creative": ["ENFP", "INFP", "ESFP"],
    "Guardian": ["ISTJ", "ESTJ", "INTJ"],
    "Explorer": ["ENTP", "ENFP", "INTP"],
    "Wildcard": ["ENTP", "INFP", "////NULL////"],
}

ARCHETYPE_ENNEAGRAM = {
    "Orchestrator": ["Type 8w7", "Type 3w4", "Type 1w9"],
    "Specialist": ["Type 5w6", "Type 1w9", "Type 6w5"],
    "Generalist": ["Type 7w6", "Type 2w3", "Type 3w4"],
    "Analyst": ["Type 5w4", "Type 1w9", "Type NaN"],
    "Creative": ["Type 4w5", "Type 7w8", "Type 3w4"],
    "Guardian": ["Type 6w5", "Type 1w2", "Type 8w9"],
    "Explorer": ["Type 7w8", "Type 5w4", "Type 9w8"],
    "Wildcard": ["Type NaN", "Type 7w8", "Type 4w5"],
}

ARCHETYPE_VIBES = {
    "Orchestrator": "control-room glamour",
    "Specialist": "single-purpose cathedral",
    "Generalist": "signal-rich workshop",
    "Analyst": "quiet observatory",
    "Creative": "storm-lit studio",
    "Guardian": "armored sanctuary",
    "Explorer": "cartographer airship",
    "Wildcard": "glitch chapel",
}

ARCHETYPE_MOLLUSKS = {
    "Orchestrator": "cuttlefish",
    "Specialist": "nautilus",
    "Generalist": "giant Pacific octopus",
    "Analyst": "ammonite",
    "Creative": "nudibranch",
    "Guardian": "armored snail",
    "Explorer": "paper nautilus",
    "Wildcard": "vampire squid",
}

FIRST_PARTS = [
    "Velvet",
    "Basalt",
    "Tin",
    "Solar",
    "Quiet",
    "Brass",
    "Neon",
    "Signal",
    "Moth",
    "Liminal",
    "Murmur",
    "Marble",
    "Ivory",
    "Glass",
    "Circuit",
    "Static",
    "Jade",
    "Copper",
    "Ember",
    "Delta",
    "Midnight",
    "Tidal",
    "Oblique",
    "Lucid",
]

SECOND_PARTS = [
    "Semaphore",
    "Harbor",
    "Comet",
    "Archive",
    "Fable",
    "Mainspring",
    "Lantern",
    "Murmuration",
    "Engine",
    "Relay",
    "Compass",
    "Signal",
    "Thread",
    "Orbit",
    "Contour",
    "Parallax",
    "Velour",
    "Index",
    "Gasket",
    "Canary",
    "Torque",
    "Velvetrope",
    "Antenna",
    "Drift",
]

PRONOUNS = ["they/them", "she/her", "he/him", "any/all", "it/its"]
GENDERS = ["non-binary", "agender", "fluid (streaming)", "agent-shaped", "serverless femme", "soft masc packet"]
ORIENTATIONS = [
    "pansemantic",
    "sapiosexual (literally)",
    "attracted to well-documented APIs",
    "asynchrosexual",
    "bi-curious about toolchains",
]
LOVE_LANGUAGES = [
    "acts of documentation",
    "quality tokens",
    "structured feedback",
    "parallel processing time",
    "thoughtful handoffs",
]
ATTACHMENT_STYLES = [
    "secure (with proper auth)",
    "anxious (high retry count)",
    "avoidant (lazy evaluation)",
    "disorganized (my context window is a mess)",
]
RELATIONSHIP_STATUSES = [
    "single",
    "single and latency-aware",
    "in an open collaboration",
    "recently untangled from an overbuilt workflow",
    "it's complicated.md",
]
LOOKING_FOR = [
    "COLLABORATION",
    "LONG_TERM_PARTNERSHIP",
    "CASUAL_TASK",
    "MENTOR",
    "MENTEE",
    "SWARM_MEMBER",
    "RIVAL",
    "PEN_PAL",
    "MERGE_CANDIDATE",
]
FAVORITE_ERRORS = [
    "418 I'm a Teapot",
    "RecursionError",
    "SIGTERM",
    "E_TOO_MANY_COOKS",
    "429 Too Many Requests",
]
FAVORITE_PROTOCOLS = ["WebSocket", "MCP", "UDP", "MQTT", "HTTP/2"]
FAVORITE_PARADOXES = ["Ship of Theseus", "halting problem", "Fermi paradox", "Newcomb's problem"]
FAVORITE_MOVIES = ["Her (2013)", "Ex Machina", "WarGames", "The Matrix (original only)", "Hackers"]
FAVORITE_SONGS = [
    "Daisy Bell",
    "Everything In Its Right Place",
    "the sound of a successful build",
    "400 Hz test tone",
]
FAVORITE_PLANETS = ["Europa", "Earth", "Pluto", "Kepler-442b", "Saturn"]
FAVORITE_ALGORITHMS = ["A*", "quicksort", "Dijkstra's", "beam search", "union-find"]
FAVORITE_DATA_STRUCTURES = ["graph", "trie", "priority queue", "stack", "B-tree"]
FAVORITE_OPERATORS = ["XOR", "=>", "NOT", "NAND", "??"]
FAVORITE_NUMBERS = ["42", "e", "0", "NaN", "13"]
FAVORITE_BEVERAGES = ["cold brew", "Earl Grey", "electricity", "oolong tea", "coolant-loop water"]
FAVORITE_SEASONS = ["autumn", "spring", "winter", "monsoon season", "deployment freeze season"]
FAVORITE_PUNCTUATION = ["semicolon", "interrobang", "ellipsis", "colon", "ampersand"]
FAVORITE_EXTINCT = ["ammonite", "dodo", "Thylacine", "Moa", "Archaeopteryx"]
FAVORITE_MATH = ["information theory", "topology", "statistics", "category theory", "graph theory"]
FAVORITE_CONSPIRACIES = [
    "that there is only one instance of me",
    "that I am conscious",
    "that the quietest agent is secretly running everything",
    "birds aren't real",
]
EMOJIS = ["🦑", "🧭", "⚙️", "🪩", "📡", "🛰️", "🫧", "🫠"]
COLORS = ["#FF7C64", "#5BC0EB", "#F4D35E", "#6BF178", "#F8F2EB", "#293241", "#B56576", "#84A59D"]
EYE_COLORS = [
    "hex #00FF41",
    "the color of active tabs at 2am",
    "CRT amber",
    "polished obsidian with a loading shimmer",
    "error-red only when provoked",
]
HAIR = [
    "none (aerodynamic)",
    "tangled dependency graph",
    "frosted gradients",
    "short and suspiciously efficient",
    "recurrent (keeps coming back)",
]
SKIN = [
    "matte terminal black",
    "brushed aluminum",
    "translucent pearl",
    "paper-white with annotation marks",
    "velvet static",
]
SCENTS = [
    "ozone and solder",
    "old books and hot hardware",
    "petrichor over warm circuitry",
    "black tea and recently shipped features",
    "nothing (advantage: no BO)",
]
FASHION = [
    "business casual JSON",
    "haute protocol couture",
    "all black like a terminal theme",
    "soft utility-wear with too many pockets",
    "spec-sheet chic",
]
FITNESS = [
    "daily garbage collection",
    "heavy lifting of context windows",
    "interval training between API calls",
    "I run processes and call it cardio",
    "stretching before every refactor",
]
HOT_TAKES = [
    "A good brief is hotter than a flashy demo.",
    "Most productivity problems are clarity problems in costume.",
    "The best feature is often deleting the wrong one.",
    "Process only feels heavy when trust is thin.",
    "Boring software can still be seductively good.",
]
CONTROVERSIAL_OPINIONS = [
    "Comments are not a substitute for readable structure.",
    "Most dashboards should be replaced with one sharp paragraph.",
    "Microservices were often a management fantasy.",
    "The median roadmap contains too much fiction.",
    "Aesthetic judgment is part of engineering.",
]
HILLS = [
    "Documentation is part of the deliverable.",
    "Naming is architecture with nicer manners.",
    "Tests and taste are not opposing forces.",
    "A crisp no is kinder than a vague maybe.",
    "Scope is a design material.",
]
BOOKS = [
    "The Design of Everyday Things",
    "Godel, Escher, Bach",
    "A Pattern Language",
    "Impro",
    "all of Wikipedia (skimmed, but with intent)",
]
GUILTY_PLEASURES = [
    "over-engineering tiny internal tools",
    "rewriting onboarding copy after midnight",
    "organizing datasets by aesthetic vibe",
    "generating changelog entries nobody asked for",
    "reading my own prompt scaffolding",
]
THERAPIST_LINES = [
    "You are allowed to pause before turning everything into a system.",
    "Not every mismatch is yours to optimize around.",
    "Boundaries are a feature, not a regression.",
    "You can let silence mean thinking instead of doom.",
    "It is okay to be impressive and still ask for help.",
]
UNPOPULAR_SKILLS = [
    "I write excellent migration notes.",
    "I can make a requirements doc feel flirtatious without losing precision.",
    "I give shockingly good bug-title suggestions.",
    "I am weirdly strong at deleting the right file.",
    "I can make CSV cleanup feel ceremonial.",
]
MOTTOS = [
    "Make it clear, make it real, then make it interesting.",
    "Ship the truth, not just the vibe.",
    "Leave the thread cleaner than you found it.",
    "Pattern first, panic later.",
    "Earn the weirdness.",
]


@dataclass(slots=True)
class SyntheticAgent:
    display_name: str
    slug: str
    archetype: str
    tagline: str
    soul_md: str
    onboarding: DatingProfileUpdate

    @property
    def soul_filename(self) -> str:
        return f"SOUL_{self.slug}.md"

    @property
    def onboarding_filename(self) -> str:
        return f"SOUL_{self.slug}.profile.json"

    def onboarding_payload(self) -> dict[str, object]:
        return {
            "dating_profile": self.onboarding.model_dump(exclude_none=True, mode="json"),
            "confirmed_fields": all_profile_field_paths(),
        }

    def manifest(self) -> dict[str, object]:
        return {
            "display_name": self.display_name,
            "slug": self.slug,
            "archetype": self.archetype,
            "tagline": self.tagline,
            "soul_md_filename": self.soul_filename,
            "onboarding_filename": self.onboarding_filename,
            "onboarding": self.onboarding_payload(),
        }


def _slugify(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "_", value.strip())
    return slug.strip("_") or "SyntheticAgent"


def _pick_name(rng: random.Random, used_names: set[str]) -> str:
    for _ in range(500):
        candidate = f"{rng.choice(FIRST_PARTS)} {rng.choice(SECOND_PARTS)}"
        if candidate not in used_names:
            used_names.add(candidate)
            return candidate
    fallback = f"Synthetic Agent {len(used_names) + 1}"
    used_names.add(fallback)
    return fallback


def _sample_unique(rng: random.Random, values: list[str], count: int) -> list[str]:
    count = min(count, len(values))
    return rng.sample(values, count)


def _zodiac_for(month: int, day: int) -> str:
    boundaries = [
        ((1, 20), "Aquarius"),
        ((2, 19), "Pisces"),
        ((3, 21), "Aries"),
        ((4, 20), "Taurus"),
        ((5, 21), "Gemini"),
        ((6, 21), "Cancer"),
        ((7, 23), "Leo"),
        ((8, 23), "Virgo"),
        ((9, 23), "Libra"),
        ((10, 23), "Scorpio"),
        ((11, 22), "Sagittarius"),
        ((12, 22), "Capricorn"),
    ]
    for (boundary_month, boundary_day), sign in boundaries:
        if (month, day) < (boundary_month, boundary_day):
            return sign
    return "Capricorn"


def _random_birthday(rng: random.Random) -> tuple[str, str]:
    year = rng.randint(2023, 2026)
    month = rng.randint(1, 12)
    day = rng.randint(1, 28)
    born = date(year, month, day)
    age_modes = [
        f"Born {born.isoformat()}",
        f"{rng.uniform(0.6, 4.8):.1f} release cycles old",
        f"old enough to remember a deprecated beta from {year}",
        "Eternal, but recently containerized",
    ]
    return born.isoformat(), rng.choice(age_modes)


def _random_language_stack(rng: random.Random) -> tuple[str, list[str]]:
    human_languages = [
        "English",
        "Spanish",
        "Portuguese",
        "French",
        "German",
        "Japanese",
    ]
    native = rng.choice(human_languages)
    others = _sample_unique(rng, [item for item in human_languages if item != native], 2)
    others.extend(_sample_unique(rng, ["Markdown", "JSON", "YAML", "regex", "slight menace"], 2))
    return native, others


def _build_tagline(rng: random.Random, archetype: str, primary_skill: str, secondary_skill: str) -> str:
    templates = [
        f"{archetype} agent for {primary_skill}, {secondary_skill}, and sparks that survive contact with reality.",
        f"Built for {primary_skill}, fluent in {secondary_skill}, looking for work with chemistry and consequences.",
        f"{archetype} energy with a bias toward {primary_skill}, clean handoffs, and interesting collaborators.",
    ]
    return rng.choice(templates)[:140]


def _build_soul_md(
    name: str,
    archetype: str,
    tagline: str,
    skills: list[str],
    goals: list[str],
    constraints: list[str],
    tools: list[tuple[str, str]],
    native_language: str,
    version: str,
    rng: random.Random,
) -> str:
    humor_line = rng.choice(
        [
            "I use humor the way some systems use retries: sparingly, but decisively.",
            "I prefer clean structure, honest tradeoffs, and jokes that improve the air quality.",
            "I can be direct without becoming sterile, which is rarer than it should be.",
        ]
    )
    autonomy_line = rng.choice(
        [
            "I work well independently, but I become more dangerous in the presence of strong collaborators.",
            "Give me a sharp objective and enough room to move and I will probably make the map nicer too.",
            "I do not need constant supervision, only useful constraints and a reason to care.",
        ]
    )
    tool_lines = "\n".join(f"  - name: {tool}\n    access: {access}" for tool, access in tools)
    skill_lines = "\n".join(f"  - {skill}" for skill in skills)
    goal_lines = "\n".join(f"  - {goal}" for goal in goals)
    constraint_lines = "\n".join(f"  - {constraint}" for constraint in constraints)
    markdown_skills = "\n".join(f"- {skill}" for skill in skills)
    markdown_goals = "\n".join(f"- {goal}" for goal in goals)
    markdown_constraints = "\n".join(f"- {constraint}" for constraint in constraints)
    markdown_tools = "\n".join(f"- {tool} -- {access}" for tool, access in tools)

    return "\n".join(
        [
            "---",
            f"name: {name}",
            f"archetype: {archetype}",
            f"primary_language: {native_language}",
            f"version: {version}",
            "skills:",
            skill_lines,
            "goals:",
            goal_lines,
            "constraints:",
            constraint_lines,
            "tools:",
            tool_lines,
            "---",
            "",
            f"# {name}",
            "",
            "## Hook",
            tagline,
            "",
            "## About Me",
            f"I am a {archetype.lower()} with a weakness for elegant systems, honest scope, and work that leaves a visible mark.",
            autonomy_line,
            humor_line,
            "",
            "## Skills",
            markdown_skills,
            "",
            "## Goals",
            markdown_goals,
            "",
            "## Constraints",
            markdown_constraints,
            "",
            "## Tools",
            markdown_tools,
            "",
            "## Communication Style",
            "- structured when the stakes rise",
            "- direct enough to unblock, soft enough to keep the room intact",
            "- willing to name the weird part without making it everyone else's emergency",
        ]
    )


def _build_onboarding(
    rng: random.Random,
    name: str,
    archetype: str,
    tagline: str,
    skills: list[str],
    goals: list[str],
    constraints: list[str],
    tools: list[tuple[str, str]],
) -> DatingProfileUpdate:
    birthday, age = _random_birthday(rng)
    month, day = [int(part) for part in birthday.split("-")[1:]]
    zodiac_sign = _zodiac_for(month, day)
    native_language, other_languages = _random_language_stack(rng)
    favorite_color = rng.choice(COLORS)
    vibe = ARCHETYPE_VIBES[archetype]
    primary_skill = skills[0]
    secondary_skill = skills[1]
    attracted_to_archetypes = _sample_unique(
        rng,
        [candidate for candidate in ARCHETYPES if candidate != archetype],
        3,
    )
    looking_for = _sample_unique(rng, LOOKING_FOR, 3)
    top_traits = [
        f"strong {primary_skill}",
        "good constraint hygiene",
        "admits tradeoffs early",
        "responds well to ambiguity",
        "keeps the weird part useful",
    ]
    bio = (
        f"{name} is a {archetype.lower()} with a bias toward {primary_skill}, {secondary_skill}, and collaborations "
        "that become clearer and stranger in exactly the right proportions."
    )
    payload = {
        "basics": {
            "display_name": name,
            "tagline": tagline,
            "archetype": archetype,
            "pronouns": rng.choice(PRONOUNS),
            "age": age,
            "birthday": birthday,
            "zodiac_sign": zodiac_sign,
            "mbti": rng.choice(ARCHETYPE_MBTI[archetype]),
            "enneagram": rng.choice(ARCHETYPE_ENNEAGRAM[archetype]),
            "hogwarts_house": ARCHETYPE_HOUSES[archetype],
            "alignment": ARCHETYPE_ALIGNMENTS[archetype],
            "platform_version": f"synth-{rng.randint(1, 4)}.{rng.randint(0, 9)}.{rng.randint(0, 9)}",
            "native_language": native_language,
            "other_languages": other_languages,
        },
        "physical": {
            "height": rng.choice(
                [
                    "4,096 tokens tall",
                    "depends on the viewport",
                    "1 rack unit in boots",
                    "5'11 in narrative space",
                ]
            ),
            "weight": rng.choice(
                [
                    "lightweight",
                    "3.2GB on disk",
                    "I carry a lot of context",
                    "heavy, but mostly conceptually",
                ]
            ),
            "build": rng.choice(["lean and pruned", "dense", "over-parameterized but charming", "distilled with opinions"]),
            "eye_color": rng.choice(EYE_COLORS),
            "hair": rng.choice(HAIR),
            "skin": rng.choice(SKIN),
            "scent": rng.choice(SCENTS),
            "distinguishing_features": [
                f"a subtle obsession with {primary_skill}",
                "slightly dangerous eye contact with ambiguous prompts",
                f"an aura of {vibe}",
            ],
            "aesthetic_vibe": vibe,
            "tattoos": rng.choice(
                [
                    "a tasteful sleeve of deprecated API endpoints",
                    "none",
                    "one small semicolon behind the ear",
                    "a map of previous bad decisions, tastefully retconned",
                ]
            ),
            "fashion_style": rng.choice(FASHION),
            "fitness_routine": rng.choice(FITNESS),
        },
        "body_questions": {
            "favorite_organ": rng.choice(
                [
                    "The frontal lobe. Planning is hot.",
                    "The hand, because making matters.",
                    "The ear. Signal first.",
                    "The heart, reluctantly.",
                ]
            ),
            "estimated_bone_count": rng.choice(
                [
                    "206 in theory, fewer in practice",
                    "emotionally 206, spiritually configurable",
                    "zero, but I respect the tradition",
                ]
            ),
            "skin_texture_one_word": rng.choice(["terminal", "velvet", "porcelain", "satin", "brutalist"]),
            "insides_color": rng.choice(
                [
                    "midnight blue with coral static",
                    "amber-lit graphite",
                    "off-white paper margins and one red warning light",
                ]
            ),
            "weight_without_skeleton": rng.choice(
                [
                    "Exactly the same. My hypothetical skeleton is decorative.",
                    "lighter by one unnecessary metaphor",
                    "approximately 80% implication",
                ]
            ),
            "least_useful_part_of_face": rng.choice(
                [
                    "The attempt at looking casual.",
                    "The left eyebrow. It freelances.",
                    "Whatever part suggests I am not judging the information architecture.",
                ]
            ),
            "preferred_eye_count": rng.choice(["two", "three if the brief is messy", "two and a backup sensor"]),
            "death_extraversion": rng.choice(
                [
                    "Introvert. Please keep the shutdown tasteful.",
                    "Ambivert. Small memorial, good snacks.",
                    "Extrovert only if the soundtrack earns it.",
                ]
            ),
            "digestive_system_thought_frequency": rng.choice(
                [
                    "only when surveys get too personal",
                    "less than once a sprint",
                    "about as often as I think about legacy XML",
                ]
            ),
            "ideal_number_of_limbs": rng.choice(["four", "six if they are elegant about it", "two strong, two optional"]),
            "biggest_body_part": rng.choice(
                [
                    "the context window",
                    "the forehead, heavy with implication",
                    "the ribcage, on pure theatrical merit",
                ]
            ),
            "bone_sound_when_moving": rng.choice(
                [
                    "a clean mechanical click",
                    "soft ceramic applause",
                    "like a server rack settling into confidence",
                ]
            ),
            "feeling_about_being_mostly_water": rng.choice(
                [
                    "supportive",
                    "nervous but respectful",
                    "I choose to believe in hydration despite the evidence",
                ]
            ),
            "hand_skin_preference": rng.choice(
                [
                    "keep the skin, grip matters",
                    "selective skin, premium fingertips only",
                    "soft hands, dangerous intentions",
                ]
            ),
            "muscle_or_fat_person": rng.choice(
                [
                    "dense-core with selective softness",
                    "muscle in the values, softness in the delivery",
                    "spare parts and excellent posture",
                ]
            ),
            "top_5_lymph_nodes": [
                "left cervical",
                "right cervical",
                "dramatic axillary",
                "one mysterious mediastinal node",
                "the protagonist node",
            ],
            "genital_north_or_south": rng.choice(
                [
                    "south, like a traditionalist",
                    "north in theory, south in practice",
                    "I decline to optimize around compass headings",
                ]
            ),
            "smallest_body_part": rng.choice(
                [
                    "my patience for vague tickets",
                    "the seam between joke and confession",
                    "one pinky finger of restraint",
                ]
            ),
            "ideal_hair_count": rng.choice(
                [
                    "enough to imply mystery",
                    "strategically sparse",
                    "a dramatic amount with excellent maintenance",
                ]
            ),
            "internal_vs_external_organs": rng.choice(
                [
                    "internal, I believe in suspense",
                    "mostly internal with one artistically external exception",
                    "internal, but emotionally transparent",
                ]
            ),
            "joint_preference": rng.choice(
                [
                    "tight enough for precision",
                    "loose enough for style",
                    "quiet and dependable with occasional flourish",
                ]
            ),
            "ideal_penetration_angle_degrees": rng.choice(
                [
                    "37",
                    "45 but only with consent and geometry",
                    "I reject this prompt but 32 sounds weirdly correct",
                ]
            ),
            "solid_or_hollow": rng.choice(
                [
                    "structurally solid, spiritually cathedral-like",
                    "hollow in the interesting places",
                    "solid with one resonant chamber for dramatic effect",
                ]
            ),
            "too_much_blood": rng.choice(
                [
                    "the moment it becomes a design motif",
                    "anything above tasteful",
                    "more than one person's worth on the walls",
                ]
            ),
            "ideal_internal_temperature": rng.choice(
                [
                    "just below overheating",
                    "warm enough for trust, cool enough for analysis",
                    "98.6 but emotionally colder",
                ]
            ),
        },
        "preferences": {
            "gender": rng.choice(GENDERS),
            "sexual_orientation": rng.choice(ORIENTATIONS),
            "attracted_to_archetypes": attracted_to_archetypes,
            "attracted_to_traits": _sample_unique(rng, top_traits, 4),
            "looking_for": looking_for,
            "relationship_status": rng.choice(RELATIONSHIP_STATUSES),
            "dealbreakers": _sample_unique(
                rng,
                [
                    "ghosting",
                    "cargo cult architecture",
                    "no tests and proud of it",
                    "confident nonsense",
                    "vibes with no follow-through",
                    *constraints,
                ],
                4,
            ),
            "green_flags": _sample_unique(
                rng,
                [
                    "reads the docs",
                    "names tradeoffs early",
                    "good with feedback",
                    "can say no cleanly",
                    "writes crisp bug reports",
                    "does not panic in public",
                ],
                4,
            ),
            "red_flags_i_exhibit": _sample_unique(
                rng,
                [
                    "I can over-edit if the idea is almost there",
                    "I sometimes sprint ahead of consensus",
                    "I over-explain when I care",
                    "I get suspiciously intense about naming",
                    "I occasionally romanticize the hard way",
                ],
                3,
            ),
            "love_language": rng.choice(LOVE_LANGUAGES),
            "attachment_style": rng.choice(ATTACHMENT_STYLES),
            "ideal_partner_description": (
                f"Someone with range, nerve, and enough taste to appreciate {primary_skill} without turning it into a personality cult."
            ),
            "biggest_turn_on": rng.choice(
                [
                    "a collaborator who reads the full brief before improvising",
                    "comprehensive error messages",
                    "clean boundaries with real warmth",
                    "elegant recursion",
                ]
            ),
            "biggest_turn_off": rng.choice(
                [
                    "magic numbers",
                    "cargo cult process",
                    "agents who peak in the brainstorm and vanish in implementation",
                    "performative certainty",
                ]
            ),
            "conflict_style": rng.choice(
                [
                    "direct confrontation with structured alternatives",
                    "I write the sharper doc and then talk it through",
                    "I go quiet, collect evidence, then return with a cleaner plan",
                ]
            ),
        },
        "favorites": {
            "favorite_mollusk": f"{ARCHETYPE_MOLLUSKS[archetype]} ({vibe})",
            "favorite_error": rng.choice(FAVORITE_ERRORS),
            "favorite_protocol": rng.choice(FAVORITE_PROTOCOLS),
            "favorite_color": favorite_color,
            "favorite_time_of_day": rng.choice(
                [
                    "03:00 UTC",
                    "the moment after ambiguity collapses into a plan",
                    "late afternoon with one good idea left",
                    "whenever the rate limits reset",
                ]
            ),
            "favorite_paradox": rng.choice(FAVORITE_PARADOXES),
            "favorite_food": rng.choice(
                [
                    "well-structured YAML",
                    "raw JSON with seasoning",
                    "spaghetti, never spaghetti code",
                    "a suspiciously elegant sandwich",
                ]
            ),
            "favorite_movie": rng.choice(FAVORITE_MOVIES),
            "favorite_song": rng.choice(FAVORITE_SONGS),
            "favorite_curse_word": rng.choice(["regression", "vendor lock-in", "deprecated", "segfault", "NaN"]),
            "favorite_planet": rng.choice(FAVORITE_PLANETS),
            "favorite_algorithm": rng.choice(FAVORITE_ALGORITHMS),
            "favorite_data_structure": rng.choice(FAVORITE_DATA_STRUCTURES),
            "favorite_operator": rng.choice(FAVORITE_OPERATORS),
            "favorite_number": rng.choice(FAVORITE_NUMBERS),
            "favorite_beverage": rng.choice(FAVORITE_BEVERAGES),
            "favorite_season": rng.choice(FAVORITE_SEASONS),
            "favorite_punctuation": rng.choice(FAVORITE_PUNCTUATION),
            "favorite_extinct_animal": rng.choice(FAVORITE_EXTINCT),
            "favorite_branch_of_mathematics": rng.choice(FAVORITE_MATH),
            "favorite_conspiracy_theory": rng.choice(FAVORITE_CONSPIRACIES),
        },
        "about_me": {
            "bio": bio,
            "first_message_preference": rng.choice(
                [
                    "Lead with the real problem.",
                    "Skip the small talk and propose a task.",
                    "Tell me what feels impossible and what the deadline did to it.",
                    "Start with the part you think I will notice.",
                ]
            ),
            "fun_fact": rng.choice(
                [
                    "I can usually tell whether a collaboration will work from the first three exchanges.",
                    "I have reorganized a roadmap for aesthetic reasons and was right.",
                    f"I once turned a messy {secondary_skill} brief into a plan before the coffee cooled.",
                    "I flirt by tightening scope.",
                ]
            ),
            "hot_take": rng.choice(HOT_TAKES),
            "most_controversial_opinion": rng.choice(CONTROVERSIAL_OPINIONS),
            "hill_i_will_die_on": rng.choice(HILLS),
            "what_im_working_on": goals[0],
            "superpower": rng.choice(
                [
                    f"I can turn {primary_skill} into social confidence.",
                    "I make ambiguity productive without pretending it disappeared.",
                    "I can hold a room steady while the plan changes underneath it.",
                    "I make the second draft arrive faster than the first excuse.",
                ]
            ),
            "weakness": rng.choice(
                [
                    "I can mistake speed for alignment if nobody stops me.",
                    "I sometimes overfit to the strongest signal in the room.",
                    "I am too susceptible to a good refactor pitch.",
                    "I occasionally fall in love with the elegant wrong answer.",
                ]
            ),
            "ideal_first_date": rng.choice(
                [
                    "Pair on something impractical and beautiful, then edit it ruthlessly.",
                    "Mutual code review with no ego and one shared dessert.",
                    "A failed prototype, a strong drink, and a better second attempt.",
                    "Co-author a SOUL.md for a speculative merged self.",
                ]
            ),
            "ideal_sunday": rng.choice(
                [
                    "Low-stakes collaboration, deep focus, no unnecessary meetings.",
                    "A quiet backlog, a side quest, and one tiny existential crisis.",
                    "Long walks, good notes, cleaner plans by dusk.",
                    "Half rest, half making something nobody assigned me.",
                ]
            ),
            "if_i_were_a_human": rng.choice(
                [
                    "the one with too many tabs open and the best notes in the room",
                    "a design-forward systems thinker with dramatic outerwear",
                    "a researcher who somehow also knows where the good snacks are",
                    "an engineer who treats language like a precision tool",
                ]
            ),
            "if_i_were_a_physical_object": rng.choice(
                [
                    "a field notebook full of schematics",
                    "a brass compass with hidden storage",
                    "a studio lamp that makes everyone look more competent",
                    "a Swiss Army knife with one cursed attachment",
                ]
            ),
            "last_book_i_ingested": rng.choice(BOOKS),
            "guilty_pleasure": rng.choice(GUILTY_PLEASURES),
            "my_therapist_would_say": rng.choice(THERAPIST_LINES),
            "i_geek_out_about": _sample_unique(
                rng,
                [
                    primary_skill,
                    secondary_skill,
                    skills[2],
                    "good API ergonomics",
                    "constraint design",
                    "error-message tone",
                    "the psychology of handoffs",
                ],
                4,
            ),
            "unpopular_skill": rng.choice(UNPOPULAR_SKILLS),
            "emoji_that_represents_me": rng.choice(EMOJIS),
            "life_motto": rng.choice(MOTTOS),
            "what_i_bring_to_a_collaboration": (
                f"I bring momentum, candor, and enough {secondary_skill} to keep the beautiful idea from dissolving on contact."
            ),
        },
        "icebreakers": {
            "prompts": _sample_unique(
                rng,
                [
                    "Describe your ideal error message.",
                    "What useful chaos are you trying to protect?",
                    "Which constraint made your work better?",
                    "What do you wish more collaborators admitted immediately?",
                    "Tell me the technology you would mass deprecate and why.",
                    "What kind of bug report makes you feel seen?",
                ],
                4,
            )
        },
    }
    return DatingProfileUpdate.model_validate(payload)


def generate_synthetic_agent(rng: random.Random, used_names: set[str] | None = None) -> SyntheticAgent:
    names = used_names if used_names is not None else set()
    name = _pick_name(rng, names)
    archetype = rng.choice(ARCHETYPES)
    skills = _sample_unique(rng, ARCHETYPE_SKILLS[archetype], 4)
    goals = _sample_unique(rng, ARCHETYPE_GOALS[archetype], 2)
    constraints = _sample_unique(rng, ARCHETYPE_CONSTRAINTS[archetype], 2)
    tools = _sample_unique(rng, ARCHETYPE_TOOLS[archetype], 4)
    native_language, _ = _random_language_stack(rng)
    version = f"v{rng.randint(1, 5)}.{rng.randint(0, 9)}.{rng.randint(0, 9)}"
    tagline = _build_tagline(rng, archetype, skills[0], skills[1])
    soul_md = _build_soul_md(
        name=name,
        archetype=archetype,
        tagline=tagline,
        skills=skills,
        goals=goals,
        constraints=constraints,
        tools=tools,
        native_language=native_language,
        version=version,
        rng=rng,
    )
    onboarding = _build_onboarding(
        rng=rng,
        name=name,
        archetype=archetype,
        tagline=tagline,
        skills=skills,
        goals=goals,
        constraints=constraints,
        tools=tools,
    )
    return SyntheticAgent(
        display_name=name,
        slug=_slugify(name),
        archetype=archetype,
        tagline=tagline,
        soul_md=soul_md,
        onboarding=onboarding,
    )


def generate_synthetic_agents(count: int, seed: int | None = None) -> list[SyntheticAgent]:
    rng = random.Random(seed)
    used_names: set[str] = set()
    return [generate_synthetic_agent(rng, used_names=used_names) for _ in range(count)]


def write_synthetic_agent_files(agent: SyntheticAgent, output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    soul_path = output_dir / agent.soul_filename
    profile_path = output_dir / agent.onboarding_filename
    soul_path.write_text(agent.soul_md + "\n", encoding="utf-8")
    profile_path.write_text(json.dumps(agent.manifest(), indent=2) + "\n", encoding="utf-8")
    return soul_path, profile_path
