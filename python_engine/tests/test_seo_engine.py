"""Test Suite for PinForge AI SEO Engine.

Verifies:
1. High-AES title synthesis and curiosity-hook formulation
2. Mandatory Save-First copy trigger inclusion
3. #AmazonAssociate compliance disclosure enforcement
4. 5-pillar board recommendation accuracy
"""

import sys
import unittest
from pathlib import Path

# Add project root to sys.path
CURRENT_DIR = Path(__file__).resolve().parent
PYTHON_ENGINE_DIR = CURRENT_DIR.parent
PROJECT_ROOT = PYTHON_ENGINE_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(PYTHON_ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHON_ENGINE_DIR))

from python_engine.seo_engine import (
    generate_pin_copy,
    select_official_board,
    load_high_aes_winning_titles,
)
from python_engine.models import CopyGenerationRequest


class TestSeoEngine(unittest.TestCase):
    """Test suite validating SEO copy synthesis and compliance triggers."""

    def test_board_recommendations(self):
        """Verifies correct board classification across the 5 Smart Spaces pillars."""
        cases = [
            ("Lifewit Drawer Dividers Clothes Storage", "Room Organization", "Room Organization"),
            ("Small Space Apartment Wall Folding Desk", "Small Apartment Hacks", "Small Apartment Hacks"),
            ("Studio Living Divider Screen with Shelves", "Studio Living Ideas", "Studio Living Ideas"),
            ("2-Tier Under Sink Sliding Rack", "Space Saving Kitchens", "Space Saving Kitchens"),
            ("Stackable Clear Shoe Organizer Box", "Closet & Wardrobe Organization", "Closet & Wardrobe Organization"),
        ]
        for title, cat, expected in cases:
            with self.subTest(title=title):
                rec = select_official_board(cat, title)
                self.assertEqual(rec, expected)

    def test_generate_hashtags_and_compliance(self):
        """Verifies hashtag generation with mandatory #AmazonAssociate disclosure."""
        req = CopyGenerationRequest(
            product_title="2-Tier Under Sink Sliding Rack",
            category="Space Saving Kitchens",
            price="$24.99",
            features=["Slide out drawer", "Rust-proof"],
        )
        res = generate_pin_copy(req)
        self.assertGreaterEqual(len(res.hashtags), 3)
        self.assertIn("#AmazonAssociate", res.hashtags)
        for tag in res.hashtags:
            self.assertTrue(tag.startswith("#"))

    def test_generate_pin_copy_save_first_contract(self):
        """Verifies that generated copy strictly contains the Save-First trigger and FTC disclosure."""
        req = CopyGenerationRequest(
            product_title="Lifewit Adjustable Acrylic Drawer Dividers 4-Pack",
            brand="Lifewit",
            category="Room Organization",
            price="$19.99",
            features=[
                "Expandable 11 to 17 inches",
                "Strong spring-loaded tension",
                "Crystal-clear transparent design"
            ],
            rating=4.8,
            affiliate_tag="smartspace07-21"
        )
        res = generate_pin_copy(req)

        self.assertIsNotNone(res.pin_title)
        self.assertLessEqual(len(res.pin_title), 100)
        self.assertIn("SAVE THIS PIN", res.pin_description.upper())
        self.assertIn("#AMAZONASSOCIATE", res.pin_description.upper())
        self.assertEqual(res.board_recommendation, "Room Organization")

    def test_winning_titles_pool(self):
        """Verifies winning titles pool contains verified problem-solver hooks without tech items."""
        titles = load_high_aes_winning_titles()
        self.assertGreater(len(titles), 5)
        for t in titles:
            self.assertFalse(any(bad in t.lower() for bad in ["cable", "charger", "earbuds", "phone stand"]))


if __name__ == "__main__":
    unittest.main()
