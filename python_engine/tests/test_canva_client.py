"""Tests for CanvaClient integration with Canva Connect API."""

import io
import unittest
from unittest.mock import MagicMock, patch
from PIL import Image

from python_engine.canva_client import CanvaClient


class TestCanvaClientImageGeneration(unittest.TestCase):
    def test_generate_image_unconfigured(self):
        client = CanvaClient(access_token="")
        result = client.generate_image(prompt="Modern desk organizer")
        self.assertIsNone(result)

    @patch("requests.get")
    @patch("requests.post")
    def test_generate_image_success(self, mock_post, mock_get):
        client = CanvaClient(access_token="canva_test_token_123")

        # Mock POST /v1/image-generations
        mock_post_resp = MagicMock()
        mock_post_resp.status_code = 201
        mock_post_resp.json.return_value = {"job": {"id": "job_abc_123", "status": "in_progress"}}
        mock_post.return_value = mock_post_resp

        # Create dummy test image bytes
        dummy_img = Image.new("RGBA", (800, 1200), color=(255, 0, 0, 255))
        buf = io.BytesIO()
        dummy_img.save(buf, format="PNG")
        dummy_bytes = buf.getvalue()

        # Mock GET poll & download
        mock_poll_resp = MagicMock()
        mock_poll_resp.status_code = 200
        mock_poll_resp.json.return_value = {
            "job": {
                "id": "job_abc_123",
                "status": "success",
                "result": {"url": "https://media.canva.com/generated.png"},
            }
        }

        mock_download_resp = MagicMock()
        mock_download_resp.status_code = 200
        mock_download_resp.content = dummy_bytes

        mock_get.side_effect = [mock_poll_resp, mock_download_resp]

        result = client.generate_image(prompt="Modern desk organizer", model="craft_v1_2k")
        self.assertIsNotNone(result)
        self.assertEqual(result.size, (1000, 1500))
        self.assertEqual(mock_post.call_count, 1)

    @patch("requests.post")
    def test_generate_image_api_error(self, mock_post):
        client = CanvaClient(access_token="canva_test_token_123")
        mock_resp = MagicMock()
        mock_resp.status_code = 401
        mock_resp.text = "Unauthorized"
        mock_post.return_value = mock_resp

        result = client.generate_image(prompt="Aesthetic small space room")
        self.assertIsNone(result)

    @patch("requests.post")
    def test_create_design_success(self, mock_post):
        client = CanvaClient(access_token="canva_test_token_123")
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "design": {
                "id": "design_123",
                "title": "Smart Spaces Pin",
                "urls": {"edit_url": "https://canva.com/edit", "view_url": "https://canva.com/view"},
            }
        }
        mock_post.return_value = mock_resp

        result = client.create_design(title="Smart Spaces Pin", asset_id="asset_456")
        self.assertTrue(result["success"])
        self.assertEqual(result["design"]["id"], "design_123")

    @patch("requests.get")
    @patch("requests.post")
    def test_export_design_success(self, mock_post, mock_get):
        client = CanvaClient(access_token="canva_test_token_123")
        mock_post_resp = MagicMock()
        mock_post_resp.status_code = 200
        mock_post_resp.json.return_value = {"job": {"id": "export_job_789", "status": "in_progress"}}
        mock_post.return_value = mock_post_resp

        mock_get_resp = MagicMock()
        mock_get_resp.status_code = 200
        mock_get_resp.json.return_value = {
            "job": {
                "id": "export_job_789",
                "status": "success",
                "urls": ["https://export-download.canva.com/pin.png"],
            }
        }
        mock_get.return_value = mock_get_resp

        result = client.export_design("design_123", format_type="png")
        self.assertTrue(result["success"])
        self.assertEqual(result["download_url"], "https://export-download.canva.com/pin.png")


if __name__ == "__main__":
    unittest.main()
