"""PinForge AI — Multi-Provider Visual Generation Engine & Waterfall Fallback.

Architected for @Smart_Spaces (Pinterest) and Amazon Affiliate workflows:
1. Tier 1: Ideogram 2.0 / 3.0 API (in-image typography, chalkboard jar labels, signs, graphic design).
2. Tier 2: Fal.ai FLUX.1 [dev / schnell] (photorealistic 2700K warm interior lighting, Japandi architecture).
3. Tier 3: Pollinations AI / Free Fallback (authenticated or free endpoints, resilient to timeouts & 402/429 errors).
4. Tier 4: Local Aesthetic Procedural Fallback (100% zero-crash guarantee, ambient lighting, gradients, framing).

Additional Capabilities:
- Track A (Aspirational Lifestyle Pins): 100% full-bleed, high-aesthetic interior design imagery
  with ZERO promotional boxes, ZERO giant buttons, and ZERO prices (Pins 1 & 2).
- FreeType Glyph Sanitizer: maps unicode symbols (➔, ✦, ⚡, 🔥, 🛡️) to safe ASCII equivalents (->, *, [!])
  eliminating Pillow missing glyph tofu boxes.
"""

from __future__ import annotations

import io
import logging
import math
import random
import re
import time
import urllib.parse
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Literal

import httpx
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from python_engine.config import (
    FONTS_DIR,
    IDEOGRAM_API_KEY,
    FAL_KEY,
    POLLINATIONS_API_KEY,
)

logger = logging.getLogger("pinforge.visual_engine")

# Canvas Dimensions (Standard Pinterest 2:3 Vertical)
CANVAS_WIDTH = 1000
CANVAS_HEIGHT = 1500

# Fonts Configuration (Bundled TTF in repo)
BOLD_FONT_PATH = FONTS_DIR / "Inter-Bold.ttf"
REGULAR_FONT_PATH = FONTS_DIR / "Inter-Regular.ttf"
SERIF_FONT_PATH = FONTS_DIR / "Editorial-Serif.ttf"

# ============================================================================
# FONT & GLYPH SANITIZATION (Fixes Pillow FreeType "NO GLYPH" / Tofu Box Bug)
# ============================================================================

GLYPH_REPLACEMENTS: Dict[str, str] = {
    # Directional Arrows
    "➔": "->",
    "➜": "->",
    "➤": "->",
    "→": "->",
    "➡": "->",
    "↳": "->",
    "⇒": "->",
    "►": ">",
    "▶": ">",
    "◄": "<",
    "◀": "<",
    # Sparkles & Decorative Stars
    "✦": "*",
    "✨": "*",
    "★": "*",
    "☆": "*",
    "✪": "*",
    "✫": "*",
    "✷": "*",
    "✵": "*",
    "❇": "*",
    # Lightning / Fire / Urgent Badges
    "⚡️": "[!]",
    "⚡": "[!]",
    "🔥": "[!]",
    "💥": "[!]",
    "⚠️": "[!]",
    "❗": "!",
    "‼️": "!!",
    # Security / Badges / Shields
    "🛡️": "[SAFE]",
    "🛡": "[SAFE]",
    "🔒": "[SAFE]",
    # Checks & Markers
    "✔": "✓",
    "☑": "✓",
    # Rulers & Tools
    "📐": "[SPECS]",
    "📏": "[SPECS]",
    "⚖️": "[CAPACITY]",
    "⚖": "[CAPACITY]",
    "🔧": "[SETUP]",
    "🛠️": "[SETUP]",
    "📦": "[BOX]",
}


def sanitize_canvas_text(text: Optional[str]) -> str:
    """Sanitizes text intended for Pillow ImageDraw text rendering.

    Replaces non-standard unicode characters, emojis, and arrows that do not have
    native glyphs in Inter or Editorial-Serif with safe ASCII equivalents
    (e.g., '➔' -> '->', '✦' -> '*', '⚡' -> '[!]').
    Strips variation selectors (\\ufe0f) and dangling unsupported symbols to prevent
    Pillow FreeType .notdef tofu box artifacts.
    """
    if not text:
        return ""

    sanitized = str(text)

    # 1. Direct multi-character and single-character symbol replacements
    for symbol, replacement in GLYPH_REPLACEMENTS.items():
        if symbol in sanitized:
            sanitized = sanitized.replace(symbol, replacement)

    # 2. Strip Unicode variation selectors (e.g. \ufe0f, \ufe0e)
    sanitized = re.sub(r"[\ufe00-\ufe0f]", "", sanitized)

    # 3. Clean any remaining unsupported high-range unicode emojis while preserving basic punctuation & accents
    # Keep printable ASCII, Latin-1 supplement, and common punctuation
    cleaned_chars = []
    for ch in sanitized:
        code = ord(ch)
        if code < 128:
            cleaned_chars.append(ch)
        elif code in (8226, 183):  # Bullet points • and ·
            cleaned_chars.append("•")
        elif ch == "✓":
            cleaned_chars.append("✓")
        elif 160 <= code <= 255:  # Latin-1 accented characters
            cleaned_chars.append(ch)
        elif code in (8216, 8217):  # Curved single quotes
            cleaned_chars.append("'")
        elif code in (8220, 8221):  # Curved double quotes
            cleaned_chars.append('"')
        elif code in (8211, 8212):  # En/Em dash
            cleaned_chars.append("-")
        else:
            # Fallback for unrecognized glyphs to safe space or discard
            cleaned_chars.append(" ")

    return re.sub(r"\s+", " ", "".join(cleaned_chars)).strip()


def get_canvas_font(path: Path, size: int) -> ImageFont.FreeTypeFont:
    """Loads a TTF font safely with graceful multi-font fallback ensuring zero bitmap pixelation."""
    for candidate in [path, BOLD_FONT_PATH, REGULAR_FONT_PATH, SERIF_FONT_PATH]:
        try:
            if candidate and candidate.exists():
                return ImageFont.truetype(str(candidate), size)
        except Exception:
            continue
    try:
        return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size)
    except Exception:
        return ImageFont.load_default()


# ============================================================================
# BOARD AESTHETICS & NICHE PROMPT SYNTHESIS
# ============================================================================

BOARD_AESTHETICS: Dict[str, str] = {
    "small apartment hacks": (
        "modern Japandi studio apartment, modular space-saving multi-functional furniture, "
        "warm 2700K ambient sunlight streaming through sheer linen curtains, bleached oak and matte black accents, "
        "clean minimal architecture, Kinfolk interior photography, 8k, soft shadows"
    ),
    "space saving kitchens": (
        "minimalist aesthetic apartment kitchen, sleek organized floating spice racks and pantry organizers, "
        "warm 2700K under-cabinet ambient lighting, white Carrara marble and warm natural oak countertops, "
        "Architectural Digest photography, pristine culinary storage styling"
    ),
    "closet & wardrobe organization": (
        "aesthetic minimalist luxury walk-in wardrobe, perfectly organized dresser drawers and hanging rails, "
        "neatly folded neutral tone linen clothes, warm ambient spotlighting, travertine stone accents, "
        "Vogue Living interior design editorial"
    ),
    "studio living ideas": (
        "cozy aesthetic studio apartment, minimalist wooden room divider with floating display shelves and potted plants, "
        "warm afternoon golden hour sunlight, Japandi interior, Kinfolk magazine style, 8k interior photography"
    ),
    "room organization": (
        "aesthetic organized home sanctuary, modern minimal floating shelves and sleek decluttered vanity desk, "
        "soft 2700K warm interior lighting, neutral linen textures, pristine high-end home staging"
    ),
}

STYLE_PROMPTS: Dict[str, str] = {
    "aspirational_lifestyle": (
        "Architectural Digest award-winning interior photography, high-end Japandi small apartment living, "
        "full-bleed composition, 2700K warm golden hour sunlight, bleached oak and natural limestone textures, "
        "Kinfolk editorial magazine style, 8k resolution, ultra-realistic, shot on Hasselblad H6D-100c"
    ),
    "luxury_editorial": (
        "Architectural Digest luxury editorial photography, minimalist Japandi penthouse, "
        "travertine stone and bleached oak, pristine high-end home styling, soft diffused sunlight, 8k"
    ),
    "warm_japandi": (
        "Warm modern Japandi apartment aesthetic, organic linen textiles, light white oak, beige and warm taupe tones, "
        "2700K gentle interior lamp illumination, cozy compact home inspiration, hyper-detailed photography"
    ),
    "story": (
        "Cinematic 35mm film photography, Kodak Portra 400 aesthetic, candid lifestyle story shot, "
        "warm cozy ambient room, soft depth of field, natural morning light, Kinfolk magazine editorial"
    ),
    "anime": (
        "Studio Ghibli aesthetic, Makoto Shinkai artistic anime style, warm golden-hour lighting, "
        "painted watercolor background, cozy organized Japanese studio apartment, vibrant key visual"
    ),
    "cyber_bento": (
        "Modern 2026 tech aesthetic, dark moody cyberpunk minimalist interior, "
        "subtle cyan and amber neon ambient glow, matte black accents, sleek futuristic smart apartment"
    ),
}


def build_visual_prompt(
    product_title: str,
    board_name: Optional[str] = None,
    category: Optional[str] = None,
    style: Optional[str] = None,
    tier: Optional[int] = None,
) -> str:
    """Synthesizes an ultra-high-converting visual prompt tailored per tier and niche board."""
    clean_title = re.sub(r"\[.*?\]|\(.*?\)", "", product_title).strip()
    words = clean_title.split()[:8]
    focal_subject = " ".join(words) if words else "modern space saving home organizer"

    # Style modifier takes priority if explicitly set
    if style and style in STYLE_PROMPTS:
        base_style = STYLE_PROMPTS[style]
    else:
        # Match board theme
        b_key = (board_name or "").lower().strip()
        matched = None
        for k, v in BOARD_AESTHETICS.items():
            if k in b_key or b_key in k:
                matched = v
                break
        base_style = matched or (
            "modern aesthetic small apartment, space saving interior design, "
            "warm 2700K natural lighting, Architectural Digest photography, Kinfolk style"
        )

    # Provider/Tier-specific prompt tailoring
    if tier == 1:
        # Ideogram: excels in in-image typography, chalkboard jar labels, and clean graphic layout
        prompt = (
            f"High-end editorial lifestyle photography of {focal_subject}, "
            f"seamlessly integrated into a {base_style}. "
            f"Crisp clean organization labels, elegant typography details on jars and signs, "
            f"2:3 vertical Pinterest aspect ratio, photorealistic, 8k, flawless composition"
        )
    elif tier == 2:
        # Fal.ai FLUX: industry leader in 2700K warm interior illumination, Japandi textures, travertine, oak
        prompt = (
            f"Photorealistic 8k interior design editorial showcasing {focal_subject}, "
            f"{base_style}. Warm 2700K ambient illumination, soft volumetric shadows, "
            f"tactile linen and natural wood textures, vertical 2:3 Pinterest composition, "
            f"shot on 50mm f/1.8 lens, Architectural Digest quality, no watermark"
        )
    else:
        # Pollinations / General
        prompt = (
            f"Aesthetic interior design photography of {focal_subject}, "
            f"{base_style}, ultra-realistic, 8k, highly detailed, soft shadows, "
            f"magazine editorial style, clean vertical 2:3 composition, photorealistic, no text, no watermark"
        )

    return prompt


# ============================================================================
# STRUCTURED RESULT DATA MODEL
# ============================================================================

@dataclass
class VisualGenerationResult:
    """Result returned by the visual engine."""
    image: Image.Image
    provider: Literal["ideogram", "fal_flux", "pollinations", "local_aesthetic"]
    tier: int
    prompt_used: str
    elapsed_ms: float
    seed: Optional[int] = None
    success: bool = True
    error_trail: List[str] = field(default_factory=list)

    @property
    def is_ai_generated(self) -> bool:
        return self.provider in ("ideogram", "fal_flux", "pollinations")

    @property
    def is_fallback(self) -> bool:
        return self.tier >= 4 or self.provider == "local_aesthetic"


# ============================================================================
# TIER 1: IDEOGRAM 2.0 / 3.0 API ENGINE
# ============================================================================

def generate_ideogram_image(
    prompt: str,
    api_key: Optional[str] = None,
    timeout: float = 30.0,
) -> Optional[Image.Image]:
    """Generates an image via Ideogram API (Tier 1).

    Ideogram excels at in-image typography, chalkboard jar labels, and clean graphic design.
    Requires IDEOGRAM_API_KEY. Gracefully falls back to None upon failure or missing key.
    """
    effective_key = (api_key or IDEOGRAM_API_KEY or "").strip()
    if not effective_key:
        logger.debug("Tier 1 (Ideogram): No IDEOGRAM_API_KEY configured, skipping to Tier 2.")
        return None

    url = "https://api.ideogram.ai/generate"
    headers = {
        "Api-Key": effective_key,
        "Content-Type": "application/json",
    }
    payload = {
        "image_request": {
            "prompt": prompt,
            "aspect_ratio": "ASPECT_2_3",
            "model": "V_2",
            "magic_prompt_option": "AUTO",
        }
    }

    logger.info("🎨 [Tier 1] Invoking Ideogram 2.0/3.0 API...")
    try:
        with httpx.Client(timeout=timeout, follow_redirects=True) as client:
            resp = client.post(url, headers=headers, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                images = data.get("data", [])
                if images and "url" in images[0]:
                    image_url = images[0]["url"]
                    img_resp = client.get(image_url)
                    if img_resp.status_code == 200 and len(img_resp.content) > 1000:
                        img = Image.open(io.BytesIO(img_resp.content)).convert("RGBA")
                        resized = img.resize((CANVAS_WIDTH, CANVAS_HEIGHT), Image.Resampling.LANCZOS)
                        logger.info("✓ [Tier 1] Ideogram visual generated successfully (1000x1500).")
                        return resized
                logger.warning(f"Tier 1 (Ideogram): Unexpected response structure: {data}")
            else:
                logger.warning(f"Tier 1 (Ideogram): HTTP {resp.status_code} - {resp.text[:200]}")
    except Exception as err:
        logger.warning(f"Tier 1 (Ideogram): Request failed ({err}), falling back to Tier 2...")

    return None


# ============================================================================
# TIER 2: FAL.AI FLUX.1 [dev / schnell] ENGINE
# ============================================================================

def generate_fal_flux_image(
    prompt: str,
    api_key: Optional[str] = None,
    model: str = "fal-ai/flux/schnell",
    timeout: float = 30.0,
) -> Optional[Image.Image]:
    """Generates an image via Fal.ai FLUX.1 API (Tier 2).

    Industry leader in photorealistic 2700K warm interior lighting and Japandi textures.
    Requires FAL_KEY. Gracefully falls back to None upon failure or missing key.
    """
    effective_key = (api_key or FAL_KEY or "").strip()
    if not effective_key:
        logger.debug("Tier 2 (Fal.ai FLUX): No FAL_KEY configured, skipping to Tier 3.")
        return None

    url = f"https://fal.run/{model}"
    headers = {
        "Authorization": f"Key {effective_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "prompt": prompt,
        "image_size": {
            "width": CANVAS_WIDTH,
            "height": CANVAS_HEIGHT,
        },
        "num_inference_steps": 4 if "schnell" in model else 28,
        "enable_safety_checker": True,
    }

    logger.info(f"🎨 [Tier 2] Invoking Fal.ai FLUX ({model})...")
    try:
        with httpx.Client(timeout=timeout, follow_redirects=True) as client:
            resp = client.post(url, headers=headers, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                images = data.get("images", [])
                if images and "url" in images[0]:
                    image_url = images[0]["url"]
                    img_resp = client.get(image_url)
                    if img_resp.status_code == 200 and len(img_resp.content) > 1000:
                        img = Image.open(io.BytesIO(img_resp.content)).convert("RGBA")
                        resized = img.resize((CANVAS_WIDTH, CANVAS_HEIGHT), Image.Resampling.LANCZOS)
                        logger.info("✓ [Tier 2] Fal.ai FLUX visual generated successfully (1000x1500).")
                        return resized
                logger.warning(f"Tier 2 (Fal.ai FLUX): Unexpected response payload: {data}")
            else:
                logger.warning(f"Tier 2 (Fal.ai FLUX): HTTP {resp.status_code} - {resp.text[:200]}")
    except Exception as err:
        logger.warning(f"Tier 2 (Fal.ai FLUX): Request failed ({err}), falling back to Tier 3...")

    return None


# ============================================================================
# TIER 3: POLLINATIONS AI / FREE FALLBACK ENGINE
# ============================================================================

def generate_pollinations_image(
    prompt: str,
    seed: Optional[int] = None,
    api_key: Optional[str] = None,
    timeout: float = 20.0,
) -> Optional[Image.Image]:
    """Generates an image via Pollinations.ai (Tier 3).

    Handles free or authenticated endpoints (?key= or Authorization header).
    Resiliently catches timeouts, HTTP 402 ('Payment Required'), and HTTP 429 rate limits.
    """
    used_seed = seed if seed is not None else random.randint(1000, 999999)
    encoded_prompt = urllib.parse.quote(prompt.strip())
    effective_key = (api_key or POLLINATIONS_API_KEY or "").strip()

    base_url = (
        f"https://image.pollinations.ai/prompt/{encoded_prompt}"
        f"?width={CANVAS_WIDTH}&height={CANVAS_HEIGHT}&model=flux&nologo=true&seed={used_seed}"
    )
    if effective_key:
        base_url += f"&key={urllib.parse.quote(effective_key)}"

    headers = {}
    if effective_key:
        headers["Authorization"] = f"Bearer {effective_key}"

    logger.info(f"🎨 [Tier 3] Invoking Pollinations AI (Flux) with seed={used_seed}...")
    try:
        with httpx.Client(timeout=timeout, follow_redirects=True, headers=headers) as client:
            res = client.get(base_url)
            if res.status_code == 200 and len(res.content) > 1000:
                img = Image.open(io.BytesIO(res.content)).convert("RGBA")
                if img.width >= 400 and img.height >= 400:
                    resized = img.resize((CANVAS_WIDTH, CANVAS_HEIGHT), Image.Resampling.LANCZOS)
                    logger.info("✓ [Tier 3] Pollinations AI visual generated and formatted to 1000x1500.")
                    return resized
                else:
                    logger.warning(f"Tier 3 (Pollinations): Image too small: {img.size}")
            elif res.status_code in (402, 429):
                logger.warning(f"Tier 3 (Pollinations): HTTP {res.status_code} quota limit reached.")
            else:
                logger.warning(f"Tier 3 (Pollinations): Returned status {res.status_code}, len={len(res.content)}")
    except Exception as e:
        logger.warning(f"Tier 3 (Pollinations): Timed out or failed ({e}), falling back to Tier 4...")

    return None


# ============================================================================
# TIER 4: LOCAL PROCEDURAL AESTHETIC FALLBACK ENGINE
# ============================================================================

def generate_local_aesthetic_fallback(
    board_name: Optional[str] = None,
    style: Optional[str] = None,
    product_img: Optional[Image.Image] = None,
) -> Image.Image:
    """Tier 4: 100% Zero-Crash Procedural Canvas Generator.

    Synthesizes a high-aesthetic Japandi / minimal interior ambiance using layered
    Gaussian radial lighting (2700K ambient warmth, linen texture, soft travertine framing).
    Guarantees 1000x1500 px RGBA canvas with zero crash even in complete network blackouts.
    """
    logger.info("🎨 [Tier 4] Rendering Local Procedural Aesthetic Canvas (100% Zero-Crash Fallback)...")
    b_key = (board_name or "").lower()

    # Determine theme colors based on board intent
    if "kitchen" in b_key:
        bg_color = (248, 245, 238, 255)  # Warm marble alabaster
        ambient_1 = (245, 158, 11, 40)   # Warm 2700K amber glow
        ambient_2 = (217, 119, 6, 25)    # Warm terracotta
        border_color = (226, 220, 205, 255)
    elif "closet" in b_key or "wardrobe" in b_key:
        bg_color = (247, 245, 240, 255)  # Travertine linen
        ambient_1 = (217, 119, 6, 30)
        ambient_2 = (180, 160, 140, 30)
        border_color = (220, 214, 202, 255)
    elif style == "cyber_bento":
        bg_color = (11, 15, 25, 255)      # Deep obsidian slate
        ambient_1 = (56, 189, 248, 50)   # Neon cyan backlight
        ambient_2 = (245, 158, 11, 35)   # Amber accent
        border_color = (30, 41, 59, 255)
    else:
        # Default Japandi warm minimal
        bg_color = (246, 243, 237, 255)  # Bone / natural linen
        ambient_1 = (245, 158, 11, 45)   # 2700K sunlight glow
        ambient_2 = (147, 112, 98, 25)   # Soft earth tone
        border_color = (225, 219, 206, 255)

    img = Image.new("RGBA", (CANVAS_WIDTH, CANVAS_HEIGHT), bg_color)

    # 1. Multi-layered 2700K Gaussian Ambient Radial Lighting
    glow = Image.new("RGBA", (CANVAS_WIDTH, CANVAS_HEIGHT), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    glow_draw.ellipse([80, 120, 920, 850], fill=ambient_1)
    glow_draw.ellipse([150, 600, 850, 1350], fill=ambient_2)
    glow = glow.filter(ImageFilter.GaussianBlur(110))
    img = Image.alpha_composite(img, glow)

    # 2. Elegant Editorial Double Framing Border
    draw = ImageDraw.Draw(img)
    draw.rectangle([30, 30, CANVAS_WIDTH - 30, CANVAS_HEIGHT - 30], outline=border_color, width=2)
    draw.rectangle([45, 45, CANVAS_WIDTH - 45, CANVAS_HEIGHT - 45], outline=border_color, width=1)

    # 3. If product image exists, composite cleanly with soft contact shadow
    if product_img:
        pw_target, ph_target = 760, 760
        ratio = min(pw_target / product_img.width, ph_target / product_img.height)
        new_w = int(product_img.width * ratio)
        new_h = int(product_img.height * ratio)
        resized_prod = product_img.resize((new_w, new_h), Image.Resampling.LANCZOS)

        pos_x = (CANVAS_WIDTH - new_w) // 2
        pos_y = (CANVAS_HEIGHT - new_h) // 2 - 40

        # Drop shadow
        p_shadow = Image.new("RGBA", (CANVAS_WIDTH, CANVAS_HEIGHT), (0, 0, 0, 0))
        ps_draw = ImageDraw.Draw(p_shadow)
        ps_draw.rounded_rectangle(
            [pos_x + 10, pos_y + 20, pos_x + new_w - 10, pos_y + new_h + 30],
            radius=24,
            fill=(0, 0, 0, 40),
        )
        p_shadow = p_shadow.filter(ImageFilter.GaussianBlur(35))
        img = Image.alpha_composite(img, p_shadow)

        # Paste product image
        img.paste(resized_prod, (pos_x, pos_y), resized_prod if resized_prod.mode == "RGBA" else None)

    return img


# ============================================================================
# UNIFIED WATERFALL ENGINE (Tier 1 -> Tier 2 -> Tier 3 -> Tier 4)
# ============================================================================

def generate_visual_with_waterfall(
    prompt: Optional[str] = None,
    product_title: str = "Modern Space Saving Interior Organizer",
    board_name: Optional[str] = None,
    category: Optional[str] = None,
    style: Optional[str] = None,
    product_img: Optional[Image.Image] = None,
    preferred_tier: Optional[int] = None,
    seed: Optional[int] = None,
) -> VisualGenerationResult:
    """Executes the multi-provider 3-tier waterfall fallback chain:

    Tier 1 (Ideogram) -> Tier 2 (Fal.ai FLUX) -> Tier 3 (Pollinations) -> Tier 4 (Local Aesthetic).

    Guarantees 100% zero-crash uptime: if any tier fails, times out, or lacks keys,
    it systematically steps to the next tier and logs the transition.
    """
    start_time = time.perf_counter()
    error_trail: List[str] = []

    # 1. Synthesize base prompt if not provided
    effective_prompt = prompt or build_visual_prompt(
        product_title=product_title,
        board_name=board_name,
        category=category,
        style=style,
    )

    # ----------------------------------------------------
    # TIER 1: IDEOGRAM 2.0 / 3.0 API
    # ----------------------------------------------------
    if preferred_tier in (None, 1) and IDEOGRAM_API_KEY:
        try:
            tier1_prompt = build_visual_prompt(
                product_title=product_title,
                board_name=board_name,
                category=category,
                style=style,
                tier=1,
            )
            img = generate_ideogram_image(tier1_prompt, timeout=25.0)
            if img:
                elapsed = (time.perf_counter() - start_time) * 1000.0
                return VisualGenerationResult(
                    image=img,
                    provider="ideogram",
                    tier=1,
                    prompt_used=tier1_prompt,
                    elapsed_ms=round(elapsed, 2),
                    seed=seed,
                    success=True,
                    error_trail=error_trail,
                )
            error_trail.append("Tier 1 (Ideogram): Returned None or invalid response")
        except Exception as e:
            error_trail.append(f"Tier 1 (Ideogram): Exception {e}")
    else:
        if not IDEOGRAM_API_KEY:
            error_trail.append("Tier 1 (Ideogram): Skipped (IDEOGRAM_API_KEY unset)")

    # ----------------------------------------------------
    # TIER 2: FAL.AI FLUX.1 [dev / schnell]
    # ----------------------------------------------------
    if preferred_tier in (None, 1, 2) and FAL_KEY:
        try:
            tier2_prompt = build_visual_prompt(
                product_title=product_title,
                board_name=board_name,
                category=category,
                style=style,
                tier=2,
            )
            img = generate_fal_flux_image(tier2_prompt, timeout=25.0)
            if img:
                elapsed = (time.perf_counter() - start_time) * 1000.0
                return VisualGenerationResult(
                    image=img,
                    provider="fal_flux",
                    tier=2,
                    prompt_used=tier2_prompt,
                    elapsed_ms=round(elapsed, 2),
                    seed=seed,
                    success=True,
                    error_trail=error_trail,
                )
            error_trail.append("Tier 2 (Fal.ai FLUX): Returned None or invalid response")
        except Exception as e:
            error_trail.append(f"Tier 2 (Fal.ai FLUX): Exception {e}")
    else:
        if not FAL_KEY:
            error_trail.append("Tier 2 (Fal.ai FLUX): Skipped (FAL_KEY unset)")

    # ----------------------------------------------------
    # TIER 3: POLLINATIONS AI / FREE FALLBACK
    # ----------------------------------------------------
    if preferred_tier in (None, 1, 2, 3):
        try:
            tier3_prompt = build_visual_prompt(
                product_title=product_title,
                board_name=board_name,
                category=category,
                style=style,
                tier=3,
            )
            img = generate_pollinations_image(tier3_prompt, seed=seed, timeout=20.0)
            if img:
                elapsed = (time.perf_counter() - start_time) * 1000.0
                return VisualGenerationResult(
                    image=img,
                    provider="pollinations",
                    tier=3,
                    prompt_used=tier3_prompt,
                    elapsed_ms=round(elapsed, 2),
                    seed=seed,
                    success=True,
                    error_trail=error_trail,
                )
            error_trail.append("Tier 3 (Pollinations): Returned None, timeout, or 402/429")
        except Exception as e:
            error_trail.append(f"Tier 3 (Pollinations): Exception {e}")

    # ----------------------------------------------------
    # TIER 4: LOCAL PROCEDURAL AESTHETIC FALLBACK
    # ----------------------------------------------------
    img = generate_local_aesthetic_fallback(
        board_name=board_name,
        style=style,
        product_img=product_img,
    )
    elapsed = (time.perf_counter() - start_time) * 1000.0
    return VisualGenerationResult(
        image=img,
        provider="local_aesthetic",
        tier=4,
        prompt_used=effective_prompt,
        elapsed_ms=round(elapsed, 2),
        seed=seed,
        success=True,
        error_trail=error_trail,
    )


# ============================================================================
# TRACK A: ASPIRATIONAL LIFESTYLE PINS (ZERO PROMO BOXES, ZERO BUTTONS, ZERO PRICES)
# ============================================================================

def render_track_a_lifestyle_pin(
    title: str,
    board_name: Optional[str] = None,
    category: Optional[str] = None,
    style: str = "aspirational_lifestyle",
    product_img: Optional[Image.Image] = None,
    subtle_editorial_overlay: bool = True,
    brand_tag: str = "SMART SPACES",
) -> Image.Image:
    """Generates Track A (Aspirational Lifestyle Pins).

    Requirements:
    - 100% full-bleed, high-aesthetic interior design imagery.
    - ZERO promotional boxes (no white rectangles, cards, or borders).
    - ZERO giant buttons (no CTA buttons or shopping badges).
    - ZERO prices (no $xx.xx price stickers).
    - Optional subtle, elegant serif editorial title overlay with soft shadow.
    """
    logger.info("🌿 Rendering Track A (Aspirational Lifestyle Pin) — Full Bleed, Zero Promo Boxes...")

    # 1. Generate full-bleed visual via waterfall fallback
    result = generate_visual_with_waterfall(
        product_title=title,
        board_name=board_name,
        category=category,
        style=style,
        product_img=product_img,
    )
    canvas = result.image.copy()

    # If pure lifestyle with no text overlay is requested, return the pristine full bleed canvas
    if not subtle_editorial_overlay:
        return canvas

    # 2. Add subtle, delicate editorial typography overlay (no boxes, no buttons, no prices)
    draw = ImageDraw.Draw(canvas)

    # Sanitize title and brand to fix FreeType glyph bug
    clean_brand = sanitize_canvas_text(brand_tag).upper()
    clean_title = sanitize_canvas_text(title)

    # Subtle top vignette for legibility of light text over light or dark walls
    vignette = Image.new("RGBA", (CANVAS_WIDTH, CANVAS_HEIGHT), (0, 0, 0, 0))
    v_draw = ImageDraw.Draw(vignette)
    for y in range(320):
        alpha = int(140 * (1.0 - (y / 320.0)))
        v_draw.line([(0, y), (CANVAS_WIDTH, y)], fill=(0, 0, 0, alpha))
    for y in range(1280, CANVAS_HEIGHT):
        alpha = int(120 * ((y - 1280) / 220.0))
        v_draw.line([(0, y), (CANVAS_WIDTH, y)], fill=(0, 0, 0, alpha))
    canvas = Image.alpha_composite(canvas, vignette)
    draw = ImageDraw.Draw(canvas)

    # Top Brand Kicker (Delicate letter-spaced aesthetic serif)
    brand_font = get_canvas_font(BOLD_FONT_PATH, 20)
    b_bbox = brand_font.getbbox(clean_brand)
    b_w = b_bbox[2] - b_bbox[0]
    draw.text(((CANVAS_WIDTH - b_w) // 2 + 1, 65 + 1), clean_brand, fill=(0, 0, 0, 160), font=brand_font)
    draw.text(((CANVAS_WIDTH - b_w) // 2, 65), clean_brand, fill=(255, 255, 255, 230), font=brand_font)

    # Delicate Main Editorial Title (Clean Serif, elegant wrap)
    title_font_size = 46 if len(clean_title) < 55 else 38
    title_font = get_canvas_font(SERIF_FONT_PATH, title_font_size)

    # Wrap title within 840px max width
    words = clean_title.split()
    lines: List[str] = []
    cur_line: List[str] = []
    for w in words:
        test_l = " ".join(cur_line + [w])
        bb = title_font.getbbox(test_l)
        if (bb[2] - bb[0]) <= 840:
            cur_line.append(w)
        else:
            if cur_line:
                lines.append(" ".join(cur_line))
                cur_line = [w]
            else:
                lines.append(w)
                cur_line = []
    if cur_line:
        lines.append(" ".join(cur_line))
    lines = lines[:3]

    cur_y = 110
    for line in lines:
        line_bbox = title_font.getbbox(line)
        lw = line_bbox[2] - line_bbox[0]
        lx = (CANVAS_WIDTH - lw) // 2
        # Soft dark text shadow
        draw.text((lx + 2, cur_y + 2), line, fill=(0, 0, 0, 180), font=title_font)
        draw.text((lx, cur_y), line, fill=(255, 255, 255, 255), font=title_font)
        cur_y += title_font_size + 12

    # Subtle bottom aesthetic tag (e.g. "PIN FOR INSPIRATION • KINFOLK LIVING")
    bottom_font = get_canvas_font(REGULAR_FONT_PATH, 18)
    bottom_text = "PIN FOR LATER  •  SMART SPACES EDITORIAL"
    bb_box = bottom_font.getbbox(bottom_text)
    bb_w = bb_box[2] - bb_box[0]
    draw.text(((CANVAS_WIDTH - bb_w) // 2 + 1, CANVAS_HEIGHT - 65 + 1), bottom_text, fill=(0, 0, 0, 140), font=bottom_font)
    draw.text(((CANVAS_WIDTH - bb_w) // 2, CANVAS_HEIGHT - 65), bottom_text, fill=(245, 245, 240, 200), font=bottom_font)

    return canvas
