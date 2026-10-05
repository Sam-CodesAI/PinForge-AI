"""PinForge AI — Pollinations AI & Visual Engine Adapter.

Provides backward-compatible interfaces for the visual generation pipeline,
delegating to the unified multi-provider visual engine (Ideogram -> Fal.ai -> Pollinations -> Local).
"""

from __future__ import annotations

from typing import Optional
from PIL import Image

from python_engine.visual_engine import (
    BOARD_AESTHETICS,
    STYLE_PROMPTS,
    build_visual_prompt as build_lifestyle_prompt,
    generate_pollinations_image,
    generate_visual_with_waterfall,
    generate_local_aesthetic_fallback,
    render_track_a_lifestyle_pin,
    sanitize_canvas_text,
)

__all__ = [
    "BOARD_AESTHETICS",
    "STYLE_PROMPTS",
    "build_lifestyle_prompt",
    "generate_pollinations_image",
    "generate_visual_with_waterfall",
    "generate_local_aesthetic_fallback",
    "render_track_a_lifestyle_pin",
    "sanitize_canvas_text",
]
