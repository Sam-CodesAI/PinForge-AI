"""PinForge AI — Unified Supabase / PostgreSQL Storage Gateway.

Implements durable relational persistence for:
1. pinforge_pins (ASIN, title, board, image, affiliate URL)
2. pinforge_analytics (impressions, clicks, outbound clicks, saves, Bayesian AES)
Matches ecosystem migration 20261104_unify_ecosystem.sql with graceful local JSON fallback.
"""

from __future__ import annotations

import json
import logging
import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx

from python_engine.config import DATA_DIR

logger = logging.getLogger("pinforge.storage")

ASIN_REGEX = re.compile(r"(?:/dp/|/gp/product/|/gp/aw/d/|/d/|/product/)([A-Z0-9]{10})(?:[/?#]|$)", re.IGNORECASE)

PUBLISHED_PINS_FILE = DATA_DIR / "published_pins.json"
PERFORMANCE_LEDGER_FILE = DATA_DIR / "performance_ledger.json"
ACCOUNT_OVERVIEW_FILE = DATA_DIR / "account_overview.json"
BOARD_ANALYTICS_FILE = DATA_DIR / "board_analytics.json"


def extract_asin(url_or_text: str) -> str:
    """Extract 10-character Amazon ASIN from URL or raw string."""
    if not url_or_text:
        return "UNKNOWN"
    m = ASIN_REGEX.search(url_or_text)
    if m:
        return m.group(1).upper()
    raw = url_or_text.strip().upper()
    if len(raw) == 10 and raw.isalnum():
        return raw
    return "UNKNOWN"


class SupabaseStorageGateway:
    """Durable Supabase datastore with zero-crash local JSON fallback."""

    def __init__(
        self,
        supabase_url: Optional[str] = None,
        supabase_key: Optional[str] = None,
    ):
        raw_url = (
            supabase_url
            or os.getenv("NEXT_PUBLIC_SUPABASE_URL")
            or os.getenv("SUPABASE_URL")
            or ""
        ).strip().rstrip("/")
        raw_key = (
            supabase_key
            or os.getenv("SUPABASE_SERVICE_ROLE_KEY")
            or os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")
            or os.getenv("SUPABASE_ANON_KEY")
            or ""
        ).strip()

        self.supabase_url = raw_url
        self.supabase_key = raw_key
        self.is_configured = bool(
            self.supabase_url
            and self.supabase_key
            and "placeholder" not in self.supabase_url
            and "your-project" not in self.supabase_url
        )

        self._headers = {
            "apikey": self.supabase_key,
            "Authorization": f"Bearer {self.supabase_key}",
            "Content-Type": "application/json",
            "Prefer": "resolution=merge-duplicates,return=minimal",
        }

    # --------------------------------------------------------------------------
    # Published Pins
    # --------------------------------------------------------------------------
    def save_published_pin(self, pin_record: Dict[str, Any]) -> None:
        """Persist single pin to Supabase pinforge_pins and local JSON ledger."""
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        pin_id = str(pin_record.get("id") or pin_record.get("pin_id") or "").strip()
        if not pin_id:
            return

        link = str(pin_record.get("link") or pin_record.get("affiliate_url") or "")
        asin = str(pin_record.get("asin") or extract_asin(link))
        title = str(pin_record.get("title") or "Smart Spaces Pin")
        board_id = str(pin_record.get("board_id") or "")
        board_name = str(pin_record.get("board_name") or "Room Organization")
        image_url = str(pin_record.get("image_url") or pin_record.get("thumbnail_url") or "")
        created_at = pin_record.get("created_at") or datetime.now(timezone.utc).isoformat()

        # 1. Update local JSON ledger
        try:
            pins: List[Dict[str, Any]] = []
            if PUBLISHED_PINS_FILE.exists():
                try:
                    pins = json.loads(PUBLISHED_PINS_FILE.read_text(encoding="utf-8"))
                except Exception:
                    pins = []

            local_entry = {
                "id": pin_id,
                "title": title,
                "link": link,
                "board_id": board_id,
                "board_name": board_name,
                "is_carousel": bool(pin_record.get("is_carousel")),
                "created_at": created_at,
            }

            existing_idx = next((i for i, p in enumerate(pins) if p.get("id") == pin_id), None)
            if existing_idx is not None:
                pins[existing_idx] = local_entry
            else:
                pins.append(local_entry)

            PUBLISHED_PINS_FILE.write_text(json.dumps(pins, indent=2), encoding="utf-8")
        except Exception as err:
            logger.warning(f"Failed to write published_pins.json: {err}")

        # 2. Durable Supabase write
        if self.is_configured:
            try:
                row = {
                    "pin_id": pin_id,
                    "asin": asin,
                    "title": title,
                    "board_id": board_id,
                    "board_name": board_name,
                    "image_url": image_url,
                    "affiliate_url": link,
                    "created_at": created_at,
                }
                endpoint = f"{self.supabase_url}/rest/v1/pinforge_pins?on_conflict=pin_id"
                with httpx.Client(timeout=5.0) as client:
                    resp = client.post(endpoint, headers=self._headers, json=[row])
                    if resp.status_code >= 400:
                        logger.warning(f"Supabase pinforge_pins insert error {resp.status_code}: {resp.text}")
            except Exception as e:
                logger.warning(f"Durable Supabase write skipped: {e}")

    def load_published_pins(self) -> List[Dict[str, Any]]:
        """Load published pins from Supabase or fallback to published_pins.json."""
        if self.is_configured:
            try:
                endpoint = f"{self.supabase_url}/rest/v1/pinforge_pins?select=*&order=created_at.desc"
                with httpx.Client(timeout=5.0) as client:
                    resp = client.get(endpoint, headers=self._headers)
                    if resp.status_code == 200:
                        rows = resp.json()
                        if isinstance(rows, list) and rows:
                            return [
                                {
                                    "id": r.get("pin_id") or r.get("id"),
                                    "title": r.get("title"),
                                    "link": r.get("affiliate_url"),
                                    "board_id": r.get("board_id"),
                                    "board_name": r.get("board_name"),
                                    "image_url": r.get("image_url"),
                                    "created_at": r.get("created_at"),
                                }
                                for r in rows
                            ]
            except Exception as e:
                logger.warning(f"Failed to query Supabase pinforge_pins: {e}")

        if PUBLISHED_PINS_FILE.exists():
            try:
                return json.loads(PUBLISHED_PINS_FILE.read_text(encoding="utf-8"))
            except Exception:
                pass
        return []

    # --------------------------------------------------------------------------
    # Analytics & Feedback Loop Persistence
    # --------------------------------------------------------------------------
    def sync_analytics_cycle(
        self,
        ranked_pins: List[Dict[str, Any]],
        account_overview: Dict[str, Any],
        board_summary: Dict[str, Any],
        sync_published_list: List[Dict[str, Any]],
    ) -> None:
        """Persist closed-loop analytics to Supabase (pinforge_pins + pinforge_analytics) & local JSON."""
        DATA_DIR.mkdir(parents=True, exist_ok=True)

        # 1. Write local JSON files for atomic offline compatibility
        ledger_payload = {
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "formula": "AES = (5 * outbound_click + 3 * save + 1.5 * pin_click + 2 * comment) / max(impressions, 10) * 100",
            "total_pins_evaluated": len(ranked_pins),
            "top_performing_pins": ranked_pins[:25],
            "board_performance_summary": board_summary,
            "all_ranked_pins": ranked_pins,
        }

        try:
            PERFORMANCE_LEDGER_FILE.write_text(json.dumps(ledger_payload, indent=2), encoding="utf-8")
            ACCOUNT_OVERVIEW_FILE.write_text(json.dumps(account_overview, indent=2), encoding="utf-8")
            BOARD_ANALYTICS_FILE.write_text(json.dumps(board_summary, indent=2), encoding="utf-8")
            PUBLISHED_PINS_FILE.write_text(json.dumps(sync_published_list, indent=2), encoding="utf-8")
            logger.info("💾 All local JSON analytics files updated successfully.")
        except Exception as e:
            logger.error(f"Failed writing local analytics files: {e}")

        # 2. Sync to Supabase pinforge_pins and pinforge_analytics tables
        if not self.is_configured:
            return

        try:
            pins_to_upsert = []
            analytics_to_insert = []
            recorded_at = datetime.now(timezone.utc).isoformat()

            for pin in ranked_pins:
                p_id = str(pin.get("pin_id") or pin.get("id") or "").strip()
                if not p_id:
                    continue

                link = str(pin.get("link") or "")
                asin = extract_asin(link)
                m = pin.get("metrics") or {}

                pins_to_upsert.append({
                    "pin_id": p_id,
                    "asin": asin,
                    "title": pin.get("title") or "Smart Spaces Pin",
                    "board_id": str(pin.get("board_id") or ""),
                    "board_name": pin.get("board") or "Room Organization",
                    "image_url": pin.get("thumbnail_url") or "",
                    "affiliate_url": link,
                    "created_at": pin.get("created_at") or recorded_at,
                })

                analytics_to_insert.append({
                    "pin_id": p_id,
                    "impressions": int(m.get("impressions") or 0),
                    "pin_clicks": int(m.get("pin_clicks") or 0),
                    "outbound_clicks": int(m.get("outbound_clicks") or 0),
                    "saves": int(m.get("saves") or 0),
                    "bayesian_aes": float(pin.get("aes_score") or 0.0),
                    "recorded_at": recorded_at,
                })

            with httpx.Client(timeout=8.0) as client:
                if pins_to_upsert:
                    client.post(
                        f"{self.supabase_url}/rest/v1/pinforge_pins?on_conflict=pin_id",
                        headers=self._headers,
                        json=pins_to_upsert,
                    )
                if analytics_to_insert:
                    client.post(
                        f"{self.supabase_url}/rest/v1/pinforge_analytics",
                        headers=self._headers,
                        json=analytics_to_insert,
                    )
            logger.info("⚡ Synchronized analytics into Supabase pinforge_pins & pinforge_analytics.")
        except Exception as e:
            logger.warning(f"Supabase analytics batch sync skipped: {e}")


# Global storage gateway singleton
default_storage = SupabaseStorageGateway()
