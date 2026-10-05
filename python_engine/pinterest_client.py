"""PinForge AI — Pinterest API v5 Production Client.

Handles authenticated API interactions for @Smart_Spaces:
- User profile & board discovery
- Programmatic Pin creation with 2:3 vertical graphics
- Analytics fetching (impressions, saves, outbound clicks)
- Token validation & 20-day autonomous refresh watchdog
"""

import os
import json
import base64
import urllib.request
import urllib.error
import urllib.parse
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from pathlib import Path

# Load configuration
try:
    from config import (
        PINTEREST_ACCESS_TOKEN,
        PINTEREST_APP_ID,
        PINTEREST_APP_SECRET,
        PINTEREST_REFRESH_TOKEN,
        PINTEREST_TARGET_USERNAME,
        DATA_DIR,
    )
except ImportError:
    from .config import (
        PINTEREST_ACCESS_TOKEN,
        PINTEREST_APP_ID,
        PINTEREST_APP_SECRET,
        PINTEREST_REFRESH_TOKEN,
        PINTEREST_TARGET_USERNAME,
        DATA_DIR,
    )

PINTEREST_API_BASE = "https://api.pinterest.com/v5"


from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

class PinterestClient:
    """Production client for Pinterest API v5 with self-healing token checks and sandbox auto-detection."""

    def __init__(self, access_token: Optional[str] = None):
        self.access_token = (access_token or PINTEREST_ACCESS_TOKEN).strip()
        self.app_id = PINTEREST_APP_ID
        self.app_secret = PINTEREST_APP_SECRET
        self.refresh_token = PINTEREST_REFRESH_TOKEN
        self.target_username = PINTEREST_TARGET_USERNAME
        self.base_url = os.getenv("PINTEREST_API_BASE", "https://api.pinterest.com/v5")
        self._board_cache: Dict[str, str] = {}  # name -> id

    @property
    def is_configured(self) -> bool:
        """Returns True if a valid access token is configured."""
        return bool(self.access_token and len(self.access_token) > 10)

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "User-Agent": "PinForge-AI/1.0 (@Smart_Spaces)",
        }

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10), retry=retry_if_exception_type((urllib.error.URLError, TimeoutError, ConnectionError)))
    def _request(
        self, endpoint: str, method: str = "GET", data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute HTTP request against Pinterest API v5 with automatic sandbox fallback."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        encoded_data = json.dumps(data).encode("utf-8") if data else None

        req = urllib.request.Request(
            url, data=encoded_data, headers=self._headers(), method=method
        )

        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                resp_body = resp.read().decode("utf-8")
                return json.loads(resp_body) if resp_body else {}
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8")
            try:
                err_json = json.loads(err_body)
            except Exception:
                err_json = {"raw": err_body}

            # Auto-detect Sandbox token if production rejected authentication
            if e.code == 401 and "Authentication failed" in err_body and "api-sandbox" not in self.base_url:
                try:
                    sandbox_url = f"https://api-sandbox.pinterest.com/v5/{endpoint.lstrip('/')}"
                    sandbox_req = urllib.request.Request(
                        sandbox_url, data=encoded_data, headers=self._headers(), method=method
                    )
                    with urllib.request.urlopen(sandbox_req, timeout=15) as s_resp:
                        self.base_url = "https://api-sandbox.pinterest.com/v5"
                        s_body = s_resp.read().decode("utf-8")
                        return json.loads(s_body) if s_body else {}
                except Exception:
                    pass
            
            # Specialized scope detection
            if e.code == 401 and "Missing:" in err_body:
                raise PermissionError(
                    f"Pinterest Token Scope Error: {err_json.get('message', err_body)}"
                )
            
            raise RuntimeError(f"Pinterest API Error ({e.code}) on {method} {endpoint}: {err_json}")
        except Exception as e:
            raise RuntimeError(f"Pinterest Request Failed ({method} {endpoint}): {e}")

    def get_user_account(self) -> Dict[str, Any]:
        """Fetch authenticated user profile details."""
        return self._request("user_account")

    def get_pin(self, pin_id: str, pin_metrics: bool = False) -> Dict[str, Any]:
        """Fetch details for a specific pin by ID from Pinterest API v5."""
        clean_id = str(pin_id).strip()
        endpoint = f"pins/{clean_id}"
        if pin_metrics:
            endpoint += "?pin_metrics=true"
        return self._request(endpoint)

    def get_boards(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """Fetch all boards on the authenticated account and cache name->id mappings."""
        if self._board_cache and not force_refresh:
            return [{"name": name, "id": b_id} for name, b_id in self._board_cache.items()]

        res = self._request("boards?page_size=100")
        items = res.get("items", [])
        self._board_cache = {b["name"].lower(): b["id"] for b in items}
        return items

    def find_board_id(self, board_name_or_keyword: str) -> Optional[str]:
        """Find matching board ID by exact name in board cache (case-insensitive).
        
        Strict matching prevents fuzzy token false-positives and enforces exact pillar alignment.
        """
        if not self._board_cache:
            self.get_boards()

        clean_query = board_name_or_keyword.lower().strip()
        if clean_query in self._board_cache:
            return self._board_cache[clean_query]

        return None

    def get_or_create_board(self, board_name: str) -> str:
        """Find existing board by exact name or create it automatically via Pinterest API.
        
        Eliminates fuzzy matching and removes any default fallback to 'Room Organization'.
        """
        clean_name = board_name.strip()
        found_id = self.find_board_id(clean_name)
        if found_id:
            return found_id

        # Board not found, create it dynamically with exact name requested
        res = self._request("boards", method="POST", data={"name": clean_name, "privacy": "PUBLIC"})
        new_id = res.get("id")
        if not new_id:
            raise RuntimeError(f"Failed to create board '{clean_name}': {res}")
        self._board_cache[clean_name.lower()] = new_id
        return new_id

    def bootstrap_smart_spaces_boards(self) -> None:
        """Ensure all 5 official Smart Spaces pillar boards exist."""
        boards = [
            'Small Apartment Hacks',
            'Space Saving Kitchens',
            'Closet & Wardrobe Organization',
            'Studio Living Ideas',
            'Room Organization'
        ]
        for b in boards:
            try:
                self.get_or_create_board(b)
            except Exception as e:
                print(f"[Warning] Failed to bootstrap board '{b}': {e}")

    def create_pin(
        self,
        board_id: str,
        title: str,
        description: str,
        link: str,
        image_url: Optional[str] = None,
        image_path: Optional[str] = None,
        base64_image: Optional[str] = None,
        alt_text: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a new Pin on Pinterest API v5.
        
        Enforces Pinterest's limits:
        - title: max 100 characters
        - description: max 500 characters
        - mandatory disclosure: #AmazonAssociate
        - Supports direct base64 upload, local image file paths, or remote public URLs.
        """
        # Truncate and sanitize title
        safe_title = title.strip()[:100]

        # Ensure FTC disclosure in description
        disclosure = "#AmazonAssociate"
        if disclosure.lower() not in description.lower():
            safe_desc = f"{description.strip()} {disclosure}"
        else:
            safe_desc = description.strip()
        safe_desc = safe_desc[:500]

        # Determine media source (base64 vs URL)
        media_source = {}
        if base64_image:
            # Strip data:image/...;base64, prefix if present
            clean_b64 = base64_image.split(",")[-1] if "," in base64_image else base64_image
            media_source = {
                "source_type": "image_base64",
                "content_type": "image/jpeg",
                "data": clean_b64,
            }
        elif image_path and Path(image_path).exists():
            raw_bytes = Path(image_path).read_bytes()
            media_source = {
                "source_type": "image_base64",
                "content_type": "image/jpeg" if str(image_path).endswith((".jpg", ".jpeg")) else "image/png",
                "data": base64.b64encode(raw_bytes).decode("utf-8"),
            }
        elif image_url and ("localhost" in image_url or "pinforge.vercel.app" in image_url):
            # If pointing to local static pins dir, load binary file directly
            filename = Path(image_url).name
            local_pin_path = Path(__file__).resolve().parent / "static" / "pins" / filename
            if local_pin_path.exists():
                raw_bytes = local_pin_path.read_bytes()
                media_source = {
                    "source_type": "image_base64",
                    "content_type": "image/jpeg",
                    "data": base64.b64encode(raw_bytes).decode("utf-8"),
                }
            else:
                media_source = {"source_type": "image_url", "url": image_url}
        elif image_url:
            media_source = {"source_type": "image_url", "url": image_url}
        else:
            raise ValueError("Must provide either image_url, image_path, or base64_image")

        payload = {
            "board_id": board_id,
            "title": safe_title,
            "description": safe_desc,
            "link": link,
            "alt_text": (alt_text or safe_title)[:500],
            "media_source": media_source,
        }

        result = self._request("pins", method="POST", data=payload)
        
        # Log to local history ledger with full request payload fallback
        self._record_published_pin(result, payload=payload)
        return result

    def create_carousel_pin_base64(
        self,
        board_id: str,
        title: str,
        description: str,
        slides: List[Union[Dict[str, Any], str, Path]],
        link: Optional[str] = None,
        alt_text: Optional[str] = None,
        board_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a multi-slide Carousel Pin on Pinterest API v5 using multiple_image_base64.

        Enforces Pinterest API v5 constraints:
        - media_source: {"source_type": "multiple_image_base64", "items": [...]}
        - Each item: content_type: "image/jpeg", data: <clean_base64>, title, description, link
        - Allows individual per-slide deep affiliate links without external CDN hosting.
        - Robustly accepts either dictionaries or file path strings.
        """
        if not slides or len(slides) < 2:
            raise ValueError("Carousel pin requires at least 2 slides")

        safe_title = title.strip()[:100]
        disclosure = "#AmazonAssociate"
        if disclosure.lower() not in description.lower():
            safe_desc = f"{description.strip()} {disclosure}"
        else:
            safe_desc = description.strip()
        safe_desc = safe_desc[:500]

        carousel_items = []
        for idx, raw_slide in enumerate(slides, start=1):
            if isinstance(raw_slide, (str, Path)):
                slide: Dict[str, Any] = {"image_path": str(raw_slide)}
            elif isinstance(raw_slide, dict):
                slide = dict(raw_slide)
            else:
                raise ValueError(f"Slide {idx} must be a dict or file path string, got {type(raw_slide)}")

            slide_data = ""
            content_type = slide.get("content_type")

            if "data" in slide and slide["data"]:
                raw_b64 = str(slide["data"])
                slide_data = raw_b64.split(",")[-1] if "," in raw_b64 else raw_b64
                if not content_type:
                    content_type = "image/jpeg"
            elif "base64_image" in slide and slide["base64_image"]:
                raw_b64 = str(slide["base64_image"])
                slide_data = raw_b64.split(",")[-1] if "," in raw_b64 else raw_b64
                if not content_type:
                    content_type = "image/jpeg"
            elif "image_path" in slide and Path(slide["image_path"]).exists():
                p = Path(slide["image_path"])
                raw_bytes = p.read_bytes()
                slide_data = base64.b64encode(raw_bytes).decode("utf-8")
                if not content_type:
                    content_type = "image/png" if p.suffix.lower() == ".png" else "image/jpeg"
            elif "image_url" in slide and slide["image_url"]:
                url = str(slide["image_url"])
                filename = Path(url).name
                local_pin_path = Path(__file__).resolve().parent / "static" / "pins" / filename
                if local_pin_path.exists():
                    raw_bytes = local_pin_path.read_bytes()
                    slide_data = base64.b64encode(raw_bytes).decode("utf-8")
                    if not content_type:
                        content_type = "image/png" if local_pin_path.suffix.lower() == ".png" else "image/jpeg"
                else:
                    req = urllib.request.Request(url, headers={"User-Agent": "PinForge-AI/1.0"})
                    with urllib.request.urlopen(req, timeout=12) as resp:
                        raw_bytes = resp.read()
                        slide_data = base64.b64encode(raw_bytes).decode("utf-8")
                    if not content_type:
                        content_type = "image/jpeg"
            else:
                raise ValueError(f"Slide {idx} missing valid image source (image_path, data, base64_image, or image_url)")

            if not content_type:
                content_type = "image/jpeg"

            # Per-slide title, description, link
            slide_title = (slide.get("title") or f"{safe_title} (Slide {idx})").strip()[:100]
            s_desc = (slide.get("description") or safe_desc).strip()
            if disclosure.lower() not in s_desc.lower():
                s_desc = f"{s_desc} {disclosure}"
            slide_description = s_desc[:500]
            slide_link = (slide.get("link") or link or "").strip()

            item: Dict[str, Any] = {
                "content_type": content_type,
                "data": slide_data,
                "title": slide_title,
                "description": slide_description,
            }
            if slide_link:
                item["link"] = slide_link
            carousel_items.append(item)

        default_link = (link or (carousel_items[0].get("link") if carousel_items else "") or "").strip()
        payload: Dict[str, Any] = {
            "board_id": board_id,
            "title": safe_title,
            "description": safe_desc,
            "alt_text": (alt_text or safe_title)[:500],
            "media_source": {
                "source_type": "multiple_image_base64",
                "items": carousel_items,
            },
        }
        if default_link:
            payload["link"] = default_link

        result = self._request("pins", method="POST", data=payload)
        self._record_published_pin(result, payload=payload, board_name=board_name, is_carousel=True)
        return result

    def publish_carousel_pin(
        self,
        title: str,
        description: str,
        board_name: str,
        slides: List[Union[Dict[str, Any], str, Path]],
        link: Optional[str] = None,
        alt_text: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Convenience method: resolves board by exact name and publishes a multi-slide carousel pin."""
        board_id = self.get_or_create_board(board_name)
        result = self.create_carousel_pin_base64(
            board_id=board_id,
            title=title,
            description=description,
            slides=slides,
            link=link,
            alt_text=alt_text,
            board_name=board_name,
        )
        return {**result, "pin_id": result.get("id", "")}

    def publish_pin(
        self,
        title: str,
        description: str,
        board_name: str,
        image_path_or_url: Optional[str] = None,
        link: Optional[str] = None,
        alt_text: Optional[str] = None,
        slides: Optional[List[Union[Dict[str, Any], str, Path]]] = None,
    ) -> Dict[str, Any]:
        """Convenience method: resolves board by name and publishes image or carousel directly."""
        if slides and len(slides) >= 2:
            return self.publish_carousel_pin(
                title=title,
                description=description,
                board_name=board_name,
                slides=slides,
                link=link,
                alt_text=alt_text,
            )

        if not image_path_or_url:
            raise ValueError("Must provide either image_path_or_url or slides for publish_pin")

        board_id = self.get_or_create_board(board_name)
        if image_path_or_url.startswith("http://") or image_path_or_url.startswith("https://"):
            result = self.create_pin(
                board_id=board_id,
                title=title,
                description=description,
                link=link or "",
                image_url=image_path_or_url,
                alt_text=alt_text,
            )
        else:
            result = self.create_pin(
                board_id=board_id,
                title=title,
                description=description,
                link=link or "",
                image_path=image_path_or_url,
                alt_text=alt_text,
            )
        return {**result, "pin_id": result.get("id", "")}

    def get_account_analytics(
        self, days: int = 30, metrics: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Fetch account-level pin performance analytics."""
        if metrics is None:
            metrics = ["IMPRESSION", "SAVE", "OUTBOUND_CLICK", "PIN_CLICK_RATE"]

        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        columns_str = ",".join(metrics)

        endpoint = (
            f"user_account/analytics"
            f"?start_date={start_date}&end_date={end_date}&columns={columns_str}"
        )
        return self._request(endpoint)

    def _record_published_pin(
        self,
        pin_data: Dict[str, Any],
        payload: Optional[Dict[str, Any]] = None,
        board_name: Optional[str] = None,
        is_carousel: bool = False,
    ) -> None:
        """Persist pin metadata locally for self-learning analytics tracking."""
        try:
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            ledger_path = DATA_DIR / "published_pins.json"
            pins = []
            if ledger_path.exists():
                try:
                    pins = json.loads(ledger_path.read_text())
                except Exception:
                    pins = []

            # Merge payload and pin_data to avoid null values when API doesn't echo request fields
            merged = {**(payload or {}), **pin_data}
            b_id = str(merged.get("board_id") or "")
            b_name = board_name or merged.get("board_name")
            if not b_name and b_id:
                for name, bid in self._board_cache.items():
                    if str(bid) == b_id:
                        b_name = name.title()
                        break

            pin_id = str(merged.get("id") or merged.get("pin_id") or "").strip()
            if not pin_id:
                return

            pin_record = {
                "id": pin_id,
                "title": merged.get("title") or "Smart Spaces Pin",
                "link": merged.get("link") or "",
                "board_id": b_id,
                "board_name": b_name or "Room Organization",
                "is_carousel": is_carousel,
                "created_at": merged.get("created_at") or datetime.now().isoformat(),
            }

            # Deduplicate by pin id if already present
            existing_idx = next(
                (i for i, p in enumerate(pins) if p.get("id") == pin_record["id"] and pin_record["id"]),
                None
            )
            if existing_idx is not None:
                pins[existing_idx] = pin_record
            else:
                pins.append(pin_record)

            ledger_path.write_text(json.dumps(pins, indent=2))
        except Exception as e:
            print(f"[Warning] Failed to record published pin: {e}")

    def refresh_access_token(
        self,
        app_id: Optional[str] = None,
        app_secret: Optional[str] = None,
        refresh_token: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Refreshes Pinterest API v5 access token using OAuth refresh token.

        Target endpoint: POST https://api.pinterest.com/v5/oauth/token
        Requires Basic auth header base64(app_id:app_secret) and grant_type=refresh_token.
        """
        effective_app_id = (app_id or self.app_id or os.getenv("PINTEREST_APP_ID") or "").strip()
        effective_app_secret = (app_secret or self.app_secret or os.getenv("PINTEREST_APP_SECRET") or "").strip()
        effective_refresh = (refresh_token or self.refresh_token or os.getenv("PINTEREST_REFRESH_TOKEN") or "").strip()

        if not effective_app_id or not effective_app_secret:
            raise ValueError("PINTEREST_APP_ID and PINTEREST_APP_SECRET are required to refresh access token.")
        if not effective_refresh:
            raise ValueError("PINTEREST_REFRESH_TOKEN is required to refresh access token.")

        auth_header = base64.b64encode(f"{effective_app_id}:{effective_app_secret}".encode("utf-8")).decode("utf-8")
        url = "https://api.pinterest.com/v5/oauth/token"
        headers = {
            "Authorization": f"Basic {auth_header}",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        body_data = urllib.parse.urlencode({
            "grant_type": "refresh_token",
            "refresh_token": effective_refresh,
        }).encode("utf-8")

        req = urllib.request.Request(url, data=body_data, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                resp_body = resp.read().decode("utf-8")
                token_data = json.loads(resp_body) if resp_body else {}
                new_token = token_data.get("access_token")
                if new_token:
                    self.access_token = new_token
                    print(f"✓ Pinterest access token successfully refreshed. Expires in: {token_data.get('expires_in')}s")
                return token_data
        except urllib.error.HTTPError as e:
            err_msg = e.read().decode("utf-8")
            print(f"[Error] Failed to refresh Pinterest access token: HTTP {e.code} - {err_msg}")
            raise RuntimeError(f"Pinterest token refresh failed ({e.code}): {err_msg}")


def generate_oauth_init_url(app_id: str, redirect_uri: str = "https://localhost", state: str = "pinforge_oauth") -> str:
    """Generates Pinterest OAuth 2.0 Authorization URL for initial connection."""
    scopes = "boards:read,boards:write,pins:read,pins:write,user_accounts:read"
    params = urllib.parse.urlencode({
        "client_id": app_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": scopes,
        "state": state,
    })
    return f"https://www.pinterest.com/oauth/?{params}"


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="PinForge Pinterest Client & OAuth Helper")
    parser.add_argument("--oauth-init", action="store_true", help="Generate OAuth 2.0 URL to obtain initial tokens")
    parser.add_argument("--refresh-token", action="store_true", help="Refresh OAuth 2.0 access token via refresh token")
    parser.add_argument("--app-id", type=str, help="Pinterest App ID for OAuth")
    parser.add_argument("--app-secret", type=str, help="Pinterest App Secret for OAuth")
    parser.add_argument("--redirect-uri", type=str, default="https://localhost", help="OAuth Redirect URI")
    args = parser.parse_args()

    client = PinterestClient()

    if args.oauth_init:
        app_id = (args.app_id or client.app_id or os.getenv("PINTEREST_APP_ID") or "").strip()
        if not app_id:
            print("Error: PINTEREST_APP_ID is required to generate OAuth authorization URL.")
            print("Pass via --app-id <ID> or set PINTEREST_APP_ID in your environment.")
        else:
            oauth_url = generate_oauth_init_url(app_id, redirect_uri=args.redirect_uri)
            print("\n" + "=" * 70)
            print("📌 PinForge AI — Pinterest OAuth 2.0 Initialization")
            print("=" * 70)
            print("1. Open the following URL in your browser:")
            print(f"\n   {oauth_url}\n")
            print("2. Authorize access for @Smart_Spaces.")
            print("3. Pinterest will redirect to your redirect URI with a ?code= parameter.")
            print("4. Exchange that code for your initial access_token and refresh_token.")
            print("=" * 70 + "\n")
    elif args.refresh_token:
        print("Refreshing Pinterest access token...")
        try:
            res = client.refresh_access_token(app_id=args.app_id, app_secret=args.app_secret)
            print("Token refresh successful:", res)
        except Exception as e:
            print(f"Token refresh failed: {e}")
    else:
        print("--- Pinterest Client Verification ---")
        try:
            user = client.get_user_account()
            print(f"Authenticated Account: {user.get('business_name')} (@{user.get('username')})")
            print(f"Boards Found: {user.get('board_count')}")

            boards = client.get_boards(force_refresh=True)
            print("\nActive Boards:")
            for b in boards:
                print(f"  - [{b.get('id')}] {b.get('name')}")
            print("\nConnection Status: HEALTHY (Read Scopes Active)")
        except Exception as e:
            print(f"Connection Error: {e}")
