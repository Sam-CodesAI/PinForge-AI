"""PinForge AI — AI Vision & Aesthetic Curator.

Uses Google Gemini 2.0 Flash Vision to inspect product images:
- Extracts dominant and complementary color palettes (hex).
- Generates high-converting visual punchlines and badge hooks.
- Analyzes product orientation and focal framing for 2:3 Pinterest crops.
"""

import json
import logging
import os
import re
from typing import Dict, Any, Optional, Union
import io
from PIL import Image, ImageFilter, ImageStat

try:
    from google import genai
    from google.genai import types
    GEMINI_SDK_AVAILABLE = True
except ImportError:
    GEMINI_SDK_AVAILABLE = False

try:
    from python_engine.config import GEMINI_API_KEY
except ImportError:
    from config import GEMINI_API_KEY

logger = logging.getLogger("PinForge.AIVision")


def extract_image_cv_features(img_or_bytes: Union[Image.Image, bytes]) -> Dict[str, Any]:
    """High-speed native Pillow local CV extraction (<14ms).

    Extracts:
    - Foreground-isolated chromaticity (RB ratio ignoring white packshot pixels)
    - 2700K warm interior (RB > 1.35) vs neutral packshot (0.82 - 1.35) and cool glow (< 0.82)
    - Whitespace %, edge clutter, dominant and vibrant accent hex extraction
    - Salient bounding box and safe badge collision placement ('top_pill', 'bottom_pill', 'floating_badge')
    """
    default_res = {
        "rb_ratio": 1.0,
        "lighting_type": "neutral_packshot",
        "dominant_theme": "bento_dark",
        "whitespace_pct": 50.0,
        "edge_clutter": 15.0,
        "dominant_hex": "#0F172A",
        "accent_hex": "#06B6D4",
        "bounding_box": [0.2, 0.2, 0.8, 0.8],
        "badge_placement": "top_pill",
    }

    if not img_or_bytes:
        return default_res

    try:
        if isinstance(img_or_bytes, bytes):
            if len(img_or_bytes) < 100:
                return default_res
            raw_img = Image.open(io.BytesIO(img_or_bytes))
        else:
            raw_img = img_or_bytes

        # Downsample to 80x80 for sub-10ms native C-level Pillow execution
        dim = 80
        thumb = raw_img.convert("RGB").resize((dim, dim), Image.Resampling.BILINEAR)
        b = thumb.tobytes()
        mv = memoryview(b)

        white_count = 0
        fg_count = 0
        sum_r, sum_g, sum_b = 0, 0, 0
        min_x, min_y, max_x, max_y = dim, dim, 0, 0
        max_sat = -1
        vib_r, vib_g, vib_b = 6, 182, 212  # fallback cyan

        for i in range(0, len(mv), 3):
            r, g, b_val = mv[i], mv[i + 1], mv[i + 2]
            # Ignore white / near-white Amazon packshot studio background pixels
            if r > 240 and g > 240 and b_val > 240:
                white_count += 1
            else:
                fg_count += 1
                sum_r += r
                sum_g += g
                sum_b += b_val
                idx = i // 3
                x = idx % dim
                y = idx // dim
                if x < min_x: min_x = x
                if x > max_x: max_x = x
                if y < min_y: min_y = y
                if y > max_y: max_y = y

                sat = max(r, g, b_val) - min(r, g, b_val)
                if sat > max_sat:
                    max_sat = sat
                    vib_r, vib_g, vib_b = r, g, b_val

        total_pixels = dim * dim
        whitespace_pct = round((white_count / total_pixels) * 100.0, 1)

        if fg_count > 0:
            mean_r = sum_r / fg_count
            mean_g = sum_g / fg_count
            mean_b = sum_b / fg_count
            rb_ratio = round(mean_r / max(mean_b, 1.0), 3)
            dom_hex = f"#{int(mean_r):02x}{int(mean_g):02x}{int(mean_b):02x}"
            accent_hex = f"#{vib_r:02x}{vib_g:02x}{vib_b:02x}"
            bbox = [
                round(min_y / dim, 3),
                round(min_x / dim, 3),
                round(max_y / dim, 3),
                round(max_x / dim, 3),
            ]
        else:
            rb_ratio = 1.0
            dom_hex = "#0F172A"
            accent_hex = "#06B6D4"
            bbox = [0.2, 0.2, 0.8, 0.8]

        # Chromaticity classification
        if rb_ratio > 1.35:
            lighting_type = "2700K_warm"
            theme = "warm_editorial"
        elif rb_ratio >= 0.82:
            lighting_type = "neutral_packshot"
            theme = "problem_solver"
        else:
            lighting_type = "cool_glow"
            theme = "bento_dark"

        # Edge clutter using Pillow FIND_EDGES (<1ms)
        edges = thumb.convert("L").filter(ImageFilter.FIND_EDGES)
        edge_mean = ImageStat.Stat(edges).mean[0]
        edge_clutter = round(min(100.0, (edge_mean / 255.0) * 300.0), 1)

        # Safe badge collision placement
        if bbox[0] > 0.22:
            badge_placement = "top_pill"
        elif bbox[2] < 0.78:
            badge_placement = "bottom_pill"
        else:
            badge_placement = "floating_badge"

        return {
            "rb_ratio": rb_ratio,
            "lighting_type": lighting_type,
            "dominant_theme": theme,
            "whitespace_pct": whitespace_pct,
            "edge_clutter": edge_clutter,
            "dominant_hex": dom_hex,
            "accent_hex": accent_hex,
            "bounding_box": bbox,
            "badge_placement": badge_placement,
        }
    except Exception as e:
        logger.warning(f"Native CV extraction failed: {e}")
        return default_res


class AIVisionCurator:
    """Multimodal AI Curator for product image analysis and aesthetic composition."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or GEMINI_API_KEY or os.getenv("GEMINI_API_KEY", "")
        self.client = None
        if GEMINI_SDK_AVAILABLE and self.api_key:
            try:
                self.client = genai.Client(api_key=self.api_key)
            except Exception as e:
                logger.warning(f"Failed to initialize Google GenAI Client: {e}")

    def extract_image_cv(self, img_or_bytes: Union[Image.Image, bytes]) -> Dict[str, Any]:
        """Expose CV extraction on curator instance."""
        return extract_image_cv_features(img_or_bytes)

    def curate_product_visuals(
        self,
        image_bytes: bytes,
        product_title: str,
        price_str: str = "",
        discount_pct: int = 0,
    ) -> Dict[str, Any]:
        """Analyzes product image and returns curated design tokens and marketing copy."""
        # 1. Always extract high-speed native Pillow local CV features (<14ms)
        cv_features = extract_image_cv_features(image_bytes)

        if not self.client or not image_bytes:
            logger.info("Gemini API not configured or no image bytes, using procedural visual heuristics.")
            return self._procedural_heuristics(product_title, price_str, discount_pct, cv_features)

        prompt = f"""
You are an elite Pinterest Creative Director and e-commerce visual conversion expert.
Analyze this product image for:
Title: {product_title}
Price: {price_str}
Discount: {discount_pct}%

Return ONLY a valid JSON object with these exact keys:
{{
  "dominant_theme": "bento_dark" or "warm_editorial" or "problem_solver",
  "primary_hex": "#hex code matching product mood (e.g. #0B0F19 or #1A2332)",
  "accent_hex": "#vibrant accent hex (e.g. #06B6D4, #F59E0B, #10B981, or #E11D48)",
  "badge_text": "short high-converting badge 2-4 words (e.g. 'Viral Amazon Find', '94% Space Saved', 'Top Rated 2026')",
  "visual_hook": "compelling 3-6 word visual headline for 2:3 pin (e.g. 'The Ultimate Small Kitchen Hack', 'Transform Your Tiny Desk')",
  "secondary_hook": "brief 4-7 word punchy feature callout",
  "target_audience": "e.g. 'Apartment Renters', 'College Dorms', 'Minimalists', 'Home Cooks'",
  "alt_text": "Descriptive SEO-rich alt text under 120 chars for Pinterest accessibility"
}}
Do NOT include markdown formatting, backticks, or preamble. Return raw JSON only.
"""

        import time
        import random

        # Active production Gemini model hierarchy
        models = ["gemini-3.5-flash-lite", "gemini-3.1-flash-lite", "gemini-flash-lite-latest"]
        for model_name in models:
            for attempt in range(1, 4):
                try:
                    response = self.client.models.generate_content(
                        model=model_name,
                        contents=[
                            types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"),
                            prompt,
                        ],
                    )

                    text = response.text.strip()
                    # Clean possible markdown wrapping
                    text = re.sub(r"^```(?:json)?\s*", "", text)
                    text = re.sub(r"\s*```$", "", text)

                    data = json.loads(text)
                    # Merge CV tokens into returned data
                    data["cv_features"] = cv_features
                    for k in ("rb_ratio", "lighting_type", "whitespace_pct", "edge_clutter", "bounding_box", "badge_placement"):
                        data[k] = cv_features.get(k)

                    logger.info(f"AI Vision curation successful: {data.get('visual_hook')}")
                    return data
                except Exception as e:
                    if "503" in str(e) and attempt < 3:
                        delay = (2 ** attempt) + random.uniform(0, 1)
                        logger.warning(f"Gemini {model_name} 503 error, retrying in {delay:.2f}s...")
                        time.sleep(delay)
                        continue
                    logger.warning(f"Gemini Vision curation failed with {model_name} ({e})")
                    break

        return self._procedural_heuristics(product_title, price_str, discount_pct, cv_features)

    def _procedural_heuristics(
        self,
        product_title: str,
        price_str: str,
        discount_pct: int,
        cv_features: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Deterministic high-converting fallback incorporating Pillow local CV features."""
        title_lower = product_title.lower()
        cv = cv_features or {}

        # Default colors from CV if available, otherwise stylish defaults
        primary_hex = cv.get("dominant_hex", "#0F172A")
        accent_hex = cv.get("accent_hex", "#06B6D4")

        # Use CV chromaticity / lighting to guide theme selection when possible
        cv_lighting = cv.get("lighting_type")
        if cv_lighting == "2700K_warm" or any(w in title_lower for w in ["kitchen", "pantry", "dish", "spice", "cooking", "wood", "bamboo"]):
            theme = "warm_editorial"
            if not cv.get("dominant_hex"):
                primary_hex = "#1E293B"
            if not cv.get("accent_hex") or cv.get("accent_hex") == "#06b6d4":
                accent_hex = "#D97706"
            badge = "Viral Kitchen Hack" if discount_pct < 10 else f"{discount_pct}% OFF DEAL"
            hook = "Genius Small Kitchen Organizer"
        elif cv_lighting == "cool_glow" or any(w in title_lower for w in ["desk", "cable", "monitor", "laptop", "office", "tech"]):
            theme = "bento_dark"
            if not cv.get("dominant_hex"):
                primary_hex = "#0B0F19"
            if not cv.get("accent_hex"):
                accent_hex = "#06B6D4"
            badge = "Workspace Upgrade"
            hook = "Clean Minimalist Desk Setup"
        else:
            theme = "problem_solver"
            if not cv.get("dominant_hex"):
                primary_hex = "#0F172A"
            if not cv.get("accent_hex"):
                accent_hex = "#10B981"
            badge = "Space-Saving Genius"
            hook = "Maximize Your Small Space"

        result = {
            "dominant_theme": theme,
            "primary_hex": primary_hex,
            "accent_hex": accent_hex,
            "badge_text": badge,
            "visual_hook": hook,
            "secondary_hook": "Rated ⭐ 4.6+ by Amazon Shoppers",
            "target_audience": "Small Space Enthusiasts",
            "alt_text": f"{product_title[:80]} - Smart Spaces Amazon find",
            "cv_features": cv,
        }
        for k in ("rb_ratio", "lighting_type", "whitespace_pct", "edge_clutter", "bounding_box", "badge_placement"):
            if k in cv:
                result[k] = cv[k]

        return result
