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

from __future__ import annotations

import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, List

try:
    from python_engine.ai_trend_hunter import AITrendHunter
    from python_engine.ai_vision_curator import AIVisionCurator
    from python_engine.scraper import fetch_product, format_usd_price
    from python_engine.seo_engine import generate_pin_copy
    from python_engine.pin_generator import generate_all_pin_variants
    from python_engine.carousel_engine import generate_carousel_pin_suite
    from python_engine.pinterest_client import PinterestClient
    from python_engine.config import DATA_DIR, DEFAULT_AFFILIATE_TAG
    from python_engine.models import CopyGenerationRequest, PinGenerateRequest
except ImportError:
    from ai_trend_hunter import AITrendHunter
    from ai_vision_curator import AIVisionCurator
    from scraper import fetch_product, format_usd_price
    from seo_engine import generate_pin_copy
    from pin_generator import generate_all_pin_variants
    from carousel_engine import generate_carousel_pin_suite
    from pinterest_client import PinterestClient
    from config import DATA_DIR, DEFAULT_AFFILIATE_TAG
    from models import CopyGenerationRequest, PinGenerateRequest

logger = logging.getLogger("PinForge.Autopilot")

AUTOPILOT_HISTORY_FILE = DATA_DIR / "autopilot_history.json"


def _build_slide_title(prefix: str, base_title: str, max_len: int = 100) -> str:
    """Builds a slide title with prefix, ensuring word-boundary truncation within max_len."""
    clean_prefix = prefix.strip()
    clean_title = base_title.strip()
    allowed_len = max_len - len(clean_prefix) - 2  # for ': '
    if len(clean_title) <= allowed_len:
        return f"{clean_prefix}: {clean_title}"
    truncated = clean_title[:allowed_len]
    if " " in truncated:
        truncated = truncated.rsplit(" ", 1)[0]
    return f"{clean_prefix}: {truncated.strip(' ,.-–—')}"


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
        target_board: Optional[str] = None,
        custom_queries: Optional[List[str]] = None,
        publish_live: bool = True,
        publish_as_carousel: bool = False,
        track_a: bool = False,
        template_style: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Runs 1 complete autonomous cycle."""
        cycle_start = time.perf_counter()
        logger.info(f"🚀 Starting PinForge AI Autonomous Autopilot cycle (Track A={track_a})...")

        # 1. Product Discovery
        if target_asin_or_url:
            query_used = "manual_input"
            candidate = {"asin": target_asin_or_url, "product_url": target_asin_or_url, "viral_score": 95.0}
        else:
            candidate = self.hunter.hunt_top_trending_product(custom_queries=custom_queries)
            query_used = candidate.get("query_source", "ai_hunt")

        asin = candidate.get("asin", "")
        product_url = candidate.get("product_url", f"https://www.amazon.com/dp/{asin}")
        logger.info(f"Targeting Amazon Product: ASIN={asin} (Viral Score: {candidate.get('viral_score')})")

        # 2. Stealth Scraping
        candidate_price_str = format_usd_price(candidate.get("price"))
        product = fetch_product(
            product_url,
            affiliate_tag=self.affiliate_tag,
            known_image_url=candidate.get("image_url"),
            known_title=candidate.get("title"),
            known_price=candidate_price_str,
        )

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

        # 5. Parallel 2:3 Pin Variant Generation (4 Aesthetic Styles)
        effective_board = target_board or copy_res.board_recommendation
        f_badge = product.friction_badge or "100% RENTER FRIENDLY • NO DRILL"
        pin_req = PinGenerateRequest(
            title=vision_meta.get("visual_hook", copy_res.pin_title),
            image_url=product.image_url,
            price=product.price,
            original_price=product.original_price,
            rating=product.rating,
            review_count=product.review_count,
            badge_text=vision_meta.get("badge_text", "TOP RATED 2026"),
            friction_badge=f_badge,
            friction_highlights=product.friction_highlights,
            features=product.features,
            category=product.category,
            board_name=effective_board,
            template="bento_dark",
        )
        variants = generate_all_pin_variants(pin_req)

        # 5b. Generate 4-Slide E-Commerce Shopping App Carousel Suite with Artistic Theme
        b_low = effective_board.lower()
        if "kitchen" in b_low:
            carousel_style = "luxury_editorial"
        elif "closet" in b_low or "wardrobe" in b_low:
            carousel_style = "story"
        elif "apartment" in b_low or "studio" in b_low:
            carousel_style = "anime"
        else:
            carousel_style = "cyber_bento"

        carousel_suite = generate_carousel_pin_suite(
            title=vision_meta.get("visual_hook", copy_res.pin_title),
            price=product.price,
            rating=product.rating,
            review_count=product.review_count,
            image_url=product.image_url,
            features=product.features,
            additional_images=product.additional_images,
            badge_text=vision_meta.get("badge_text", "TOP RATED 2026"),
            friction_badge=f_badge,
            friction_highlights=product.friction_highlights,
            style=carousel_style,
        )

        # 6. Live Publishing to Pinterest API v5 (if enabled)
        live_pin_data = None
        if publish_live and self.pinterest.is_configured:
            try:
                if publish_as_carousel and carousel_suite.get("slide_paths"):
                    # Native Base64 Carousel Publishing with per-slide deep affiliate links
                    spec_callout = (
                        product.friction_highlights[1]
                        if len(product.friction_highlights) > 1
                        else (product.features[0] if product.features else "Tested load capacity and tool-free setup")
                    )
                    rental_callout = product.friction_badge or "100% RENTER FRIENDLY • NO DRILL"

                    carousel_slides = [
                        {
                            "image_path": carousel_suite["slide_paths"][0],
                            "title": f"{copy_res.pin_title[:88]} (Slide 1/4)",
                            "description": copy_res.pin_description,
                            "link": product.affiliate_url,
                        },
                        {
                            "image_path": carousel_suite["slide_paths"][1],
                            "title": _build_slide_title("Dimensions & Build Specs", product.title),
                            "description": f"Full space-saving specifications, dimensions, and {spec_callout.lower()}. Check today's price! #AmazonAssociate",
                            "link": product.affiliate_url,
                        },
                        {
                            "image_path": carousel_suite["slide_paths"][2],
                            "title": _build_slide_title("Color & Angle Variants", product.title),
                            "description": "Multi-angle inspection, finish options, and aesthetic variants for modern compact homes. Tap to view on Amazon! #AmazonAssociate",
                            "link": product.affiliate_url,
                        },
                        {
                            "image_path": carousel_suite["slide_paths"][3],
                            "title": _build_slide_title("Transform Your Space", product.title),
                            "description": f"Real-world space-saving transformation. {rental_callout}. Practical uses for compact living. Tap for today's deal! #AmazonAssociate",
                            "link": product.affiliate_url,
                        },
                    ]
                    live_pin_data = self.pinterest.publish_pin(
                        title=copy_res.pin_title,
                        description=copy_res.pin_description,
                        board_name=effective_board,
                        slides=carousel_slides,
                        link=product.affiliate_url,
                        alt_text=vision_meta.get("alt_text"),
                    )
                    logger.info(f"✅ Published live Carousel Pin ID: {live_pin_data.get('pin_id')} to Board: '{effective_board}'")
                else:
                    # Dynamic single-pin template routing based on Track A, AI vision theme, and board intent
                    if track_a or template_style in ("aspirational_lifestyle", "track_a_lifestyle"):
                        chosen_variant = next(
                            (v for v in variants if "aspirational_lifestyle" in v.image_path),
                            variants[0],
                        )
                    else:
                        v_theme = vision_meta.get("theme", "bento_dark")
                        chosen_variant = variants[0]
                        for v in variants:
                            if v_theme in v.image_path:
                                chosen_variant = v
                                break
                        else:
                            # If specific theme not found, rotate lifestyle for apartment/studio boards
                            if any(k in effective_board.lower() for k in ["apartment", "studio"]):
                                for v in variants:
                                    if "aspirational_lifestyle" in v.image_path or "pollinations_lifestyle" in v.image_path:
                                        chosen_variant = v
                                        break

                    live_pin_data = self.pinterest.publish_pin(
                        title=copy_res.pin_title,
                        description=copy_res.pin_description,
                        board_name=effective_board,
                        image_path_or_url=chosen_variant.image_path,
                        link=product.affiliate_url,
                        alt_text=vision_meta.get("alt_text"),
                    )
                    logger.info(f"✅ Published live Pin ID: {live_pin_data.get('pin_id')} to Board: '{effective_board}'")
            except Exception as e:
                logger.error(f"Live Pinterest publishing failed: {e}")
                live_pin_data = {"error": str(e)}

        # Always record executed ASIN to ensure deduplication across all cycles
        pin_id_str = ""
        if isinstance(live_pin_data, dict):
            pin_id_str = str(live_pin_data.get("pin_id", ""))
        self.hunter.mark_asin_seen(
            asin=product.asin,
            title=product.title,
            pin_id=pin_id_str,
        )

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
                "board": effective_board,
                "hashtags": copy_res.hashtags,
            },
            "creative_variants": [
                {"template": v.template or (v.image_path.split("_")[-2] if "_" in v.image_path else "pin"), "url": v.image_url}
                for v in variants
            ],
            "track_a_lifestyle": next((v.image_url for v in variants if "aspirational_lifestyle" in v.image_path), None),
            "carousel": {
                "slides": carousel_suite["slide_paths"],
                "composite": carousel_suite["composite_path"],
                "style": carousel_suite["style"],
            },
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
