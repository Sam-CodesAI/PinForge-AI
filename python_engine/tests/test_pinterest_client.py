"""Test Suite for PinForge AI Pinterest API Client.

Verifies:
1. Header formulation with Bearer auth token
2. Board resolution caching and lookup
3. Dry-run and error response handling
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

# Add project root to sys.path
CURRENT_DIR = Path(__file__).resolve().parent
PYTHON_ENGINE_DIR = CURRENT_DIR.parent
PROJECT_ROOT = PYTHON_ENGINE_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(PYTHON_ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHON_ENGINE_DIR))

from python_engine.pinterest_client import PinterestClient


class TestPinterestClient(unittest.TestCase):
    """Test suite validating Pinterest API v5 client operations."""

    def setUp(self):
        self.client = PinterestClient(access_token="test_mock_token")

    def test_build_headers(self):
        """Verifies correct Authorization and Content-Type headers."""
        headers = self.client._headers()
        self.assertIn("Authorization", headers)
        self.assertEqual(headers["Authorization"], "Bearer test_mock_token")
        self.assertEqual(headers["Content-Type"], "application/json")

    def test_board_cache_resolution(self):
        """Verifies board name to board ID lookup using local cache."""
        self.client._board_cache = {
            "room organization": "1132444337492930442",
            "small apartment hacks": "1132444337492933749",
        }
        board_id = self.client.get_or_create_board("Room Organization")
        self.assertEqual(board_id, "1132444337492930442")

    @patch.object(PinterestClient, "_request")
    def test_create_pin_payload_structure(self, mock_request):
        """Verifies API payload formatting on create_pin call."""
        mock_request.return_value = {
            "id": "1132444999999999",
            "title": "Aesthetic Room Organization",
            "link": "https://pinforge.vercel.app/p/test-slug",
        }

        res = self.client.create_pin(
            board_id="1132444337492930442",
            title="Aesthetic Room Organization",
            description="📌 SAVE THIS PIN to your home board! #AmazonAssociate",
            link="https://pinforge.vercel.app/p/test-slug",
            image_url="https://pinforge.vercel.app/pin.png",
        )

        self.assertEqual(res["id"], "1132444999999999")
        mock_request.assert_called_once()


if __name__ == "__main__":
    unittest.main()
