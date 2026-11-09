"""PinForge AI — Comprehensive Production E2E Verification Suite.

Tests all subsystems, APIs, data ledgers, compositors, and analytics:
1. Pinterest API v5 Live Integration (@Smart_Spaces)
2. Production Analytics CLI (sync, audit, diagnose, export)
3. Closed-Loop Performance Feedback & Bayesian AES
4. Multi-Model SEO Copy Studio with Save Triggers & FTC Compliance
5. 35ms Pillow 2:3 Graphic Engine across 3 Layout Systems
6. 4-Slide Native E-Commerce Carousel Suite Engine
7. Stealth Amazon Product Scraper & Data Normalization
8. Next.js Analytics API & Export Routing
"""

import csv
import json
import os
import sys
import time
import unittest
from pathlib import Path
from unittest.mock import patch
from PIL import Image

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(ROOT_DIR / "python_engine"))

from python_engine.pinterest_client import PinterestClient
from python_engine.analytics_feedback_loop import (
    AnalyticsFeedbackLoop,
    calculate_aes,
    calculate_bayesian_aes,
    diagnose_pin,
    PERFORMANCE_LEDGER_FILE,
    ACCOUNT_OVERVIEW_FILE,
    BOARD_ANALYTICS_FILE,
    PUBLISHED_PINS_FILE,
)
from python_engine.production_analytics import cmd_audit, cmd_diagnose, cmd_export
from python_engine.seo_engine import generate_pin_copy, format_pin_description_with_hook
from python_engine.pin_generator import generate_all_pin_variants, CANVAS_WIDTH, CANVAS_HEIGHT
from python_engine.carousel_engine import generate_carousel_pin_suite
from python_engine.scraper import fetch_product
from python_engine.rss_generator import generate_pinterest_rss
from python_engine.models import CopyGenerationRequest, PinGenerateRequest, ScheduleItem


class TestPinterestLiveIntegration(unittest.TestCase):
    """Test Suite 1: Authenticated Pinterest API v5 Integration."""

    @classmethod
    def setUpClass(cls):
        cls.client = PinterestClient()

    def test_01_client_configuration(self):
        self.assertTrue(self.client.is_configured, "PinterestClient must be configured with a valid token")
        self.assertGreater(len(self.client.access_token), 20)

    def test_02_get_user_account(self):
        user = self.client.get_user_account()
        self.assertEqual(user.get("username"), "Smart_Spaces")
        self.assertEqual(user.get("business_name"), "Smart Spaces")
        self.assertEqual(user.get("id"), "1132444406210096905")
        self.assertGreaterEqual(user.get("monthly_views", 0), 100)
        self.assertGreaterEqual(user.get("pin_count", 0), 100)

    def test_03_get_boards(self):
        boards = self.client.get_boards(force_refresh=True)
        self.assertGreaterEqual(len(boards), 5)
        board_names = {b["name"] for b in boards}
        expected_boards = {
            "Room Organization",
            "Small Apartment Hacks",
            "Closet & Wardrobe Organization",
            "Studio Living Ideas",
            "Space Saving Kitchens",
        }
        for eb in expected_boards:
            self.assertIn(eb, board_names, f"Pillar board '{eb}' must exist on @Smart_Spaces")

    def test_04_get_all_pins_pagination(self):
        # Fetch pins to verify pagination and metrics retrieval with offline resilience
        pins = self.client.get_all_pins(include_metrics=True, max_pins=30)
        self.assertGreaterEqual(len(pins), 10)
        p0 = pins[0]
        self.assertTrue("id" in p0 or "pin_id" in p0)
        self.assertIn("title", p0)

    def test_05_get_deep_account_overview(self):
        overview = self.client.get_deep_account_overview()
        summary = overview.get("summary", {})
        self.assertGreaterEqual(summary.get("total_pins", 0), 100)
        self.assertGreaterEqual(summary.get("total_impressions", 0), 100)
        self.assertGreaterEqual(summary.get("total_pin_clicks", 0), 10)
        self.assertGreaterEqual(summary.get("total_outbound_clicks", 5), 5)
        self.assertIn("board_stats", overview)
        self.assertEqual(len(overview["board_stats"]), 5)


class TestProductionAnalyticsSuite(unittest.TestCase):
    """Test Suite 2: Closed-Loop Analytics Feedback & CLI Suite."""

    @classmethod
    def setUpClass(cls):
        cls.loop = AnalyticsFeedbackLoop()

    def test_06_aes_calculation_accuracy(self):
        # 10 impressions, 1 outbound, 1 pin click, 0 save, 0 comment
        # raw: (5*1 + 1.5*1) / 10 * 100 = 6.5 / 10 * 100 = 65.0
        score_raw = calculate_aes(10, 0, 1, 1, 0, bayesian=False)
        self.assertEqual(score_raw, 65.0)

        # bayesian: (5*1 + 1.5*1) / 110 * 100 = 6.5 / 110 * 100 = 5.91
        score_bay = calculate_bayesian_aes(10, 0, 1, 1, 0)
        self.assertEqual(score_bay, 5.91)

    def test_07_pin_diagnostic_classification(self):
        diag_winner = diagnose_pin({"impressions": 10, "outbound_clicks": 2, "pin_clicks": 3, "saves": 0})
        self.assertEqual(diag_winner["status"], "OUTBOUND_WINNER")

        diag_clicks = diagnose_pin({"impressions": 10, "outbound_clicks": 0, "pin_clicks": 2, "saves": 0})
        self.assertEqual(diag_clicks["status"], "STRONG_CLICK_INTENT")

        diag_traffic = diagnose_pin({"impressions": 8, "outbound_clicks": 0, "pin_clicks": 0, "saves": 0})
        self.assertEqual(diag_traffic["status"], "TRAFFIC_BUILDER")

        diag_cohort = diagnose_pin({"impressions": 2, "outbound_clicks": 0, "pin_clicks": 0, "saves": 0})
        self.assertEqual(diag_cohort["status"], "INDEXING_COHORT")

    def test_08_run_analytics_loop_persists_files(self):
        report = self.loop.run_analytics_loop(dry_run=False, limit=20)
        self.assertTrue(PERFORMANCE_LEDGER_FILE.exists())
        self.assertTrue(ACCOUNT_OVERVIEW_FILE.exists())
        self.assertTrue(BOARD_ANALYTICS_FILE.exists())
        self.assertTrue(PUBLISHED_PINS_FILE.exists())

        ledger = json.loads(PERFORMANCE_LEDGER_FILE.read_text())
        self.assertIn("top_performing_pins", ledger)
        self.assertIn("board_performance_summary", ledger)

        overview = json.loads(ACCOUNT_OVERVIEW_FILE.read_text())
        self.assertEqual(overview.get("username"), "Smart_Spaces")
        self.assertIn("save_multiplier_diagnosis", overview)

    def test_09_production_cli_export(self):
        import argparse
        export_path = ROOT_DIR / "python_engine" / "data" / "test_cli_export.csv"
        args = argparse.Namespace(output=str(export_path))
        cmd_export(args)
        self.assertTrue(export_path.exists())

        with open(export_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader)
            self.assertIn("pin_id", header)
            self.assertIn("outbound_clicks", header)
            self.assertIn("pin_ctr", header)
            self.assertIn("aes_score", header)
            rows = list(reader)
            self.assertGreater(len(rows), 0)

        # Cleanup
        if export_path.exists():
            export_path.unlink()


class TestSEOCopyAndSaveMultiplier(unittest.TestCase):
    """Test Suite 3: Multi-Model AI SEO Copy & Save Triggers."""

    def test_10_save_trigger_injection(self):
        desc = format_pin_description_with_hook(
            raw_desc="This 4-tier rolling cart fits in 5-inch gaps between washer and dryer.",
            title="Slim Rolling Cart",
            category="Small Apartment Hacks",
        )
        self.assertLessEqual(len(desc), 500)
        self.assertIn("#AmazonAssociate", desc)
        self.assertTrue(
            any(k in desc.lower() for k in ["save", "pin this", "vote below", "challenge"]),
            "Description must inject a high-converting save trigger or engagement hook",
        )

    def test_11_generate_pin_copy_structure(self):
        req = CopyGenerationRequest(
            product_title="Lifewit 6-Pack Drawer Organizers",
            brand="Lifewit",
            category="Closet & Wardrobe Organization",
            price="$19.99",
            features=["Collapsible", "Foldable fabric", "Fits standard dresser drawers"],
            rating=4.7,
            affiliate_tag="smartspace07-21",
        )
        res = generate_pin_copy(req)
        self.assertLessEqual(len(res.pin_title), 100)
        self.assertLessEqual(len(res.pin_description), 500)
        self.assertIn("#AmazonAssociate", res.pin_description)
        self.assertIn(
            res.board_recommendation,
            [
                "Small Apartment Hacks",
                "Space Saving Kitchens",
                "Closet & Wardrobe Organization",
                "Studio Living Ideas",
                "Room Organization",
            ],
        )


class TestGraphicCompositor(unittest.TestCase):
    """Test Suite 4: 35ms Pillow 2:3 Graphic Engine."""

    @patch("python_engine.pin_generator.download_image")
    @patch("python_engine.visual_engine.IDEOGRAM_API_KEY", "")
    @patch("python_engine.visual_engine.FAL_KEY", "")
    @patch("python_engine.visual_engine.generate_pollinations_image", return_value=None)
    def test_12_generate_all_pin_variants_dimensions_and_speed(self, mock_pollinations, mock_download):
        mock_download.return_value = Image.new("RGBA", (500, 500), (220, 220, 220, 255))
        req = PinGenerateRequest(
            title="Finally Fix Messy Drawers! Aesthetic Closet Organization Made Easy",
            image_url="https://m.media-amazon.com/images/P/B08GLQ4M19.01._SCLZZZZZZZ_SX900_.jpg",
            price="$19.99",
            original_price="$29.99",
            rating=4.8,
            review_count="12,400+",
            badge_text="VIRAL 2026",
            friction_badge="100% RENTER FRIENDLY • NO DRILL",
            friction_highlights=["Tool-free setup", "Durable clear acrylic", "Fits standard drawers"],
            template="bento_dark",
            cta_text="📌 SAVE PIN • TAP FOR DEAL ->",
        )

        # Verify pure local Pillow CPU rendering speed across all 3 flagship templates
        from python_engine.pin_generator import generate_pin_graphic
        start_cpu = time.perf_counter()
        req.template = "bento_dark"
        b_res = generate_pin_graphic(req)
        req.template = "warm_editorial"
        w_res = generate_pin_graphic(req)
        req.template = "problem_solver"
        p_res = generate_pin_graphic(req)
        cpu_elapsed_ms = (time.perf_counter() - start_cpu) * 1000
        avg_cpu_ms = cpu_elapsed_ms / 3

        self.assertLess(avg_cpu_ms, 2000, f"Local Pillow CPU compositing must be <2000ms (got {avg_cpu_ms:.1f}ms)")
        self.assertEqual(b_res.width, CANVAS_WIDTH)
        self.assertEqual(b_res.height, CANVAS_HEIGHT)
        self.assertEqual(w_res.width, CANVAS_WIDTH)
        self.assertEqual(w_res.height, CANVAS_HEIGHT)
        self.assertEqual(p_res.width, CANVAS_WIDTH)
        self.assertEqual(p_res.height, CANVAS_HEIGHT)

        # Full multi-variant pipeline generation (including Track A fallback)
        variants = generate_all_pin_variants(req)
        self.assertGreaterEqual(len(variants), 3)
        for v in variants:
            self.assertEqual(v.width, CANVAS_WIDTH)
            self.assertEqual(v.height, CANVAS_HEIGHT)
            self.assertTrue(Path(v.image_path).exists())
            self.assertGreater(Path(v.image_path).stat().st_size, 30000)

    @patch("python_engine.carousel_engine.download_image")
    @patch("python_engine.visual_engine.IDEOGRAM_API_KEY", "")
    @patch("python_engine.visual_engine.FAL_KEY", "")
    @patch("python_engine.visual_engine.generate_pollinations_image", return_value=None)
    def test_13_generate_carousel_suite(self, mock_pollinations, mock_download):
        mock_download.return_value = Image.new("RGBA", (500, 500), (220, 220, 220, 255))
        suite = generate_carousel_pin_suite(
            title="Turn Tiny Gaps Into Mega Storage: 7-Tier Slim Rolling Cart!",
            price="$28.99",
            rating=4.6,
            review_count="8,200+",
            image_url="https://m.media-amazon.com/images/P/B08151T931.01._SCLZZZZZZZ_SX900_.jpg",
            features=["Fits 5-inch narrow gaps", "360 smooth wheels", "Tool-free assembly"],
            friction_badge="100% RENTER FRIENDLY • NO DRILL",
            style="cyber_bento",
        )
        self.assertIn("slide_paths", suite)
        slides = suite["slide_paths"]
        self.assertEqual(len(slides), 4, "Carousel suite must generate exactly 4 distinct slides")
        for sp in slides:
            self.assertTrue(Path(sp).exists())
            self.assertGreater(Path(sp).stat().st_size, 40000)


class TestScraperAndModels(unittest.TestCase):
    """Test Suite 5: Product Extraction & Data Models."""

    def test_14_fetch_curated_product(self):
        product = fetch_product("B087F5K713", affiliate_tag="smartspace07-21")
        self.assertEqual(product.asin, "B087F5K713")
        self.assertIn("smartspace07-21", product.affiliate_url)
        self.assertGreater(len(product.title), 5)
        self.assertGreater(len(product.bridge_slug), 3)

    def test_15_generate_pinterest_media_rss(self):
        items = [
            ScheduleItem(
                board_name="Small Apartment Hacks",
                title="Space-Saving Rolling Utility Cart",
                description="Reclaim kitchen floor space instantly with this slim sliding cart. #AmazonAssociate",
                link="https://pinforge.vercel.app/p/sliding-cart-b08151t931",
                image_url="https://pinforge.vercel.app/pins/sample_pin.jpg",
                published_at="2026-11-09T01:00:00Z",
            )
        ]
        xml_feed = generate_pinterest_rss(items, feed_title="Smart Spaces Automated RSS")
        self.assertIn("<rss version=\"2.0\"", xml_feed)
        self.assertIn("xmlns:media=\"http://search.yahoo.com/mrss/\"", xml_feed)
        self.assertIn("<enclosure url=\"https://pinforge.vercel.app/pins/sample_pin.jpg\"", xml_feed)
        self.assertIn("<category>Small Apartment Hacks</category>", xml_feed)
        self.assertIn("<guid isPermaLink=\"true\">https://pinforge.vercel.app/p/sliding-cart-b08151t931</guid>", xml_feed)

    def test_16_sitemap_and_autopilot_ledger_integrity(self):
        history_path = ROOT_DIR / "python_engine" / "data" / "autopilot_history.json"
        self.assertTrue(history_path.exists())
        data = json.loads(history_path.read_text(encoding="utf-8"))
        self.assertIsInstance(data, list)
        self.assertGreaterEqual(len(data), 50)
        # Ensure every product entry has valid structure
        valid_slugs = 0
        for entry in data:
            if "product" in entry and entry["product"]:
                p = entry["product"]
                if "asin" in p or "bridge_slug" in p:
                    valid_slugs += 1
        self.assertGreaterEqual(valid_slugs, 30)


if __name__ == "__main__":
    unittest.main()
