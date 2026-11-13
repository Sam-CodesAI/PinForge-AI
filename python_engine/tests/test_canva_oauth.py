"""Tests for Canva OAuth PKCE helper."""

import unittest
from unittest.mock import MagicMock, patch

from python_engine.canva_oauth import (
    generate_pkce_pair,
    build_authorization_url,
    exchange_code,
    refresh_token,
)


class TestCanvaOAuth(unittest.TestCase):
    def test_generate_pkce_pair(self):
        verifier, challenge = generate_pkce_pair()
        self.assertTrue(len(verifier) >= 43)
        self.assertTrue(len(challenge) >= 43)
        self.assertNotEqual(verifier, challenge)

    def test_build_authorization_url(self):
        url = build_authorization_url(
            client_id="mock_client_id_123",
            redirect_uri="https://pinforge.vercel.app/api/auth/canva/callback",
            code_challenge="test_challenge_abc",
        )
        self.assertIn("https://www.canva.com/api/oauth/authorize?", url)
        self.assertIn("client_id=mock_client_id_123", url)
        self.assertIn("code_challenge=test_challenge_abc", url)
        self.assertIn("code_challenge_method=S256", url)
        self.assertIn("response_type=code", url)

    @patch("requests.post")
    def test_exchange_code_success(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "access_token": "canva_access_token_123",
            "token_type": "Bearer",
            "expires_in": 14400,
            "refresh_token": "canva_refresh_token_456",
        }
        mock_post.return_value = mock_resp

        result = exchange_code(
            client_id="mock_client_id_123",
            client_secret="mock_client_secret_xyz",
            code="test_code",
            code_verifier="test_verifier",
            redirect_uri="https://pinforge.vercel.app/api/auth/canva/callback",
        )
        self.assertTrue(result["success"])
        self.assertEqual(result["data"]["access_token"], "canva_access_token_123")

    @patch("requests.post")
    def test_refresh_token_success(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "access_token": "canva_new_access_token_789",
            "token_type": "Bearer",
            "expires_in": 14400,
        }
        mock_post.return_value = mock_resp

        result = refresh_token(
            client_id="mock_client_id_123",
            client_secret="mock_client_secret_xyz",
            refresh_token_str="canva_refresh_token_456",
        )
        self.assertTrue(result["success"])
        self.assertEqual(result["data"]["access_token"], "canva_new_access_token_789")


if __name__ == "__main__":
    unittest.main()
