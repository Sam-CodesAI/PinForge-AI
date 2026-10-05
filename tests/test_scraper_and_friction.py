"""PinForge AI — Comprehensive Tests for Scraper, Friction Classifier, Currency Parsing, and Deduplication.
"""

import io
import json
import unittest
from unittest.mock import MagicMock, patch
from PIL import Image

from python_engine.ai_trend_hunter import AITrendHunter, BLACKLISTED_ASINS, VERIFIED_SMART_SPACES_POOL
from python_engine.autonomous_autopilot import AutonomousAutopilot
from python_engine.models import CopyGenerationRequest, PinCopyResponse, ProductData
from python_engine.pin_generator import download_image
from python_engine.scraper import (
    calculate_discount_percent,
    classify_mounting_and_safety,
    fetch_product,
    format_usd_price,
    mine_friction_highlights,
    resolve_master_image_url,
    scrape_amazon_direct,
)
from python_engine.seo_engine import generate_pin_copy


class TestCurrencyAndDiscount(unittest.TestCase):
    """Test currency normalization and discount calculation without INR divisor bug."""

    def test_usd_pricing_up_to_999(self):
        # Previously broken by division by 84.0
        self.assertEqual(format_usd_price("$249.99"), "$249.99")
        self.assertEqual(format_usd_price("249.99"), "$249.99")
        self.assertEqual(format_usd_price("$899.00"), "$899.00")
        self.assertEqual(format_usd_price("899.00"), "$899.00")
        self.assertEqual(format_usd_price("$999.00"), "$999.00")
        self.assertEqual(format_usd_price("999.00"), "$999.00")

    def test_usd_pricing_standard_and_bounds(self):
        self.assertEqual(format_usd_price("$29.99"), "$29.99")
        self.assertEqual(format_usd_price("49.95"), "$49.95")
        self.assertEqual(format_usd_price("15"), "$15.00")
        self.assertEqual(format_usd_price(""), "$24.99")
        self.assertEqual(format_usd_price(None), "$24.99")
        self.assertEqual(format_usd_price("invalid"), "$24.99")
        # Over 999 capped to 999.00
        self.assertEqual(format_usd_price("$1,499.00"), "$999.00")

    def test_calculate_discount_percent(self):
        self.assertEqual(calculate_discount_percent("$29.99", "$39.99"), 25)
        self.assertEqual(calculate_discount_percent("$150.00", "$200.00"), 25)
        self.assertEqual(calculate_discount_percent("80", "100"), 20)
        self.assertIsNone(calculate_discount_percent("$50.00", "$50.00"))
        self.assertIsNone(calculate_discount_percent("$60.00", "$50.00"))
        self.assertIsNone(calculate_discount_percent("$29.99", None))


class TestMasterImageResolutionAndGifRejection(unittest.TestCase):
    """Test Amazon CDN master image URL extraction and GIF / 43-byte rejection."""

    def test_resolve_master_image_url(self):
        # Strips Amazon dynamic crop and size tags
        test_cases = [
            (
                "https://m.media-amazon.com/images/I/71+8M4pS+SL._AC_SL1500_.jpg",
                "https://m.media-amazon.com/images/I/71+8M4pS+SL.jpg",
            ),
            (
                "https://m.media-amazon.com/images/I/61Nl0kS9VqL._AC_SX679_.jpg",
                "https://m.media-amazon.com/images/I/61Nl0kS9VqL.jpg",
            ),
            (
                "https://m.media-amazon.com/images/P/B087F5K713.01._SCLZZZZZZZ_SX900_.jpg",
                "https://m.media-amazon.com/images/P/B087F5K713.01.jpg",
            ),
            (
                "https://m.media-amazon.com/images/I/71abc.jpg",
                "https://m.media-amazon.com/images/I/71abc.jpg",
            ),
        ]
        for raw_url, expected in test_cases:
            self.assertEqual(resolve_master_image_url(raw_url), expected)

    @patch("httpx.Client.get")
    def test_download_image_rejects_under_1000_bytes(self, mock_get):
        # 43-byte 1x1 tracking pixel payload
        fake_43_bytes = (
            b"GIF89a\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00!\xf9\x04\x01\x00"
            b"\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;"
        )
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.content = fake_43_bytes
        mock_resp.headers = {"content-type": "image/gif"}
        mock_get.return_value = mock_resp

        result = download_image("https://example.com/pixel.gif")
        self.assertIsNone(result)

    @patch("httpx.Client.get")
    def test_download_image_rejects_gif_content_type(self, mock_get):
        # Valid-sized GIF (> 1000 bytes) but should still be rejected because of GIF type
        buf = io.BytesIO()
        img = Image.new("P", (100, 100), color=1)
        img.save(buf, format="GIF")
        gif_bytes = buf.getvalue()
        # Ensure it's padded > 1000 bytes
        padded_gif = gif_bytes + b"\x00" * 1200

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.content = padded_gif
        mock_resp.headers = {"content-type": "image/gif"}
        mock_get.return_value = mock_resp

        result = download_image("https://example.com/animation.gif")
        self.assertIsNone(result)

    @patch("httpx.Client.get")
    def test_download_image_accepts_valid_large_png(self, mock_get):
        buf = io.BytesIO()
        # Create uncompressed textured image to ensure bytes > 1000
        import os
        img = Image.frombytes("RGBA", (100, 100), os.urandom(100 * 100 * 4))
        img.save(buf, format="PNG")
        png_bytes = buf.getvalue()
        self.assertGreater(len(png_bytes), 1000)

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.content = png_bytes
        mock_resp.headers = {"content-type": "image/png"}
        mock_get.return_value = mock_resp

        result = download_image("https://example.com/product.png")
        self.assertIsNotNone(result)
        self.assertEqual(result.size, (100, 100))


class TestDeterministicMountingAndSafetyClassifier(unittest.TestCase):
    """Test deterministic mounting classification and anti-false-badging invariants."""

    def test_countertop_freestanding(self):
        specs = {"Mounting Type": "Countertop", "Material": "Stainless Steel"}
        bullets = ["Sits freely on any kitchen counter", "Non-slip rubber feet prevent sliding"]
        m_type, is_renter, badge = classify_mounting_and_safety(specs, bullets)
        self.assertEqual(m_type, "Countertop / Freestanding")
        self.assertTrue(is_renter)
        self.assertEqual(badge, "100% RENTER FRIENDLY • NO DRILL")

    def test_in_drawer(self):
        specs = {"Mounting Type": "In-Drawer", "Recommended Uses": "Silverware"}
        bullets = ["Expands from 13 to 22 inches to fit standard kitchen drawers", "Tool-free drop-in fit"]
        m_type, is_renter, badge = classify_mounting_and_safety(specs, bullets)
        self.assertEqual(m_type, "In-Drawer")
        self.assertTrue(is_renter)
        self.assertIn("IN-DRAWER", badge)

    def test_over_the_door(self):
        specs = {"Mounting Type": "Over the Door"}
        bullets = ["Includes sturdy metal hooks that fit standard doors", "No tools or drilling required"]
        m_type, is_renter, badge = classify_mounting_and_safety(specs, bullets)
        self.assertEqual(m_type, "Over-the-Door")
        self.assertTrue(is_renter)
        self.assertEqual(badge, "OVER-THE-DOOR • ZERO WALL HOLES")

    def test_tension_adhesive(self):
        specs = {"Mounting Type": "Tension Mount"}
        bullets = ["Heavy-duty spring tension rod", "Strong damage-free adhesive strips included"]
        m_type, is_renter, badge = classify_mounting_and_safety(specs, bullets)
        self.assertEqual(m_type, "Tension/Adhesive")
        self.assertTrue(is_renter)
        self.assertEqual(badge, "100% RENTER FRIENDLY • NO DRILL")

    def test_screw_wall_mount_invariant(self):
        # Strict invariant: screw/stud mounted products must NEVER be badged as renter friendly / no drill
        specs = {"Mounting Type": "Wall Mount", "Item Weight": "8 lbs"}
        bullets = [
            "Heavy-duty floating shelves engineered for living room display",
            "Mounting hardware included: heavy-duty screws and drywall anchors",
            "Must be anchored directly into wall studs for 50 lb load rating",
        ]
        m_type, is_renter, badge = classify_mounting_and_safety(specs, bullets)
        self.assertEqual(m_type, "Screw / Wall-Mount")
        self.assertFalse(is_renter)
        self.assertEqual(badge, "HEAVY-DUTY STUD MOUNT • ZERO SAG")

        # Also verify mine_friction_highlights honors this invariant
        highlights, primary_badge = mine_friction_highlights(
            title="Industrial Pipe Wall Floating Shelf",
            bullets=bullets,
            specs=specs,
        )
        self.assertEqual(primary_badge, "HEAVY-DUTY STUD MOUNT • ZERO SAG")
        self.assertNotIn("100% RENTER FRIENDLY • NO DRILL", highlights)
        self.assertIn("HEAVY-DUTY STUD MOUNT • ZERO SAG", highlights)


class TestMobileScraperAndSignals(unittest.TestCase):
    """Test mobile-web anti-bot bypass endpoint (/gp/aw/d/) and signal extraction."""

    SAMPLE_MOBILE_HTML = """
    <html>
      <body>
        <h1 id="title">Space-Saving Expandable Tiered Organizer Rack</h1>
        <a id="bylineInfo">Visit the SpaceCraft Store</a>
        <div id="apex-pricetopay-accessibility-label">$34.99</div>
        <span class="basisPrice"><span class="a-offscreen">$49.99</span></span>
        <span class="couponBadge">Save $5.00 with coupon</span>
        <div id="social-proofing-faceout-title-tk_bought">50K+ bought in past month</div>
        <span class="dealBadge">Limited time deal</span>
        <div id="acrPopover" title="4.8 out of 5 stars"></div>
        <span id="acrCustomerReviewText">12,450 ratings</span>
        <div id="productOverview_feature_div">
          <table>
            <tr><td>Mounting Type</td><td>Countertop</td></tr>
            <tr><td>Material</td><td>Alloy Steel</td></tr>
          </table>
        </div>
        <ul id="feature-bullets">
          <li><span>Tool-free 60 second assembly</span></li>
          <li><span>Ultra-slim 5.5 inch profile fits any narrow gap</span></li>
        </ul>
        <img id="landingImage" src="https://m.media-amazon.com/images/I/71Y8+gS7JTL._AC_SL1500_.jpg" />
      </body>
    </html>
    """

    @patch("curl_cffi.requests.get")
    def test_scrape_amazon_direct_mobile_endpoint(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = self.SAMPLE_MOBILE_HTML
        mock_get.return_value = mock_resp

        result = scrape_amazon_direct("B093GKKQ65")

        # Verify the requested URL targets the mobile-web endpoint /gp/aw/d/
        called_url = mock_get.call_args[0][0]
        self.assertIn("/gp/aw/d/B093GKKQ65", called_url)
        self.assertEqual(mock_get.call_args[1].get("impersonate"), "chrome124")

        self.assertIsNotNone(result)
        self.assertEqual(result["title"], "Space-Saving Expandable Tiered Organizer Rack")
        self.assertEqual(result["price"], "$34.99")
        self.assertEqual(result["original_price"], "$49.99")
        self.assertEqual(result["discount_percent"], 30)
        self.assertEqual(result["coupon_text"], "Save $5.00 with coupon")
        self.assertEqual(result["bought_past_month"], "50K+ bought in past month")
        self.assertEqual(result["deal_badge"], "Limited time deal")
        self.assertEqual(result["mounting_type"], "Countertop / Freestanding")
        self.assertTrue(result["is_renter_safe"])
        # Master image resolution strips ._AC_SL1500_.
        self.assertEqual(result["image_url"], "https://m.media-amazon.com/images/I/71Y8+gS7JTL.jpg")

    @patch("curl_cffi.requests.get")
    def test_fetch_product_populates_extended_models(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = self.SAMPLE_MOBILE_HTML
        mock_get.return_value = mock_resp

        product: ProductData = fetch_product("B093GKKQ65")

        self.assertIsInstance(product, ProductData)
        self.assertEqual(product.asin, "B093GKKQ65")
        self.assertEqual(product.price, "$34.99")
        self.assertEqual(product.original_price, "$49.99")
        self.assertEqual(product.discount_percent, 30)
        self.assertEqual(product.coupon_text, "Save $5.00 with coupon")
        self.assertEqual(product.bought_past_month, "50K+ bought in past month")
        self.assertEqual(product.deal_badge, "Limited time deal")
        self.assertEqual(product.mounting_type, "Countertop / Freestanding")
        self.assertTrue(product.is_renter_safe)


class TestTrendHunterDeduplicationAndBlacklist(unittest.TestCase):
    """Test B087F5K713 blacklisting and rotating fallback pool deduplication."""

    def test_blacklist_invariants(self):
        self.assertIn("B087F5K713", BLACKLISTED_ASINS)
        hunter = AITrendHunter()
        self.assertIn("B087F5K713", hunter.seen_asins)

    @patch("time.sleep")
    def test_rotating_fallback_pool_excludes_blacklisted(self, mock_sleep):
        hunter = AITrendHunter()
        # Mock search_category to return empty (forcing fallback)
        hunter.search_category = MagicMock(return_value=[])

        chosen = hunter.hunt_top_trending_product()
        self.assertIsNotNone(chosen)
        self.assertNotEqual(chosen["asin"], "B087F5K713")
        self.assertIn(chosen["asin"], [p["asin"] for p in VERIFIED_SMART_SPACES_POOL])

    def test_autopilot_marks_asin_seen_on_all_cycles(self):
        hunter = AITrendHunter()
        autopilot = AutonomousAutopilot()
        autopilot.hunter = hunter

        # Mock hunter.hunt_top_trending_product and fetch_product
        candidate = {
            "asin": "B093GKKQ65",
            "title": "Sliding Under Sink Organizer",
            "price": 24.99,
            "rating": 4.6,
            "review_count": 5000,
            "image_url": "https://m.media-amazon.com/images/I/71test.jpg",
            "viral_score": 93.0,
        }
        hunter.hunt_top_trending_product = MagicMock(return_value=candidate)
        hunter.mark_asin_seen = MagicMock()

        # Run cycle with publish_live=False
        with patch("python_engine.autonomous_autopilot.fetch_product") as mock_fetch, \
             patch("python_engine.autonomous_autopilot.generate_all_pin_variants") as mock_gen, \
             patch("python_engine.autonomous_autopilot.generate_carousel_pin_suite") as mock_suite:

            mock_prod = ProductData(
                asin="B093GKKQ65",
                title="Sliding Under Sink Organizer",
                price="$24.99",
                image_url="https://m.media-amazon.com/images/I/71test.jpg",
                affiliate_url="https://amazon.com/dp/B093GKKQ65?tag=pinforge",
                bridge_slug="sliding-under-sink-b093gkkq65",
            )
            mock_fetch.return_value = mock_prod

            mock_variant = MagicMock()
            mock_variant.image_path = "/tmp/pin_bento_dark.png"
            mock_variant.image_url = "http://localhost/pin.png"
            mock_variant.template = "bento_dark"
            mock_gen.return_value = [mock_variant]

            mock_suite.return_value = {
                "slide_paths": ["/tmp/s1.png", "/tmp/s2.png", "/tmp/s3.png", "/tmp/s4.png"],
                "composite_path": "/tmp/comp.png",
                "style": "cyber_bento",
            }

            res = autopilot.run_autopilot_cycle(publish_live=False)

            self.assertEqual(res["status"], "success")
            # Verify mark_asin_seen was called even when publish_live=False
            hunter.mark_asin_seen.assert_called_once_with(
                asin="B093GKKQ65",
                title="Sliding Under Sink Organizer",
                pin_id="",
            )


class TestGroqFirstPrioritization(unittest.TestCase):
    """Test that Groq is prioritized before Gemini in copy generation."""

    @patch("python_engine.seo_engine.generate_with_groq")
    @patch("python_engine.seo_engine.generate_with_gemini")
    def test_groq_called_before_gemini(self, mock_gemini, mock_groq):
        mock_copy = PinCopyResponse(
            pin_title="Space-Saving Hack for Small Kitchens",
            pin_description="Keep counters clutter-free with this organizer. Vote below! 👇 #AmazonAssociate",
            hashtags=["#KitchenHacks", "#AmazonAssociate"],
            board_recommendation="Space Saving Kitchens",
            call_to_action="Tap to check price",
            hook="The Clutter Solution",
            bridge_review={
                "verdict": "Great organizer",
                "pros": ["Compact", "Durable", "Fast Prime"],
                "cons": ["Limited stock"],
                "who_is_it_for": "Small apartment kitchens",
            },
        )
        mock_groq.return_value = mock_copy

        req = CopyGenerationRequest(product_title="Expandable Spice Rack")
        result = generate_pin_copy(req)

        self.assertEqual(result, mock_copy)
        mock_groq.assert_called_once()
        # Gemini should NOT be called if Groq succeeded
        mock_gemini.assert_not_called()


if __name__ == "__main__":
    unittest.main()
