"""Test Suite for PinForge AI Scraper Module.

Verifies:
1. Robust ASIN extraction across URLs and raw strings
2. Price normalization and currency formatting
3. Verified Smart Spaces catalog retrieval
4. Affiliate tag parameter injection
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

from python_engine.scraper import (
    extract_asin,
    format_usd_price,
    fetch_product,
    VERIFIED_CATALOG,
)


class TestScraper(unittest.TestCase):
    """Test suite validating Amazon extraction and price normalization."""

    def test_extract_asin_direct_and_whitespace(self):
        """Verifies extracting 10-char ASIN directly or with whitespace/case variation."""
        self.assertEqual(extract_asin("B0DHGM5XT4"), "B0DHGM5XT4")
        self.assertEqual(extract_asin("  b0c42yjvcd  "), "B0C42YJVCD")
        self.assertEqual(extract_asin("B093GKKQ65"), "B093GKKQ65")
        self.assertIsNone(extract_asin("not-an-asin"))

    def test_extract_asin_from_amazon_urls(self):
        """Verifies extracting ASIN from standard, short, and referral Amazon URLs."""
        urls = [
            ("https://www.amazon.com/dp/B0DHGM5XT4?ref=nb_sb_noss", "B0DHGM5XT4"),
            ("https://www.amazon.com/Lifewit-Adjustable-Dividers/dp/B0DHGM5XT4/", "B0DHGM5XT4"),
            ("https://www.amazon.com/gp/product/B0C42YJVCD?th=1", "B0C42YJVCD"),
            ("https://amazon.com/exec/obidos/ASIN/B093GKKQ65/ref=nosim", "B093GKKQ65"),
            ("http://amzn.to/dp/B08332N66L", "B08332N66L"),
        ]
        for url, expected in urls:
            with self.subTest(url=url):
                self.assertEqual(extract_asin(url), expected)

    def test_format_usd_price(self):
        """Verifies price sanitization and currency representation."""
        self.assertEqual(format_usd_price(19.99), "$19.99")
        self.assertEqual(format_usd_price("24.99"), "$24.99")
        self.assertEqual(format_usd_price("$35.00"), "$35.00")
        self.assertEqual(format_usd_price(25), "$25.00")
        self.assertEqual(format_usd_price(None), "$24.99")

    def test_fetch_product_from_verified_catalog(self):
        """Verifies retrieval of seeded Smart Spaces home organization products."""
        product = fetch_product("B0DHGM5XT4", affiliate_tag="smartspace07-21")
        self.assertEqual(product.asin, "B0DHGM5XT4")
        self.assertIn("Lifewit", product.title)
        self.assertEqual(product.price, "$19.99")
        self.assertEqual(product.rating, 4.8)
        self.assertIn("smartspace07-21", product.affiliate_url)

    def test_verified_catalog_completeness(self):
        """Verifies all top Smart Spaces ASINs are present in catalog with valid pricing."""
        required_asins = ["B0DHGM5XT4", "B0C42YJVCD", "B093GKKQ65", "B08332N66L"]
        for asin in required_asins:
            self.assertIn(asin, VERIFIED_CATALOG)
            item = VERIFIED_CATALOG[asin]
            self.assertTrue(item["price"].startswith("$"))
            self.assertGreaterEqual(item["rating"], 4.5)
            self.assertGreater(len(item["features"]), 0)


if __name__ == "__main__":
    unittest.main()
