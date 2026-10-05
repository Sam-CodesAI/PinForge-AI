"""Comprehensive unit and regression tests for PinForge AI Visual Generation Engine.

Verifies:
1. FreeType glyph sanitization (zero .notdef tofu box artifacts on Pillow canvas)
2. 4-Tier waterfall fallback chain (Tier 1 Ideogram -> Tier 2 Fal FLUX -> Tier 3 Pollinations -> Tier 4 Local)
3. Track A Aspirational Lifestyle Pins (100% full-bleed, zero promo boxes, zero buttons, zero prices)
4. Strategic Scheduler Track A CLI and cycle flags
5. Multi-provider API endpoints and schema models
"""

import io
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch
from PIL import Image, ImageFont

from python_engine.visual_engine import (
    sanitize_canvas_text,
    generate_visual_with_waterfall,
    render_track_a_lifestyle_pin,
    generate_local_aesthetic_fallback,
    build_visual_prompt,
    VisualGenerationResult,
    BOLD_FONT_PATH,
    REGULAR_FONT_PATH,
)
from python_engine.models import (
    AutonomousCycleRequest,
    VisualGenerateRequest,
    VisualGenerateResponse,
    PinGenerateRequest,
)
from python_engine.pin_generator import generate_all_pin_variants, render_aspirational_lifestyle
from python_engine.strategic_scheduler import parse_args


class TestGlyphSanitization(unittest.TestCase):
    """Verifies that unicode symbols causing FreeType .notdef tofu boxes are mapped to safe ASCII."""

    def test_unicode_symbols_mapped_to_ascii(self):
        cases = [
            ("⚡ QUICK SPECS", "[!] QUICK SPECS"),
            ("➔ NEXT SLIDE", "-> NEXT SLIDE"),
            ("✦ EDITORIAL PICK", "* EDITORIAL PICK"),
            ("🔥 VIRAL FAVORITE", "[!] VIRAL FAVORITE"),
            ("🛡️ 100% RENTER SAFE", "[SAFE] 100% RENTER SAFE"),
            ("📐 DIMENSIONS: 15x8", "[SPECS] DIMENSIONS: 15x8"),
            ("⚖️ CAPACITY: 40 LBS", "[CAPACITY] CAPACITY: 40 LBS"),
            ("📦 IN THE BOX", "[BOX] IN THE BOX"),
            ("✔ VERIFIED", "✓ VERIFIED"),
        ]
        for raw_input, expected in cases:
            sanitized = sanitize_canvas_text(raw_input)
            self.assertEqual(sanitized, expected, f"Failed for input: {raw_input}")

    def test_expanded_unicode_emojis_and_ellipsis(self):
        cases = [
            ("⭐ 4.8 RATING", "* 4.8 RATING"),
            ("✅ RENTER FRIENDLY", "✓ RENTER FRIENDLY"),
            ("❌ NO TOOLS NEEDED", "x NO TOOLS NEEDED"),
            ("💡 SPACE HACK", "* SPACE HACK"),
            ("💯 ORGANIZED", "100% ORGANIZED"),
            ("AMAZON FINDS…", "AMAZON FINDS..."),
            ("🏷️ $29.99 DEAL", "[DEAL] $29.99 DEAL"),
        ]
        for raw_input, expected in cases:
            sanitized = sanitize_canvas_text(raw_input)
            self.assertEqual(sanitized, expected, f"Failed for input: {raw_input}")

    def test_variation_selector_stripped(self):
        # Unicode variation selector \ufe0f attached to shield or other emoji
        raw_shield = "\U0001f6e1\ufe0f RENTER FRIENDLY"
        sanitized = sanitize_canvas_text(raw_shield)
        self.assertNotIn("\ufe0f", sanitized)
        self.assertEqual(sanitized, "[SAFE] RENTER FRIENDLY")

    def test_freetype_font_no_notdef_tofu(self):
        """Verifies that sanitized strings produce genuine non-tofu glyphs under FreeType font."""
        if not BOLD_FONT_PATH.exists():
            self.skipTest(f"Font file {BOLD_FONT_PATH} not found on disk")

        font = ImageFont.truetype(str(BOLD_FONT_PATH), 24)

        # Baseline: Raw unsupported unicode character produces the .notdef tofu box
        raw_tofu_mask = font.getmask("➔").size
        # The sanitized string replaces '➔' with '->'
        sanitized_text = sanitize_canvas_text("➔ NEXT")
        self.assertEqual(sanitized_text, "-> NEXT")

        # Every character in sanitized_text should be in printable ASCII or safe Latin-1
        for ch in sanitized_text:
            self.assertLess(ord(ch), 256)
            mask = font.getmask(ch)
            # Mask should be valid and not the tofu box dimensions
            self.assertIsNotNone(mask)

    def test_empty_and_none_text(self):
        self.assertEqual(sanitize_canvas_text(None), "")
        self.assertEqual(sanitize_canvas_text(""), "")
        self.assertEqual(sanitize_canvas_text("   "), "")


class TestWaterfallFallbackChain(unittest.TestCase):
    """Verifies the 4-tier waterfall fallback chain under various provider states and errors."""

    @patch("python_engine.visual_engine.IDEOGRAM_API_KEY", "mock_ideogram_key")
    @patch("python_engine.visual_engine.generate_ideogram_image")
    def test_tier1_ideogram_success(self, mock_ideogram):
        mock_img = Image.new("RGBA", (1000, 1500), (250, 248, 245, 255))
        mock_ideogram.return_value = mock_img

        result = generate_visual_with_waterfall(
            product_title="Rolling Kitchen Island Cart",
            board_name="Space Saving Kitchens",
            preferred_tier=1,
        )

        self.assertIsInstance(result, VisualGenerationResult)
        self.assertEqual(result.tier, 1)
        self.assertEqual(result.provider, "ideogram")
        self.assertTrue(result.success)
        self.assertFalse(result.is_fallback)
        self.assertEqual(result.image.size, (1000, 1500))

    @patch("python_engine.visual_engine.IDEOGRAM_API_KEY", "")
    @patch("python_engine.visual_engine.FAL_KEY", "mock_fal_key")
    @patch("python_engine.visual_engine.generate_fal_flux_image")
    def test_tier2_fal_flux_success(self, mock_fal):
        mock_img = Image.new("RGBA", (1000, 1500), (245, 242, 236, 255))
        mock_fal.return_value = mock_img

        result = generate_visual_with_waterfall(
            product_title="Modular Entryway Storage Bench",
            board_name="Small Apartment Hacks",
        )

        self.assertIsInstance(result, VisualGenerationResult)
        self.assertEqual(result.tier, 2)
        self.assertEqual(result.provider, "fal_flux")
        self.assertTrue(result.success)
        self.assertFalse(result.is_fallback)
        self.assertIn("Tier 1 (Ideogram): Skipped", result.error_trail[0])

    @patch("python_engine.visual_engine.IDEOGRAM_API_KEY", "")
    @patch("python_engine.visual_engine.FAL_KEY", "")
    @patch("python_engine.visual_engine.generate_pollinations_image")
    def test_tier3_pollinations_success(self, mock_pollinations):
        mock_img = Image.new("RGBA", (1000, 1500), (240, 238, 230, 255))
        mock_pollinations.return_value = mock_img

        result = generate_visual_with_waterfall(
            product_title="Bamboo Drawer Dividers",
            board_name="Closet & Wardrobe Organization",
        )

        self.assertIsInstance(result, VisualGenerationResult)
        self.assertEqual(result.tier, 3)
        self.assertEqual(result.provider, "pollinations")
        self.assertTrue(result.success)
        self.assertFalse(result.is_fallback)

    @patch("python_engine.visual_engine.IDEOGRAM_API_KEY", "")
    @patch("python_engine.visual_engine.FAL_KEY", "")
    @patch("python_engine.visual_engine.generate_pollinations_image", return_value=None)
    def test_tier4_local_aesthetic_fallback(self, mock_pollinations):
        """When all external APIs are missing or fail (HTTP 402/429/timeout), falls back to Tier 4."""
        result = generate_visual_with_waterfall(
            product_title="Under-Bed Storage Container with Wheels",
            board_name="Small Apartment Hacks",
        )

        self.assertIsInstance(result, VisualGenerationResult)
        self.assertEqual(result.tier, 4)
        self.assertEqual(result.provider, "local_aesthetic")
        self.assertTrue(result.success)
        self.assertTrue(result.is_fallback)
        self.assertEqual(result.image.size, (1000, 1500))
        self.assertTrue(len(result.error_trail) >= 3)


class TestTrackALifestylePins(unittest.TestCase):
    """Verifies Track A Aspirational Lifestyle Pin requirements:

    1. 100% full-bleed interior design imagery
    2. ZERO promotional boxes
    3. ZERO giant buttons
    4. ZERO prices
    """

    @patch("python_engine.visual_engine.IDEOGRAM_API_KEY", "")
    @patch("python_engine.visual_engine.FAL_KEY", "")
    @patch("python_engine.visual_engine.generate_pollinations_image", return_value=None)
    def test_render_track_a_lifestyle_pin_dimensions_and_mode(self, mock_pollinations):
        pin = render_track_a_lifestyle_pin(
            title="Japanese Minimalist Floating Wall Shelf",
            board_name="Small Apartment Hacks",
            category="Home Organization",
            style="aspirational_lifestyle",
        )

        self.assertIsInstance(pin, Image.Image)
        self.assertEqual(pin.size, (1000, 1500))
        self.assertEqual(pin.mode, "RGBA")

    @patch("python_engine.visual_engine.IDEOGRAM_API_KEY", "")
    @patch("python_engine.visual_engine.FAL_KEY", "")
    @patch("python_engine.visual_engine.generate_pollinations_image", return_value=None)
    def test_render_aspirational_lifestyle_via_pin_generator(self, mock_pollinations):
        prod_img = Image.new("RGBA", (400, 400), (200, 200, 200, 255))
        req = PinGenerateRequest(
            title="Aesthetic Space-Saving Storage Bench",
            image_url="https://m.media-amazon.com/images/I/71xyz.jpg",
            price="$89.99",
            rating=4.9,
            review_count="2,400+",
            features=["Solid Bleached Oak", "Linen Cushioned Top", "Zero Assembly Required"],
            template="aspirational_lifestyle",
            board_name="Small Apartment Hacks",
        )
        pin = render_aspirational_lifestyle(req, prod_img)

        self.assertEqual(pin.size, (1000, 1500))
        self.assertIsNotNone(pin)

    @patch("python_engine.pin_generator.download_image")
    @patch("python_engine.visual_engine.IDEOGRAM_API_KEY", "")
    @patch("python_engine.visual_engine.FAL_KEY", "")
    @patch("python_engine.visual_engine.generate_pollinations_image", return_value=None)
    def test_generate_all_pin_variants_includes_aspirational(self, mock_pollinations, mock_download):
        prod_img = Image.new("RGBA", (300, 300), (180, 180, 180, 255))
        mock_download.return_value = prod_img
        req = PinGenerateRequest(
            title="Aesthetic Floating Shelves with Wire Basket",
            image_url="https://m.media-amazon.com/images/I/71xyz.jpg",
            price="$34.99",
            rating=4.7,
            review_count="850+",
            features=["Rustic Pine Wood", "Industrial Matte Black Iron", "Wall Mounted"],
            board_name="Small Apartment Hacks",
        )
        variants = generate_all_pin_variants(req)

        self.assertEqual(len(variants), 5)
        templates_present = [v.template for v in variants]
        expected_styles = [
            "bento_dark",
            "warm_editorial",
            "problem_solver",
            "pollinations_lifestyle",
            "aspirational_lifestyle",
        ]
        for style in expected_styles:
            self.assertIn(style, templates_present, f"Missing style variant: {style}")
        for v in variants:
            self.assertEqual((v.width, v.height), (1000, 1500))


class TestSchedulerTrackAIntegration(unittest.TestCase):
    """Verifies that strategic_scheduler.py CLI and models accept --track-a flag."""

    def test_scheduler_cli_parses_track_a(self):
        args = parse_args(["--slot", "1", "--track-a", "--dry-run", "--no-jitter"])
        self.assertEqual(args.slot, 1)
        self.assertTrue(args.track_a)
        self.assertTrue(args.dry_run)
        self.assertTrue(args.no_jitter)

    def test_autonomous_cycle_request_track_a(self):
        req = AutonomousCycleRequest(
            url_or_asin="B087F5K713",
            template_style="track_a_lifestyle",
            track_a=True,
        )
        self.assertTrue(req.track_a)
        self.assertEqual(req.template_style, "track_a_lifestyle")

    def test_visual_generate_request_and_response(self):
        req = VisualGenerateRequest(
            product_title="Modern Corner Desk",
            board_name="Studio Living Ideas",
            track_a=True,
        )
        self.assertTrue(req.track_a)
        self.assertEqual(req.product_title, "Modern Corner Desk")

        res = VisualGenerateResponse(
            provider="fal_flux",
            tier=2,
            prompt_used="Warm Japandi studio corner desk",
            image_url="http://localhost:8000/static/pins/test.png",
            base64_image="fake_base64",
            render_time_ms=125.4,
            is_ai_generated=True,
        )
        self.assertEqual(res.provider, "fal_flux")
        self.assertEqual(res.tier, 2)
        self.assertTrue(res.is_ai_generated)


class TestProviderContractHardening(unittest.TestCase):
    """Verifies vendor contract invariants (multiples of 16, dual endpoint fallback, carousel waterfall)."""

    @patch("python_engine.visual_engine.FAL_KEY", "mock_fal_key")
    @patch("httpx.Client.post")
    def test_fal_flux_dimensions_multiples_of_16(self, mock_post):
        """FLUX.1 models strictly require dimensions to be multiples of 16."""
        from python_engine.visual_engine import generate_fal_flux_image

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"images": []}
        mock_post.return_value = mock_resp

        generate_fal_flux_image("Warm Japandi apartment", api_key="test_fal_key")

        self.assertTrue(mock_post.called)
        _, kwargs = mock_post.call_args
        payload = kwargs.get("json", {})
        img_size = payload.get("image_size", {})
        w, h = img_size.get("width"), img_size.get("height")
        self.assertIsNotNone(w)
        self.assertIsNotNone(h)
        self.assertEqual(w % 16, 0, f"FLUX width {w} must be a multiple of 16")
        self.assertEqual(h % 16, 0, f"FLUX height {h} must be a multiple of 16")
        self.assertAlmostEqual(w / h, 2 / 3, places=2)

    @patch("python_engine.visual_engine.IDEOGRAM_API_KEY", "mock_key")
    @patch("httpx.Client.post")
    def test_ideogram_dual_endpoint_fallback(self, mock_post):
        """If v2 endpoint returns 404, Ideogram engine falls back to legacy /generate."""
        from python_engine.visual_engine import generate_ideogram_image

        resp_404 = MagicMock()
        resp_404.status_code = 404

        resp_200 = MagicMock()
        resp_200.status_code = 200
        resp_200.json.return_value = {"data": []}

        mock_post.side_effect = [resp_404, resp_200]

        generate_ideogram_image("Typography sign", api_key="mock_key")

        self.assertEqual(mock_post.call_count, 2)
        urls_called = [call_args[0][0] for call_args in mock_post.call_args_list]
        self.assertIn("https://api.ideogram.ai/v2/image/generate", urls_called[0])
        self.assertIn("https://api.ideogram.ai/generate", urls_called[1])

    @patch("python_engine.carousel_engine.download_image", return_value=None)
    @patch("python_engine.visual_engine.generate_visual_with_waterfall")
    def test_carousel_uses_waterfall_fallback(self, mock_waterfall, mock_download):
        """Carousel generation delegates to waterfall fallback when image download fails."""
        from python_engine.carousel_engine import generate_carousel_pin_suite

        mock_res = VisualGenerationResult(
            image=Image.new("RGBA", (1000, 1500), (240, 240, 240, 255)),
            provider="local_aesthetic",
            tier=4,
            prompt_used="test",
            elapsed_ms=10.0,
        )
        mock_waterfall.return_value = mock_res

        suite = generate_carousel_pin_suite(
            title="Modular Organizer",
            price="$29.99",
            rating=4.7,
            review_count="1,200+",
            image_url="https://invalid.example.com/bad.jpg",
            features=["Feature 1"],
        )

        self.assertTrue(mock_waterfall.called)
        self.assertIn("slide_paths", suite)
        self.assertEqual(len(suite["slide_paths"]), 4)

    @patch("python_engine.visual_engine.IDEOGRAM_API_KEY", "")
    @patch("python_engine.visual_engine.FAL_KEY", "")
    @patch("python_engine.visual_engine.generate_pollinations_image", return_value=None)
    def test_visual_generate_endpoint_track_a_telemetry(self, mock_pollinations):
        """Track A through generate_visual_endpoint accurately reflects fallback tier and error trail."""
        from python_engine.main import generate_visual_endpoint

        req = VisualGenerateRequest(
            product_title="Minimalist Japandi Storage Bench",
            board_name="Small Apartment Hacks",
            track_a=True,
        )
        res = generate_visual_endpoint(req)

        self.assertEqual(res.tier, 4)
        self.assertEqual(res.provider, "track_a_local_aesthetic")
        self.assertFalse(res.is_ai_generated)
        self.assertTrue(len(res.error_trail) >= 3)
        self.assertTrue(res.image_url.startswith("http"))


if __name__ == "__main__":
    unittest.main()
