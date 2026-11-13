"""Test Suite for PinForge AI Graphic Generator.

Verifies:
1. 1000x1500 canvas resolution (2:3 Pinterest standard)
2. Unicode emoji and arrow sanitization
3. Smart Spaces brand color token enforcement
4. Multi-template generation (warm_editorial, problem_solver)
"""

import sys
import unittest
from pathlib import Path
from PIL import Image

# Add project root to sys.path
CURRENT_DIR = Path(__file__).resolve().parent
PYTHON_ENGINE_DIR = CURRENT_DIR.parent
PROJECT_ROOT = PYTHON_ENGINE_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(PYTHON_ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHON_ENGINE_DIR))

from python_engine.pin_generator import (
    sanitize_canvas_text,
    hex_to_rgb,
    generate_pin_graphic,
    CANVAS_WIDTH,
    CANVAS_HEIGHT,
)
from python_engine.models import PinGenerateRequest, SMART_SPACES_BRAND


class TestPinGenerator(unittest.TestCase):
    """Test suite validating canvas layout, font sanitization, and template rendering."""

    def test_canvas_dimensions(self):
        """Verifies standard 1000x1500 resolution."""
        self.assertEqual(CANVAS_WIDTH, 1000)
        self.assertEqual(CANVAS_HEIGHT, 1500)

    def test_sanitize_canvas_text(self):
        """Verifies non-standard emojis and arrows are safely converted without tofu box artifacts."""
        raw = "🔥 Top Deal ➔ 100% Renter Friendly ⭐⭐⭐⭐⭐"
        sanitized = sanitize_canvas_text(raw)
        self.assertNotIn("🔥", sanitized)
        self.assertNotIn("➔", sanitized)
        self.assertIn("->", sanitized)
        self.assertIn("[!]", sanitized)

    def test_hex_to_rgb(self):
        """Verifies hex string to RGB tuple conversion."""
        self.assertEqual(hex_to_rgb("#F9F6F0", (0, 0, 0)), (249, 246, 240))
        self.assertEqual(hex_to_rgb("#D97706", (0, 0, 0)), (217, 119, 6))
        self.assertEqual(hex_to_rgb(None, (10, 20, 30)), (10, 20, 30))

    def test_generate_warm_editorial_graphic(self):
        """Verifies end-to-end rendering of Warm Editorial template."""
        req = PinGenerateRequest(
            asin="B0DHGM5XT4",
            title="Lifewit Adjustable Acrylic Drawer Dividers 4-Pack",
            price="$19.99",
            original_price="$25.99",
            rating=4.8,
            review_count="18,400+ ratings",
            image_url="https://m.media-amazon.com/images/I/71P4q+4oWNL.jpg",
            category="Room Organization",
            board_name="Room Organization",
            features=[
                "Expandable 11 to 17 inches fits any drawer",
                "Strong spring-loaded tension mechanism",
                "Crystal-clear acrylic transparent finish"
            ],
            friction_badge="100% RENTER FRIENDLY • NO DRILL",
            cta_text="📌 SAVE THIS PIN • TAP FOR FULL GUIDE ->",
            primary_hex=SMART_SPACES_BRAND.primary_hex,
            accent_hex=SMART_SPACES_BRAND.accent_hex,
            template="warm_editorial",
        )
        res = generate_pin_graphic(req)

        self.assertEqual(res.width, 1000)
        self.assertEqual(res.height, 1500)
        self.assertEqual(res.template, "warm_editorial")
        self.assertTrue(Path(res.image_path).exists())

        # Verify pixel dimensions on disk
        with Image.open(res.image_path) as img:
            self.assertEqual(img.size, (1000, 1500))

    def test_generate_problem_solver_graphic(self):
        """Verifies end-to-end rendering of Problem Solver template."""
        req = PinGenerateRequest(
            asin="B0C42YJVCD",
            title="360 Rotating Makeup Organizer Vanity Storage Carousel",
            price="$23.99",
            rating=4.7,
            image_url="https://m.media-amazon.com/images/I/71+2Z-1mK7L.jpg",
            category="Room Organization",
            board_name="Room Organization",
            features=[
                "Smooth 360-degree silent spinning base",
                "7 adjustable multi-level trays",
                "Reclaims 70% of bathroom vanity countertop"
            ],
            friction_badge="ZERO WALL HOLES",
            cta_text="📌 SAVE THIS PIN • TAP FOR FULL GUIDE ->",
            template="problem_solver",
        )
        res = generate_pin_graphic(req)
        self.assertEqual(res.width, 1000)
        self.assertEqual(res.height, 1500)
        self.assertTrue(Path(res.image_path).exists())


if __name__ == "__main__":
    unittest.main()
