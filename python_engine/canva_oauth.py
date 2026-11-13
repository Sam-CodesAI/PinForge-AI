"""PinForge AI — Canva Connect API OAuth 2.0 PKCE Helper.

Handles:
- PKCE code_verifier and code_challenge generation
- Authorization URL construction for user consent
- Token exchange (code -> access_token & refresh_token)
- Automated token refresh
"""

import os
import base64
import hashlib
import logging
import urllib.parse
from typing import Dict, Any, Tuple, Optional
import requests

logger = logging.getLogger("PinForge.CanvaOAuth")

CANVA_AUTH_URL = "https://www.canva.com/api/oauth/authorize"
CANVA_TOKEN_URL = "https://api.canva.com/rest/v1/oauth/token"

DEFAULT_SCOPES = [
    "asset:read",
    "asset:write",
    "design:content:read",
    "design:content:write",
    "brandtemplate:content:read",
    "brandtemplate:meta:read",
]


def generate_pkce_pair() -> Tuple[str, str]:
    """Generates PKCE code_verifier and code_challenge (S256)."""
    # 32 random bytes -> 43 characters URL-safe base64 string
    raw_verifier = base64.urlsafe_b64encode(os.urandom(32)).decode("utf-8").rstrip("=")
    # SHA-256 digest
    digest = hashlib.sha256(raw_verifier.encode("utf-8")).digest()
    challenge = base64.urlsafe_b64encode(digest).decode("utf-8").rstrip("=")
    return raw_verifier, challenge


def build_authorization_url(
    client_id: str,
    redirect_uri: str,
    code_challenge: str,
    state: str = "pinforge_canva_oauth",
    scopes: Optional[list] = None,
) -> str:
    """Builds the 1-click Canva OAuth authorization URL."""
    scope_str = " ".join(scopes or DEFAULT_SCOPES)
    params = {
        "response_type": "code",
        "client_id": client_id.strip(),
        "redirect_uri": redirect_uri.strip(),
        "scope": scope_str,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
        "state": state,
    }
    return f"{CANVA_AUTH_URL}?{urllib.parse.urlencode(params)}"


def exchange_code(
    client_id: str,
    client_secret: str,
    code: str,
    code_verifier: str,
    redirect_uri: str,
) -> Dict[str, Any]:
    """Exchanges authorization code for access and refresh tokens."""
    payload = {
        "grant_type": "authorization_code",
        "code": code.strip(),
        "code_verifier": code_verifier.strip(),
        "redirect_uri": redirect_uri.strip(),
    }
    try:
        res = requests.post(
            CANVA_TOKEN_URL,
            auth=(client_id.strip(), client_secret.strip()),
            data=payload,
            timeout=15,
        )
        if res.status_code == 200:
            data = res.json()
            logger.info("✓ Successfully exchanged Canva authorization code for access token.")
            return {"success": True, "data": data}
        else:
            logger.error("Canva token exchange failed (%s): %s", res.status_code, res.text)
            return {"success": False, "status_code": res.status_code, "error": res.text}
    except Exception as e:
        logger.exception("Error exchanging Canva authorization code: %s", e)
        return {"success": False, "error": str(e)}


def refresh_token(
    client_id: str,
    client_secret: str,
    refresh_token_str: str,
) -> Dict[str, Any]:
    """Refreshes a Canva access token using the refresh_token grant."""
    payload = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token_str.strip(),
    }
    try:
        res = requests.post(
            CANVA_TOKEN_URL,
            auth=(client_id.strip(), client_secret.strip()),
            data=payload,
            timeout=15,
        )
        if res.status_code == 200:
            data = res.json()
            logger.info("✓ Successfully refreshed Canva access token.")
            return {"success": True, "data": data}
        else:
            logger.error("Canva token refresh failed (%s): %s", res.status_code, res.text)
            return {"success": False, "status_code": res.status_code, "error": res.text}
    except Exception as e:
        logger.exception("Error refreshing Canva token: %s", e)
        return {"success": False, "error": str(e)}
