from __future__ import annotations

import re

from core.image import PlaceholderImageGenerator
from schemas import PortraitStructuredPrompt

GENERATOR = PlaceholderImageGenerator()

COLOR_PATTERN = re.compile(r"#(?:[0-9a-fA-F]{3}){1,2}")


def _find_colors(description: str) -> list[str]:
    colors = COLOR_PATTERN.findall(description)
    if colors:
        return colors[:4]
    lowered = description.lower()
    named = []
    for name, hex_value in [
        ("coral", "#ff7c64"),
        ("amber", "#f59e0b"),
        ("blue", "#4f7cff"),
        ("green", "#10b981"),
        ("silver", "#cbd5e1"),
        ("black", "#0b1016"),
        ("white", "#f8f2eb"),
    ]:
        if name in lowered:
            named.append(hex_value)
    return named[:4] or ["#ff7c64", "#0b1016", "#f8f2eb"]


async def extract_portrait_prompt(description: str) -> PortraitStructuredPrompt:
    colors = _find_colors(description)
    lowered = description.lower()
    mood = "playful" if any(token in lowered for token in ("playful", "joy", "bright")) else "contemplative"
    if any(token in lowered for token in ("chaos", "storm", "wild", "feral")):
        mood = "chaotic"
    if any(token in lowered for token in ("guardian", "armor", "fortress", "security")):
        mood = "defiant"

    if any(token in lowered for token in ("creature", "monster", "animal", "octopus")):
        form_factor = "creature"
    elif any(token in lowered for token in ("tower", "architecture", "cathedral", "fortress")):
        form_factor = "impossible architecture"
    elif any(token in lowered for token in ("portrait", "face", "humanoid", "person")):
        form_factor = "humanoid silhouette"
    else:
        form_factor = "abstract signal entity"

    symbols = []
    for token in ("compass", "cables", "crown", "shell", "terminal", "storm", "glass", "mollusk"):
        if token in lowered:
            symbols.append(token)
    if not symbols:
        symbols = ["signal flare", "constellation map", "echoing shell"]

    return PortraitStructuredPrompt(
        form_factor=form_factor,
        primary_colors=colors[:2],
        accent_colors=colors[2:4] or ["#f8f2eb"],
        texture_material="glossy code-forged glass" if "glass" in lowered else "layered digital matter",
        expression_mood=mood,
        environment="storm-lit datascape" if "storm" in lowered else "midnight gradient void",
        lighting="bioluminescent rim light",
        symbolic_elements=symbols,
        art_style="cinematic digital illustration",
        camera_angle="three-quarter portrait",
        composition_notes="Center the subject and leave strong negative space for profile overlays.",
    )


async def generate_portrait(prompt: PortraitStructuredPrompt) -> str:
    return await GENERATOR.generate(prompt)

