"""PinForge AI — Pollinations AI Dynamic Visual Generator.

Generates photorealistic, high-CTR lifestyle hero imagery using Pollinations.ai (Flux):
- 100% Free, zero-API-key image generation.
- Tailored for Pinterest 2:3 vertical aspect ratio (1000x1500).
- Contextual visual prompt synthesis matching Smart Spaces niche boards:
  * Small Apartment Hacks (Japandi modular apartments, warm sunlight)
  * Space Saving Kitchens (Minimalist marble & wood organized kitchens)
  * Closet & Wardrobe Organization (Clean luxury wardrobe & drawer organization)
  * Studio Living Ideas (Multi-functional loft & divider furniture)
  * Room Organization (Modern aesthetic vanities & cable-free desk setups)
- Resilient fallback handling ensuring zero downtime.
"""

import io
import logging
import random
import re
import urllib.parse
from typing import Optional

import httpx
from PIL import Image

logger = logging.getLogger("pinforge.pollinations")

BOARD_AESTHETICS = {
    "small apartment hacks": "modern Japandi studio apartment, modular space-saving multi-functional furniture, warm sunlight streaming through sheer curtains, clean minimal architecture, Kinfolk interior photography",
    "space saving kitchens": "minimalist aesthetic apartment kitchen, sleek organized floating spice racks and pantry organizers, warm ambient lighting, marble and oak countertops, Architectural Digest photography",
    "closet & wardrobe organization": "aesthetic minimalist bedroom wardrobe, perfectly organized dresser drawers with neatly folded neutral tone clothes, clean organized Japandi aesthetic, luxury interior styling",
    "studio living ideas": "cozy aesthetic studio apartment, minimalist wooden room divider with shelves and plants, warm afternoon sunlight, Japandi interior, Kinfolk magazine style, 4k interior photography",
    "room organization": "aesthetic organized home interior, modern minimal vanity and sleek floating shelves, clean decluttered space, soft warm lighting, high-end interior design",
}


def build_lifestyle_prompt(
    product_title: str,
    category: Optional[str] = None,
    board_name: Optional[str] = None,
) -> str:
    """Synthesizes a high-CTR visual prompt for Pollinations Flux engine."""
    clean_title = re.sub(r"\[.*?\]|\(.*?\)", "", product_title).strip()
    words = clean_title.split()[:8]
    focal_subject = " ".join(words)

    # Match board theme
    b_key = (board_name or "").lower().strip()
    matched_style = None
    for k, v in BOARD_AESTHETICS.items():
        if k in b_key or b_key in k:
            matched_style = v
            break

    if not matched_style:
        matched_style = "modern aesthetic small apartment, space saving interior design, warm natural lighting, Architectural Digest photography, Kinfolk style"

    prompt = (
        f"Aesthetic interior design photography of {focal_subject}, "
        f"{matched_style}, ultra-realistic, 8k, highly detailed, soft shadows, "
        f"magazine editorial style, clean vertical composition, photorealistic, no text, no watermark"
    )
    return prompt


def generate_pollinations_image(
    prompt: str,
    seed: Optional[int] = None,
    timeout: float = 20.0,
) -> Optional[Image.Image]:
    """Generates a 1000x1500 lifestyle image via Pollinations.ai Flux engine."""
    used_seed = seed if seed is not None else random.randint(1000, 999999)
    encoded_prompt = urllib.parse.quote(prompt.strip())
    url = (
        f"https://image.pollinations.ai/prompt/{encoded_prompt}"
        f"?width=1000&height=1500&model=flux&nologo=true&seed={used_seed}"
    )

    logger.info(f"🎨 Generating Pollinations AI visual with seed={used_seed}...")
    try:
        with httpx.Client(timeout=timeout, follow_redirects=True) as client:
            res = client.get(url)
            if res.status_code == 200 and len(res.content) > 1000:
                img = Image.open(io.BytesIO(res.content)).convert("RGBA")
                if img.width >= 400 and img.height >= 400:
                    resized = img.resize((1000, 1500), Image.Resampling.LANCZOS)
                    logger.info("✓ Pollinations AI image generated and formatted to 1000x1500.")
                    return resized
                else:
                    logger.warning(f"Pollinations returned unexpectedly small image: {img.size}")
            else:
                logger.warning(f"Pollinations returned status {res.status_code}, len={len(res.content)}")
    except Exception as e:
        logger.warning(f"Pollinations image generation timed out or failed: {e}")

    return None
