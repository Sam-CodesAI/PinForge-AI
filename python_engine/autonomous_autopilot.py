"""PinForge AI — Autonomous AI Autopilot.

Orchestrates end-to-end autonomous discovery, vision curation, A/B creative generation,
and live Pinterest publishing for the Smart Spaces brand:
1. AI Trend Hunter scans for viral space-saving Amazon products.
2. Stealth scraper extracts full Amazon product metadata.
3. Gemini 3.8 Flash Vision analyzes product image aesthetics and palettes.
4. Gemini 3.8 Flash generates SEO copy, boards, and FTC disclaimers.
5. Pillow compositor renders 3 high-converting 2:3 vertical variants.
6. Pinterest Client uploads image via Base64 to @Smart_Spaces.
7. Stores execution history in data/autopilot_history.json.
"""

import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional

try:
    from python_engine.ai_trend_hunter import AITrendHunter
    from python_engine.ai_vision_curator import AIVisionCurator
    from python_engine.scraper import fetch_product
    from python_engine.seo_engine import generate_pin_copy
    from python_engine.pin_generator import generate_all_pin_variants
    from python_engine.pinterest_client import PinterestClient
    from python_engine.config import DATA_DIR, DEFAULT_AFFILIATE_TAG
    from python_engine.models import CopyGenerationRequest, PinGenerateRequest
except ImportError:
    from ai_trend_hunter import AITrendHunter
    from ai_vision_curator import AIVisionCurator
    from scraper import fetch_product
    from seo_engine import generate_pin_copy
    from pin_generator import generate_all_pin_variants
    from pinterest_client import PinterestClient
    from config import DATA_DIR, DEFAULT_AFFILIATE_TAG
    from models import CopyGenerationRequest, PinGenerateRequest

logger = logging.getLogger("PinForge.Autopilot")

AUTOPILOT_HISTORY_FILE = DATA_DIR / "autopilot_history.json"


class AutonomousAutopilot:
    """End-to-end autonomous AI loop for Smart Spaces."""

    def __init__(self, affiliate_tag: str = DEFAULT_AFFILIATE_TAG):
        self.affiliate_tag = affiliate_tag
        self.hunter = AITrendHunter()
        self.curator = AIVisionCurator()
        self.pinterest = PinterestClient()

    def run_autopilot_cycle(
        self,
        target_asin_or_url: Optional[str] = None,
        publish_live: bool = True,
    ) -> Dict[str, Any]:
        """Runs 1 complete autonomous cycle."""
        cycle_start = time.perf_counter()
        logger.info("🚀 Starting PinForge AI Autonomous Autopilot cycle...")

        # 1. Product Discovery
        if target_asin_or_url:
            query_used = "manual_input"
            candidate = {"asin": target_asin_or_url, "product_url": target_asin_or_url, "viral_score": 95.0}
        else:
            candidate = self.hunter.hunt_top_trending_product()
            query_used = candidate.get("query_source", "ai_hunt")

        asin = candidate.get("asin", "")
        product_url = candidate.get("product_url", f"https://www.amazon.com/dp/{asin}")
        logger.info(f"Targeting Amazon Product: ASIN={asin} (Viral Score: {candidate.get('viral_score')})")

        # 2. Stealth Scraping
        product = fetch_product(product_url, affiliate_tag=self.affiliate_tag)

        # 3. AI Vision Curation
        image_bytes = b""
        if product.image_url:
            try:
                import httpx
                with httpx.Client(timeout=8.0, follow_redirects=True) as client:
                    img_resp = client.get(product.image_url)
                    if img_resp.status_code == 200:
                        image_bytes = img_resp.content
            except Exception as err:
                logger.warning(f"Could not pre-fetch image bytes for vision curator: {err}")

        vision_meta = self.curator.curate_product_visuals(
            image_bytes=image_bytes,
            product_title=product.title,
            price_str=product.price,
            discount_pct=product.discount_percent or 0,
        )

        # 4. Multi-Model AI SEO Copy
        copy_req = CopyGenerationRequest(
            product_title=product.title,
            brand=product.brand,
            category=product.category,
            price=product.price,
            features=product.features,
            rating=product.rating,
            affiliate_tag=self.affiliate_tag,
        )
        copy_res = generate_pin_copy(copy_req)

        # 5. Parallel 2:3 Pin Variant Generation (3 Aesthetic Styles)
        pin_req = PinGenerateRequest(
            title=vision_meta.get("visual_hook", copy_res.pin_title),
            image_url=product.image_url,
            price=product.price,
            original_price=product.original_price,
            rating=product.rating,
            review_count=product.review_count,
            badge_text=vision_meta.get("badge_text", "TOP RATED 2026"),
            features=product.features,
            template="bento_dark",
        )
        variants = generate_all_pin_variants(pin_req)

        # 6. Live Publishing to Pinterest API v5 (if enabled)
        live_pin_data = None
        if publish_live and self.pinterest.is_configured:
            chosen_variant = variants[0]  # default to bento_dark
            try:
                live_pin_data = self.pinterest.publish_pin(
                    title=copy_res.pin_title,
                    description=copy_res.pin_description,
                    board_name=copy_res.board_recommendation,
                    image_path_or_url=chosen_variant.image_path,
                    link=product.affiliate_url,
                    alt_text=vision_meta.get("alt_text"),
                )
                logger.info(f"✅ Published live Pin ID: {live_pin_data.get('pin_id')}")
                self.hunter.mark_asin_seen(
                    asin=product.asin,
                    title=product.title,
                    pin_id=live_pin_data.get("pin_id", ""),
                )
            except Exception as e:
                logger.error(f"Live Pinterest publishing failed: {e}")
                live_pin_data = {"error": str(e)}

        total_elapsed = round(time.perf_counter() - cycle_start, 2)

        result_summary = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "success",
            "execution_time_seconds": total_elapsed,
            "product": {
                "asin": product.asin,
                "title": product.title,
                "price": product.price,
                "rating": product.rating,
                "affiliate_url": product.affiliate_url,
                "bridge_slug": product.bridge_slug,
            },
            "ai_vision": vision_meta,
            "seo_copy": {
                "title": copy_res.pin_title,
                "description": copy_res.pin_description,
                "board": copy_res.board_recommendation,
                "hashtags": copy_res.hashtags,
            },
            "creative_variants": [
                {"template": v.image_path.split("_")[-2] if "_" in v.image_path else "pin", "url": v.image_url}
                for v in variants
            ],
            "live_pinterest": live_pin_data,
        }

        self._record_history(result_summary)
        return result_summary

    def _record_history(self, summary: Dict[str, Any]):
        """Appends run results to history file."""
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        try:
            history = []
            if AUTOPILOT_HISTORY_FILE.exists():
                history = json.loads(AUTOPILOT_HISTORY_FILE.read_text())
            history.append(summary)
            AUTOPILOT_HISTORY_FILE.write_text(json.dumps(history[-100:], indent=2))
        except Exception as e:
            logger.warning(f"Could not write history file: {e}")
