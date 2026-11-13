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


if __name__ == "__main__":
    unittest.main()
