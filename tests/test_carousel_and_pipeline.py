"""Comprehensive verification tests for PinForge AI carousel publishing and engine pipeline."""

import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch
from PIL import Image

from python_engine.models import (
    PinterestPublishRequest,
    AutonomousCycleRequest,
    ProductData,
)
from python_engine.autonomous_autopilot import _build_slide_title
from python_engine.carousel_engine import (
    render_slide1_showcase,
    render_slide2_specs,
    render_slide3_variants,
    render_slide4_uses,
    generate_carousel_pin_suite,
)
from python_engine.pinterest_client import PinterestClient
from python_engine.analytics_feedback_loop import AnalyticsFeedbackLoop, calculate_aes
from python_engine.scraper import search_duckduckgo_title


class TestCarouselAndPipeline(unittest.TestCase):

    def test_pydantic_models_and_fastapi_schema(self):
        """Test PinterestPublishRequest and AutonomousCycleRequest parse carousel fields cleanly."""
        # 1. Carousel payload without image_url should be valid
        c_req = PinterestPublishRequest(
            board_name_or_id="Small Apartment Hacks",
            title="4-Slide Carousel",
            description="Carousel Pin #AmazonAssociate",
            slides=[
                {"image_path": "/fake/slide1.jpg", "title": "Slide 1"},
                {"image_path": "/fake/slide2.jpg", "title": "Slide 2"},
            ],
        )
        self.assertIsNone(c_req.image_url)
        self.assertEqual(len(c_req.slides), 2)

        # 2. AutonomousCycleRequest has publish_as_carousel
        a_req = AutonomousCycleRequest(
            url_or_asin="B087F5K713",
            publish_as_carousel=True,
        )
        self.assertTrue(a_req.publish_as_carousel)

    def test_slide_title_builder_boundary_and_length(self):
        """Test _build_slide_title adheres to <= 100 chars and never cuts off mid-word."""
        prefix = "Dimensions & Build Specs"
        title = "Slim Rolling Storage Cart, 7-Tier Narrow Kitchen Organizer with Wheels"
        res = _build_slide_title(prefix, title, max_len=100)
        self.assertLessEqual(len(res), 100)
        self.assertTrue(res.startswith("Dimensions & Build Specs: "))
        self.assertFalse(res.endswith(" w"))  # No mid-word cutting!
        self.assertEqual(res, "Dimensions & Build Specs: Slim Rolling Storage Cart, 7-Tier Narrow Kitchen Organizer with Wheels")

        # Test extreme length
        very_long_title = "A" * 150 + " B" * 50
        res_long = _build_slide_title(prefix, very_long_title, max_len=100)
        self.assertLessEqual(len(res_long), 100)
        self.assertFalse(res_long.endswith(" "))
        self.assertFalse(res_long.endswith("-"))

    def test_carousel_slide_renders_with_sparse_friction_highlights(self):
        """Test slide rendering does not crash and utilizes 1 or 2 friction highlights."""
        img = Image.new("RGBA", (500, 500), (255, 255, 255, 255))
        sparse_highlights = ["100% RENTER FRIENDLY • NO DRILL", "TOOL-FREE 60S SETUP"]

        # Slide 1
        s1 = render_slide1_showcase(
            title="Slim Gap Cart",
            price="$29.99",
            rating=4.8,
            review_count="1,200+",
            product_img=img,
            friction_badge="⚡ RENTER FRIENDLY",
        )
        self.assertIsNotNone(s1)

        # Slide 2 with only 2 highlights
        s2 = render_slide2_specs(
            title="Slim Gap Cart",
            price="$29.99",
            features=["Feature A", "Feature B"],
            product_img=img,
            friction_highlights=sparse_highlights,
        )
        self.assertIsNotNone(s2)

        # Slide 3
        s3 = render_slide3_variants(
            title="Slim Gap Cart",
            price="$29.99",
            product_img=img,
        )
        self.assertIsNotNone(s3)

        # Slide 4 with only 2 highlights
        s4 = render_slide4_uses(
            title="Slim Gap Cart",
            price="$29.99",
            product_img=img,
            friction_highlights=sparse_highlights,
        )
        self.assertIsNotNone(s4)

    def test_pinterest_client_get_pin_and_link_sanitization(self):
        """Test get_pin method and carousel link payload omission when empty."""
        client = PinterestClient(access_token="test_token_1234567890")
        
        # Test get_pin constructs correct endpoint
        with patch.object(client, "_request", return_value={"id": "12345"}) as mock_req:
            res = client.get_pin("12345", pin_metrics=True)
            self.assertEqual(res["id"], "12345")
            mock_req.assert_called_once_with("pins/12345?pin_metrics=true")

        # Test create_carousel_pin_base64 link sanitization
        with patch.object(client, "_request", return_value={"id": "pin_999"}) as mock_req, \
             patch.object(client, "_record_published_pin") as mock_record:
            slides = [
                {"data": "base64data1", "title": "S1", "description": "D1", "link": "https://amazon.com"},
                {"data": "base64data2", "title": "S2", "description": "D2", "link": ""},
            ]
            client.create_carousel_pin_base64(
                board_id="b_123",
                title="Carousel Test",
                description="Desc #AmazonAssociate",
                slides=slides,
            )
            payload = mock_req.call_args[1]["data"]
            items = payload["media_source"]["items"]
            self.assertIn("link", items[0])
            self.assertNotIn("link", items[1])  # Empty link should be omitted!
            self.assertEqual(payload["link"], "https://amazon.com")

    def test_aes_calculation(self):
        """Test Algorithmic Engagement Score calculation formula."""
        score = calculate_aes(
            impressions=100,
            saves=5,
            outbound_clicks=2,
            pin_clicks=10,
            comments=1,
        )
        # (5*2 + 3*5 + 1.5*10 + 2*1) / 100 * 100 = (10 + 15 + 15 + 2) = 42.0
        self.assertEqual(score, 42.0)


if __name__ == "__main__":
    unittest.main()
