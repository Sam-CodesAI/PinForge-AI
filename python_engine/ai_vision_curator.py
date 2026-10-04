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
from typing import Dict, Any, Optional

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

    def curate_product_visuals(
        self,
        image_bytes: bytes,
        product_title: str,
        price_str: str = "",
        discount_pct: int = 0,
    ) -> Dict[str, Any]:
        """Analyzes product image and returns curated design tokens and marketing copy."""
        if not self.client:
            logger.info("Gemini API not configured, using procedural visual heuristics.")
            return self._procedural_heuristics(product_title, price_str, discount_pct)

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
        
        models = ["gemini-3.8-flash", "gemini-3.5-flash-lite"]
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
        
        return self._procedural_heuristics(product_title, price_str, discount_pct)

    def _procedural_heuristics(
        self,
        product_title: str,
        price_str: str,
        discount_pct: int,
    ) -> Dict[str, Any]:
        """Deterministic high-converting fallback when AI is offline."""
        title_lower = product_title.lower()

        if any(w in title_lower for w in ["kitchen", "pantry", "dish", "spice", "cooking"]):
            theme = "warm_editorial"
            primary_hex = "#1E293B"
            accent_hex = "#D97706"
            badge = "Viral Kitchen Hack" if discount_pct < 10 else f"{discount_pct}% OFF DEAL"
            hook = "Genius Small Kitchen Organizer"
        elif any(w in title_lower for w in ["desk", "cable", "monitor", "laptop", "office"]):
            theme = "bento_dark"
            primary_hex = "#0B0F19"
            accent_hex = "#06B6D4"
            badge = "Workspace Upgrade"
            hook = "Clean Minimalist Desk Setup"
        else:
            theme = "problem_solver"
            primary_hex = "#0F172A"
            accent_hex = "#10B981"
            badge = "Space-Saving Genius"
            hook = "Maximize Your Small Space"

        return {
            "dominant_theme": theme,
            "primary_hex": primary_hex,
            "accent_hex": accent_hex,
            "badge_text": badge,
            "visual_hook": hook,
            "secondary_hook": "Rated ⭐ 4.6+ by Amazon Shoppers",
            "target_audience": "Small Space Enthusiasts",
            "alt_text": f"{product_title[:80]} - Smart Spaces Amazon find",
        }
