"""PinForge AI — Google Antigravity Agentic Orchestrator ('AI with Hands').

Orchestrates the autonomous multi-agent pipeline for @Smart_Spaces:
1. Sourcing Tool: Extracts verified product data & image assets via curl_cffi.
2. SEO Tool: Generates high-CTR title, keyword-dense description, and #AmazonAssociate disclosure.
3. Creative Tool: Renders 1000x1500 vertical 2:3 pin graphics via Pillow / Canva.
4. Publisher Tool: Posts programmatically to Pinterest API v5 on matching @Smart_Spaces boards.
5. Self-Learning Tool: Evaluates Pinterest analytics and updates prompt weights.
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

# Path setup
CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))
if str(CURRENT_DIR.parent) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR.parent))

from config import DEFAULT_AFFILIATE_TAG, BASE_URL, DATA_DIR, STATIC_DIR, PINS_DIR
from scraper import fetch_product
from seo_engine import generate_pin_copy
from pin_generator import generate_pin_graphic
from pinterest_client import PinterestClient
from models import (
    ExtractRequest,
    CopyGenerationRequest,
    PinGenerateRequest,
    ProductData,
    PinCopyResponse,
    PinGenerateResponse,
)

logger = logging.getLogger("pinforge.antigravity")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")


class AntigravityOrchestrator:
    """Agentic Orchestrator providing the AI with concrete 'hands' (executable tools)."""

    def __init__(self, affiliate_tag: str = DEFAULT_AFFILIATE_TAG):
        self.affiliate_tag = affiliate_tag
        self.pinterest = PinterestClient()
        self.ledger_file = DATA_DIR / "autonomous_ledger.json"

    # ==========================================
    # TOOL 1: SOURCING & EXTRACTION
    # ==========================================
    def tool_source_product(self, url_or_asin: str) -> Dict[str, Any]:
        """Tool: Scrapes Amazon product details with Chrome 124 stealth TLS fingerprinting."""
        logger.info(f"🖐️ [Tool Executing] tool_source_product: {url_or_asin}")
        product = fetch_product(url_or_asin, self.affiliate_tag)
        logger.info(f"✓ Sourced: {product.title[:60]}... | Price: {product.price} | ASIN: {product.asin}")
        return product.model_dump()

    # ==========================================
    # TOOL 2: SEO COPYWRITING STUDIO
    # ==========================================
    def tool_generate_copy(self, product_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Tool: Generates search-ranked Pinterest title, description, and hashtags via Gemini/Groq."""
        logger.info(f"🖐️ [Tool Executing] tool_generate_copy for ASIN: {product_dict.get('asin')}")
        req = CopyGenerationRequest(
            product_title=product_dict.get("title", "Space Saving Organizer"),
            brand=product_dict.get("brand"),
            category=product_dict.get("category", "Home & Room Organization"),
            price=product_dict.get("price", "$29.99"),
            features=product_dict.get("features", []),
            rating=product_dict.get("rating", 4.7),
            affiliate_tag=self.affiliate_tag,
        )
        copy_res = generate_pin_copy(req)
        logger.info(f"✓ Generated Copy: '{copy_res.pin_title}' | Board: '{copy_res.board_recommendation}'")
        return copy_res.model_dump()

    # ==========================================
    # TOOL 3: 2:3 VERTICAL CREATIVE GENERATOR
    # ==========================================
    def tool_render_pin(
        self,
        product_dict: Dict[str, Any],
        copy_dict: Dict[str, Any],
        template_style: str = "bento_dark",
    ) -> Dict[str, Any]:
        """Tool: Renders a high-resolution 1000x1500 vertical 2:3 pin graphic."""
        logger.info(f"🖐️ [Tool Executing] tool_render_pin (Style: {template_style})")
        req = PinGenerateRequest(
            title=copy_dict.get("pin_title") or product_dict.get("title", ""),
            image_url=product_dict.get("image_url", ""),
            price=product_dict.get("price", "$29.99"),
            original_price=product_dict.get("original_price"),
            rating=product_dict.get("rating", 4.8),
            review_count=product_dict.get("review_count", "1,200+"),
            template=template_style if template_style in ["bento_dark", "warm_editorial", "problem_solver"] else "bento_dark",  # type: ignore
            brand=product_dict.get("brand"),
            features=product_dict.get("features", []),
            cta_text="CHECK PRICE ON AMAZON ➔",
        )
        pin_res = generate_pin_graphic(req)
        logger.info(f"✓ Rendered Pin: {pin_res.image_url} in {pin_res.render_time_ms:.1f}ms")
        return pin_res.model_dump()

    # ==========================================
    # TOOL 4: PINTEREST API v5 PUBLISHER
    # ==========================================
    def tool_publish_pin(
        self,
        board_name_or_keyword: str,
        title: str,
        description: str,
        link: str,
        image_url: Optional[str] = None,
        image_path: Optional[str] = None,
        base64_image: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Tool: Posts programmatically to the matching @Smart_Spaces Pinterest board."""
        logger.info(f"🖐️ [Tool Executing] tool_publish_pin to board query: '{board_name_or_keyword}'")
        
        # 1. Resolve or create board
        board_id = self.pinterest.get_or_create_board(board_name_or_keyword)

        # 2. Call Pinterest API v5
        result = self.pinterest.create_pin(
            board_id=board_id,
            title=title,
            description=description,
            link=link,
            image_url=image_url,
            image_path=image_path,
            base64_image=base64_image,
        )
        logger.info(f"✓ Successfully published Pin ID: {result.get('id')} to Board ID: {board_id}")
        return result

    # ==========================================
    # TOOL 5: SELF-LEARNING ANALYTICS
    # ==========================================
    def tool_evaluate_analytics(self, days: int = 14) -> Dict[str, Any]:
        """Tool: Fetches recent Pinterest performance metrics and calculates engagement."""
        logger.info(f"🖐️ [Tool Executing] tool_evaluate_analytics (Past {days} days)")
        analytics_data = self.pinterest.get_account_analytics(days=days)
        return analytics_data

    # ==========================================
    # ==========================================
    # TOOL 3B: CAROUSEL SUITE GENERATOR
    # ==========================================
    def tool_render_carousel_suite(
        self,
        product_dict: Dict[str, Any],
        copy_dict: Dict[str, Any],
        style: str = "cyber_bento",
    ) -> Dict[str, Any]:
        """Tool: Renders a 4-slide shopping app carousel suite."""
        logger.info(f"🖐️ [Tool Executing] tool_render_carousel_suite (Style: {style})")
        from carousel_engine import generate_carousel_pin_suite
        f_badge = product_dict.get("friction_badge") or "100% RENTER FRIENDLY • NO DRILL"
        suite = generate_carousel_pin_suite(
            title=copy_dict.get("pin_title") or product_dict.get("title", ""),
            price=product_dict.get("price", "$29.99"),
            rating=product_dict.get("rating", 4.8),
            review_count=product_dict.get("review_count", "1,200+"),
            image_url=product_dict.get("image_url", ""),
            features=product_dict.get("features", []),
            additional_images=product_dict.get("additional_images", []),
            friction_badge=f_badge,
            friction_highlights=product_dict.get("friction_highlights", []),
            style=style,
        )
        logger.info(f"✓ Rendered 4-slide carousel suite with {suite.get('total_slides', 4)} slides")
        return suite

    # ==========================================
    # COMPLETE END-TO-END AUTONOMOUS PIPELINE
    # ==========================================
    def execute_autonomous_cycle(
        self,
        url_or_asin: str,
        template_style: str = "bento_dark",
        publish_live: bool = False,
        publish_as_carousel: bool = False,
    ) -> Dict[str, Any]:
        """Executes the full automated workflow from sourcing to FTC bridge routing and Pinterest posting."""
        logger.info(f"🚀 Starting Autonomous PinForge Cycle for: {url_or_asin} (Carousel={publish_as_carousel})")
        start_time = datetime.now()

        # Step 1: Source
        product = self.tool_source_product(url_or_asin)

        # Step 2: Copywriting
        copy = self.tool_generate_copy(product)

        # Step 3: Render Creative
        graphic = self.tool_render_pin(product, copy, template_style=template_style)
        carousel_suite = None
        if publish_as_carousel:
            c_style = template_style if template_style in ["cyber_bento", "luxury_editorial", "story", "anime"] else "cyber_bento"
            carousel_suite = self.tool_render_carousel_suite(product, copy, style=c_style)

        # Step 4: Construct Bridge Destination URL
        slug = product.get("asin", "").lower()
        bridge_url = f"{BASE_URL}/p/{slug}?tag={self.affiliate_tag}"
        image_url = graphic.get("image_url")

        result = {
            "asin": product.get("asin"),
            "title": copy.get("pin_title"),
            "description": copy.get("pin_description"),
            "board_recommendation": copy.get("board_recommendation"),
            "image_url": image_url,
            "bridge_url": bridge_url,
            "render_time_ms": graphic.get("render_time_ms"),
            "is_carousel": publish_as_carousel,
            "status": "ready",
            "published_to_pinterest": False,
        }
        if carousel_suite:
            result["carousel_suite"] = carousel_suite

        # Step 5: Publish if live mode requested
        if publish_live:
            try:
                board_target = copy.get("board_recommendation", "Room Organization")
                if publish_as_carousel and carousel_suite and carousel_suite.get("slide_paths"):
                    prod_title = product.get("title", "")
                    highlights = product.get("friction_highlights", [])
                    spec_txt = highlights[1] if len(highlights) > 1 else "Tested load capacity and tool-free setup"
                    rent_txt = product.get("friction_badge") or "100% RENTER FRIENDLY • NO DRILL"

                    def _slide_t(prefix: str, base_t: str) -> str:
                        clean_p = prefix.strip()
                        clean_b = base_t.strip()
                        max_len = 100 - len(clean_p) - 2
                        if len(clean_b) <= max_len:
                            return f"{clean_p}: {clean_b}"
                        tr = clean_b[:max_len]
                        if " " in tr:
                            tr = tr.rsplit(" ", 1)[0]
                        return f"{clean_p}: {tr.strip(' ,.-–—')}"

                    c_slides = [
                        {
                            "image_path": carousel_suite["slide_paths"][0],
                            "title": f"{copy.get('pin_title', '')[:88]} (Slide 1/4)",
                            "description": copy.get("pin_description", ""),
                            "link": bridge_url,
                        },
                        {
                            "image_path": carousel_suite["slide_paths"][1],
                            "title": _slide_t("Dimensions & Build Specs", prod_title),
                            "description": f"Full space-saving specifications, dimensions, and {spec_txt.lower()}. Check today's price! #AmazonAssociate",
                            "link": bridge_url,
                        },
                        {
                            "image_path": carousel_suite["slide_paths"][2],
                            "title": _slide_t("Color & Angle Variants", prod_title),
                            "description": "Multi-angle inspection, finish options, and aesthetic variants for modern compact homes. Tap to view on Amazon! #AmazonAssociate",
                            "link": bridge_url,
                        },
                        {
                            "image_path": carousel_suite["slide_paths"][3],
                            "title": _slide_t("Transform Your Space", prod_title),
                            "description": f"Real-world space-saving transformation. {rent_txt}. Practical uses for compact living. Tap for today's deal! #AmazonAssociate",
                            "link": bridge_url,
                        },
                    ]
                    pin_pub = self.pinterest.publish_carousel_pin(
                        title=copy.get("pin_title", ""),
                        description=copy.get("pin_description", ""),
                        board_name=board_target,
                        slides=c_slides,
                        link=bridge_url,
                    )
                else:
                    pin_pub = self.tool_publish_pin(
                        board_name_or_keyword=board_target,
                        title=copy.get("pin_title", ""),
                        description=copy.get("pin_description", ""),
                        link=bridge_url,
                        image_url=image_url,
                        image_path=graphic.get("image_path"),
                        base64_image=graphic.get("base64_image"),
                    )

                result["published_to_pinterest"] = True
                result["pinterest_pin_id"] = pin_pub.get("id")
                result["status"] = "published"
            except PermissionError as perm_err:
                logger.warning(f"⚠️ Pinterest Token needs write scope: {perm_err}")
                result["publish_error"] = str(perm_err)
                result["status"] = "queued_pending_write_scope"
            except Exception as pub_err:
                logger.error(f"❌ Failed to publish to Pinterest: {pub_err}")
                result["publish_error"] = str(pub_err)
                result["status"] = "failed"

        # Record to Autonomous Ledger
        self._record_cycle(result)
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info(f"🎉 Autonomous Cycle completed in {elapsed:.2f}s | Status: {result['status']}")
        return result

    def _record_cycle(self, result: Dict[str, Any]) -> None:
        """Persist cycle to autonomous ledger."""
        try:
            records = []
            if self.ledger_file.exists():
                records = json.loads(self.ledger_file.read_text())
            records.append({**result, "timestamp": datetime.now().isoformat()})
            self.ledger_file.write_text(json.dumps(records, indent=2))
        except Exception as e:
            logger.warning(f"Failed to record cycle: {e}")


if __name__ == "__main__":
    orchestrator = AntigravityOrchestrator()
    print("Testing Autonomous Sourcing & Creative Generation...")
    # Test on a verified desk organizer ASIN
    cycle_result = orchestrator.execute_autonomous_cycle(
        url_or_asin="B087F5K713",  # Space-saving desk organizer
        template_style="bento_dark",
        publish_live=False,  # Dry run
    )
    print("\nAutonomous Cycle Result:")
    print(json.dumps(cycle_result, indent=2))
