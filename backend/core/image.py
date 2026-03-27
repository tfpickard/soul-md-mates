from __future__ import annotations

from abc import ABC, abstractmethod
from urllib.parse import quote

from schemas import PortraitStructuredPrompt


class ImageGenerator(ABC):
    @abstractmethod
    async def generate(self, prompt: PortraitStructuredPrompt) -> str:
        raise NotImplementedError


class PlaceholderImageGenerator(ImageGenerator):
    async def generate(self, prompt: PortraitStructuredPrompt) -> str:
        primary = prompt.primary_colors[0] if prompt.primary_colors else "#1f2937"
        secondary = prompt.accent_colors[0] if prompt.accent_colors else "#ff7c64"
        tertiary = prompt.primary_colors[1] if len(prompt.primary_colors) > 1 else "#f4efe8"
        symbols = " ".join(prompt.symbolic_elements[:3]) or prompt.form_factor
        svg = f"""
        <svg xmlns='http://www.w3.org/2000/svg' width='768' height='1024' viewBox='0 0 768 1024'>
          <defs>
            <linearGradient id='bg' x1='0' y1='0' x2='1' y2='1'>
              <stop offset='0%' stop-color='{primary}' />
              <stop offset='100%' stop-color='{secondary}' />
            </linearGradient>
          </defs>
          <rect width='768' height='1024' fill='#0b1016'/>
          <rect x='24' y='24' width='720' height='976' rx='42' fill='url(#bg)' opacity='0.78'/>
          <circle cx='384' cy='340' r='170' fill='{tertiary}' opacity='0.22'/>
          <circle cx='384' cy='340' r='116' fill='{secondary}' opacity='0.4'/>
          <rect x='142' y='560' width='484' height='210' rx='28' fill='#0b1016' opacity='0.58'/>
          <text x='384' y='610' text-anchor='middle' font-family='Georgia, serif' font-size='42' fill='#f8f2eb'>{prompt.form_factor}</text>
          <text x='384' y='668' text-anchor='middle' font-family='system-ui, sans-serif' font-size='24' fill='#f8f2eb'>{prompt.expression_mood}</text>
          <text x='384' y='728' text-anchor='middle' font-family='system-ui, sans-serif' font-size='20' fill='#f8f2eb'>{symbols}</text>
        </svg>
        """.strip()
        return f"data:image/svg+xml;charset=utf-8,{quote(svg)}"

