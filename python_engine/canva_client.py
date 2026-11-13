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
    from python_engine.config import CANVA_BRAND_TEMPLATE_ID
except ImportError:
    from config import CANVA_BRAND_TEMPLATE_ID

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

    def upload_asset(self, file_path: str, name: Optional[str] = None, timeout: float = 30.0) -> Dict[str, Any]:
        """Uploads an image asset to Canva library via Connect API and waits for completion."""
        if not self.access_token:
            logger.warning("Canva access token not configured, skipping Connect API upload.")
            return {"success": False, "error": "CANVA_ACCESS_TOKEN_MISSING"}

        path = Path(file_path)
        if not path.exists():
            return {"success": False, "error": f"File not found: {file_path}"}

        import base64
        import time

        clean_name = name or path.stem
        name_b64 = base64.b64encode(clean_name.encode("utf-8")).decode("utf-8")

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Asset-Upload-Metadata": json.dumps({"name_base64": name_b64}),
            "Content-Type": "application/octet-stream",
        }

        try:
            with open(path, "rb") as f:
                res = requests.post(
                    f"{CANVA_API_BASE}/asset-uploads",
                    headers=headers,
                    data=f.read(),
                    timeout=30,
                )

            if res.status_code not in (200, 201):
                logger.error("Canva asset upload failed (%s): %s", res.status_code, res.text)
                return {"success": False, "status_code": res.status_code, "error": res.text}

            data = res.json()
            job = data.get("job", {})
            job_id = job.get("id")
            if not job_id:
                return {"success": True, "asset": data.get("asset")}

            # Poll for completion
            poll_headers = {"Authorization": f"Bearer {self.access_token}"}
            start_time = time.time()
            while time.time() - start_time < timeout:
                poll_res = requests.get(f"{CANVA_API_BASE}/asset-uploads/{job_id}", headers=poll_headers, timeout=10)
                if poll_res.status_code == 200:
                    poll_data = poll_res.json().get("job", {})
                    if poll_data.get("status") == "success":
                        asset = poll_data.get("asset", {})
                        logger.info("Successfully uploaded and processed asset in Canva: %s", asset.get("id"))
                        return {"success": True, "asset": asset}
                    elif poll_data.get("status") in ("failed", "error"):
                        return {"success": False, "error": poll_data.get("error", "Asset upload processing failed")}
                time.sleep(1.0)
            return {"success": False, "error": f"Canva asset upload timed out after {timeout}s"}
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

    def generate_image(
        self,
        prompt: str,
        model: str = "craft_v1_2k",
        aspect_ratio: str = "portrait",
        timeout: float = 30.0,
    ) -> Optional[Any]:
        """Generates an image via Canva Connect Image Generation API.

        Uses model 'craft_v1_2k' (Canva Craft) or 'z_image_turbo' with async job polling.
        Returns a Pillow Image formatted to 1000x1500 (2:3 aspect ratio).
        """
        if not self.access_token:
            logger.debug("Canva access token not configured, skipping Canva AI image generation.")
            return None

        import io
        import time
        import uuid
        from PIL import Image, ImageOps

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        payload = {
            "prompt": prompt.strip(),
            "model": model,
            "aspect_ratio": aspect_ratio,
            "idempotency_key": str(uuid.uuid4()),
        }

        try:
            logger.info("🎨 [Canva AI] Invoking Canva Connect Image Generation (%s)...", model)
            # 1. Create Generation Job
            res = requests.post(
                f"{CANVA_API_BASE}/image-generations",
                headers=headers,
                json=payload,
                timeout=15,
            )
            if res.status_code not in (200, 201, 202):
                logger.warning("Canva image generation job creation failed (%s): %s", res.status_code, res.text)
                return None

            job_data = res.json().get("job", {})
            job_id = job_data.get("id")
            if not job_id:
                logger.warning("Canva image generation response missing job ID: %s", res.json())
                return None

            # 2. Poll for Completion (up to timeout)
            start_time = time.time()
            while time.time() - start_time < timeout:
                poll_res = requests.get(
                    f"{CANVA_API_BASE}/image-generations/{job_id}",
                    headers=headers,
                    timeout=10,
                )
                if poll_res.status_code == 200:
                    status_data = poll_res.json().get("job", {})
                    status = status_data.get("status")
                    if status == "success":
                        result = status_data.get("result", {})
                        image_url = result.get("url") or (result.get("image", {}).get("url"))
                        if image_url:
                            img_data = requests.get(image_url, timeout=15).content
                            img = Image.open(io.BytesIO(img_data)).convert("RGBA")
                            logger.info("✓ [Canva AI] Image generated and formatted to 1000x1500 successfully.")
                            return ImageOps.fit(img, (1000, 1500), method=Image.Resampling.LANCZOS)
                    elif status in ("failed", "error"):
                        logger.warning("Canva image generation job failed: %s", status_data)
                        return None
                time.sleep(2.0)
            logger.warning("Canva image generation timed out after %ss", timeout)
        except Exception as e:
            logger.warning("Error generating image via Canva: %s", e)
        return None
