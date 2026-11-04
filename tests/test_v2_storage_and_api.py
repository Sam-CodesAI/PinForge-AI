"""V2.0.0 Storage Gateway, Async Pipeline, and Security Verification Tests."""

import os
import unittest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from python_engine.main import app
from python_engine.storage import SupabaseStorageGateway
from python_engine.models import ProductData


class TestV2StorageAndSecurity(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)

    def test_storage_gateway_local_fallback(self):
        """Verify storage gateway falls back to local JSON without failing."""
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            with patch("python_engine.storage.PUBLISHED_PINS_FILE", tmp_path / "published_pins.json"), \
                 patch("python_engine.storage.PERFORMANCE_LEDGER_FILE", tmp_path / "performance_ledger.json"), \
                 patch("python_engine.storage.ACCOUNT_OVERVIEW_FILE", tmp_path / "account_overview.json"), \
                 patch("python_engine.storage.BOARD_ANALYTICS_FILE", tmp_path / "board_analytics.json"):

                gateway = SupabaseStorageGateway(supabase_url=None, supabase_key=None)
                self.assertFalse(gateway.is_configured)

                # Test local pin save and retrieval
                test_pin = {
                    "id": "test_pin_9999",
                    "asin": "B0TESTASIN",
                    "title": "Local Fallback Test Product",
                    "board_id": "b_123",
                    "board_name": "Small Apartment Hacks",
                    "image_url": "https://example.com/pin.jpg",
                    "link": "https://amzn.to/test",
                    "created_at": "2026-11-04T00:00:00Z",
                }
                gateway.save_published_pin(test_pin)

                pins = gateway.load_published_pins()
                found = any(p.get("id") == "test_pin_9999" or p.get("pin_id") == "test_pin_9999" for p in pins)
                self.assertTrue(found)

                # Test analytics sync cycle
                ranked = [
                    {
                        "pin_id": "test_pin_9999",
                        "title": "Local Fallback Test Product",
                        "link": "https://amzn.to/test",
                        "metrics": {
                            "impressions": 1500,
                            "pin_clicks": 45,
                            "outbound_clicks": 12,
                            "saves": 8,
                        },
                        "bayesian_aes": 0.035,
                    }
                ]
                gateway.sync_analytics_cycle(
                    ranked_pins=ranked,
                    account_overview={"total_pins": 1},
                    board_summary={"Small Apartment Hacks": {"pins": 1}},
                    sync_published_list=[test_pin],
                )

                # Ensure written to temp files
                self.assertTrue((tmp_path / "published_pins.json").exists())
                self.assertTrue((tmp_path / "performance_ledger.json").exists())

    @patch("httpx.Client.post")
    def test_storage_gateway_remote_sync(self, mock_post):
        """Verify storage gateway routes through REST PostgREST endpoint when configured."""
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_post.return_value = mock_response

        gateway = SupabaseStorageGateway(
            supabase_url="https://mock.supabase.co",
            supabase_key="mock-service-key",
        )
        self.assertTrue(gateway.is_configured)

        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            with patch("python_engine.storage.PUBLISHED_PINS_FILE", tmp_path / "published_pins.json"):
                # Test saving pin over HTTP/REST
                test_pin = {
                    "id": "sb_101",
                    "asin": "B087F5K713",
                    "title": "Supabase Backed Pin",
                    "link": "https://amzn.to/test",
                    "board_id": "b_101",
                    "board_name": "Space Saving Kitchens",
                }
                gateway.save_published_pin(test_pin)
                self.assertTrue(mock_post.called)
                call_url = mock_post.call_args[0][0]
                self.assertIn("/rest/v1/pinforge_pins", call_url)
                self.assertIn("on_conflict=pin_id", call_url)

    def test_production_fails_closed_without_api_key(self):
        """Verify endpoints fail closed with HTTP 500 when ENVIRONMENT=production and no API key configured."""
        with patch.dict(os.environ, {"ENVIRONMENT": "production", "PINFORGE_API_KEY": "", "API_KEY": ""}):
            res = self.client.post("/api/extract", json={"url_or_asin": "B087F5K713"})
            self.assertEqual(res.status_code, 500)
            self.assertIn("Production security invariant violated", res.json()["detail"])

    def test_api_key_security_enforcement(self):
        """Verify API key dependency protects endpoints when PINFORGE_API_KEY is configured."""
        with patch.dict(os.environ, {"PINFORGE_API_KEY": "supersecretkey123"}):
            # 1. Request without API key should be rejected with 401
            res_no_key = self.client.post("/api/extract", json={"url_or_asin": "B087F5K713"})
            self.assertEqual(res_no_key.status_code, 401)
            self.assertIn("Unauthorized", res_no_key.json()["detail"])

            # 2. Request with invalid key should be rejected with 401
            res_bad_key = self.client.post(
                "/api/extract",
                json={"url_or_asin": "B087F5K713"},
                headers={"X-API-Key": "wrong-key"},
            )
            self.assertEqual(res_bad_key.status_code, 401)

            # 3. Request with valid X-API-Key should pass authentication
            with patch("python_engine.main.async_fetch_product") as mock_fetch:
                mock_fetch.return_value = ProductData(
                    asin="B087F5K713",
                    title="Mock Space Saver",
                    price="$29.99",
                    rating=4.7,
                    review_count="1,200+",
                    image_url="https://example.com/p.jpg",
                    features=["Foldable", "Compact"],
                    affiliate_url="https://amzn.to/mock",
                    bridge_slug="mock-space-saver",
                )
                res_good_header = self.client.post(
                    "/api/extract",
                    json={"url_or_asin": "B087F5K713"},
                    headers={"X-API-Key": "supersecretkey123"},
                )
                self.assertEqual(res_good_header.status_code, 200)
                self.assertEqual(res_good_header.json()["asin"], "B087F5K713")

                # 4. Request with valid Bearer token should pass authentication
                res_good_bearer = self.client.post(
                    "/api/extract",
                    json={"url_or_asin": "B087F5K713"},
                    headers={"Authorization": "Bearer supersecretkey123"},
                )
                self.assertEqual(res_good_bearer.status_code, 200)

    def test_cors_origins_configured(self):
        """Verify allowed origins in CORS configuration."""
        from python_engine.main import CORS_ALLOWED_ORIGINS
        self.assertIn("https://pinforge.vercel.app", CORS_ALLOWED_ORIGINS)
        self.assertIn("https://sam-codes.com", CORS_ALLOWED_ORIGINS)
        self.assertIn("http://localhost:3000", CORS_ALLOWED_ORIGINS)


if __name__ == "__main__":
    unittest.main()
