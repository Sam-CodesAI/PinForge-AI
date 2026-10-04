"""PinForge AI — Canva Client Integration.

Handles Canva Connect API and Canva Apps SDK integration for the Smart Spaces brand:
- Asset uploading to Canva Media library
- Brand Template autofill for 2:3 vertical product collages
- Canva App status and preview URL generation
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

import requests
try:
    from python_engine.config import (
        CANVA_CLIENT_ID,
        CANVA_CLIENT_SECRET,
        CANVA_BRAND_TEMPLATE_ID,
    )
except ImportError:
    from config import (
        CANVA_CLIENT_ID,
        CANVA_CLIENT_SECRET,
        CANVA_BRAND_TEMPLATE_ID,
    )

logger = logging.getLogger("PinForge.Canva")

CANVA_API_BASE = "https://api.canva.com/rest/v1"
CANVA_APP_ID = os.getenv("CANVA_APP_ID", "AAHOGH31K5Q")
CANVA_APP_ORIGIN = os.getenv("CANVA_APP_ORIGIN", "https://app-aahogh31k5q.canva-apps.com")


class CanvaClient:
    """Canva Connect API & Apps SDK Client."""

    def __init__(self, access_token: Optional[str] = None):
        self.access_token = access_token or os.getenv("CANVA_ACCESS_TOKEN", "")
        self.app_id = CANVA_APP_ID
        self.app_origin = CANVA_APP_ORIGIN

    @property
    def is_configured(self) -> bool:
        """Returns True if minimum Canva credentials or app ID is available."""
        return bool(self.access_token or self.app_id)

    def get_app_info(self) -> Dict[str, Any]:
        """Returns metadata for the linked Canva Smart Spaces App."""
        return {
            "app_name": "smart-spaces",
            "app_id": self.app_id,
            "app_origin": self.app_origin,
            "developer_portal_url": f"https://www.canva.com/developers/app/{self.app_id}",
            "preview_url": f"https://www.canva.com/developers/app/{self.app_id}/preview?intent=design_editor&surface=editor",
            "local_dev_url": "http://localhost:8080",
        }

    def upload_asset(self, file_path: str, name: Optional[str] = None) -> Dict[str, Any]:
        """Uploads an image asset to Canva library via Connect API."""
        if not self.access_token:
            logger.warning("Canva access token not configured, skipping Connect API upload.")
            return {"success": False, "error": "CANVA_ACCESS_TOKEN_MISSING"}

        path = Path(file_path)
        if not path.exists():
            return {"success": False, "error": f"File not found: {file_path}"}

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Asset-Upload-Metadata": json.dumps({"name_base64": name or path.stem}),
        }

        try:
            with open(path, "rb") as f:
                res = requests.post(
                    f"{CANVA_API_BASE}/asset-uploads",
                    headers=headers,
                    data=f.read(),
                    timeout=30,
                )

            if res.status_code in (200, 201):
                data = res.json()
                logger.info("Successfully uploaded asset to Canva: %s", data.get("asset", {}).get("id"))
                return {"success": True, "asset": data.get("asset")}
            else:
                logger.error("Canva asset upload failed (%s): %s", res.status_code, res.text)
                return {"success": False, "status_code": res.status_code, "error": res.text}
        except Exception as e:
            logger.exception("Error uploading asset to Canva: %s", e)
            return {"success": False, "error": str(e)}

    def create_autofill_job(
        self,
        template_id: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Autofills a Canva Brand Template with Amazon product data."""
        if not self.access_token:
            return {"success": False, "error": "CANVA_ACCESS_TOKEN_MISSING"}

        target_template = template_id or CANVA_BRAND_TEMPLATE_ID
        if not target_template:
            return {"success": False, "error": "CANVA_BRAND_TEMPLATE_ID_MISSING"}

        payload = {
            "brand_template_id": target_template,
            "data": data or {},
        }

        try:
            res = requests.post(
                f"{CANVA_API_BASE}/autofills",
                headers={
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=30,
            )

            if res.status_code in (200, 201, 202):
                return {"success": True, "job": res.json().get("job")}
            else:
                logger.error("Canva autofill failed (%s): %s", res.status_code, res.text)
                return {"success": False, "status_code": res.status_code, "error": res.text}
        except Exception as e:
            logger.exception("Error creating Canva autofill job: %s", e)
            return {"success": False, "error": str(e)}
