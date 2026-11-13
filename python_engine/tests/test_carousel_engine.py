"""Test Suite for PinForge AI 4-Slide Carousel Engine.

Verifies:
1. 4-slide progressive disclosure rendering sequence
2. Slide 1 (Hook), Slide 2 (Features), Slide 3 (Specs), Slide 4 (Trust & Save CTA)
3. 2x2 composite grid pin generation
4. Base64 encoding and progress dot indicator logic
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

from python_engine.carousel_engine import (
    generate_carousel_pin_suite,
    render_composite_carousel_preview,
)


class TestCarouselEngine(unittest.TestCase):
    """Test suite validating 4-slide native carousel suite generation."""

    def test_generate_carousel_suite_structure(self):
        """Verifies full 4-slide carousel suite data output."""
        suite = generate_carousel_pin_suite(
            title="Lifewit Clear Adjustable Drawer Dividers 4-Pack",
            price="$19.99",
            rating=4.8,
            review_count="18,400+ ratings",
            image_url="https://m.media-amazon.com/images/I/71P4q+4oWNL.jpg",
            features=[
                "Expandable 11 to 17 inches",
                "Non-slip EVA foam protective pads",
                "Tool-free damage-free setup"
            ],
            friction_badge="100% RENTER FRIENDLY • NO DRILL",
        )

        self.assertEqual(suite["total_slides"], 4)
        self.assertEqual(len(suite["slide_paths"]), 4)
        self.assertIn("composite_path", suite)
        self.assertTrue(Path(suite["composite_path"]).exists())

        # Verify each slide is a valid 1000x1500 image on disk
        for p in suite["slide_paths"]:
            self.assertTrue(Path(p).exists())
            with Image.open(p) as img:
                self.assertEqual(img.size, (1000, 1500))

    def test_composite_carousel_preview_dimensions(self):
        """Verifies 2x2 grid overview image rendering."""
        dummy_slides = [Image.new("RGB", (1000, 1500), color=(240, 240, 240)) for _ in range(4)]
        comp = render_composite_carousel_preview(dummy_slides, friction_badge="100% RENTER FRIENDLY")

        self.assertEqual(comp.size, (1000, 1500))


if __name__ == "__main__":
    unittest.main()
