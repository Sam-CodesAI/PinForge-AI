"""PinForge AI — Official 5-Pillar Pinterest Board Creator & Synchronizer.

Creates or synchronizes the 5 official Smart Spaces pillar boards on Pinterest API v5:
1. Room Organization
2. Small Apartment Hacks
3. Studio Living Ideas
4. Space Saving Kitchens
5. Closet & Wardrobe Organization
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Ensure repo root and python_engine are in sys.path
CURRENT_DIR = Path(__file__).resolve().parent
REPO_ROOT = CURRENT_DIR.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from python_engine.config import DATA_DIR, PINTEREST_ACCESS_TOKEN
from python_engine.pinterest_client import PinterestClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("PinForge.BoardCreator")

OFFICIAL_BOARDS = {
    "Room Organization": {
        "description": "Curated aesthetic room organization, bedroom storage, minimalist vanity setups, acrylic drawer dividers, and clutter-free living hacks for modern homes. 📌 Save your favorites!",
        "privacy": "PUBLIC",
    },
    "Small Apartment Hacks": {
        "description": "Clever space-saving solutions, renter-friendly vertical storage, no-drill shelving, slim rolling carts, and compact apartment organization ideas. 📌 Save for your next apartment move!",
        "privacy": "PUBLIC",
    },
    "Studio Living Ideas": {
        "description": "Aesthetic studio apartment layouts, multifunctional furniture, room dividers with storage, space zoning hacks, and micro-living inspiration. 📌 Save to your decor board!",
        "privacy": "PUBLIC",
    },
    "Space Saving Kitchens": {
        "description": "Smart small kitchen organization, sliding under-sink racks, magnetic refrigerator spice organizers, pantry storage, and clutter-free countertop ideas. 📌 Save this pin!",
        "privacy": "PUBLIC",
    },
    "Closet & Wardrobe Organization": {
        "description": "Minimalist wardrobe organization, cascading space-saving hangers, clear stackable shoe bins, closet decluttering hacks, and capsule closet storage. 📌 Save for wardrobe inspo!",
        "privacy": "PUBLIC",
    },
}


def sync_or_create_boards(token: Optional[str] = None) -> Dict[str, Any]:
    """Inspects Pinterest account boards and creates missing ones."""
    effective_token = (token or PINTEREST_ACCESS_TOKEN or os.getenv("PINTEREST_ACCESS_TOKEN", "")).strip()

    client = PinterestClient(access_token=effective_token)

    results: Dict[str, Any] = {
        "status": "in_progress",
        "boards": {},
        "created": [],
        "existing": [],
        "errors": [],
    }

    print("\n" + "═" * 72)
    print("📌 SMART SPACES 5-PILLAR PINTEREST BOARD CREATOR")
    print("═" * 72)

    # 1. Test live API authentication
    try:
        existing_boards = client.get_boards(force_refresh=True)
        existing_map = {b.get("name", "").strip().lower(): b.get("id") for b in existing_boards if b.get("id")}
        logger.info(f"Connected to Pinterest API v5. Found {len(existing_map)} existing boards on profile.")
    except Exception as auth_err:
        err_msg = str(auth_err)
        logger.warning(f"Live Pinterest authentication failed: {err_msg}")
        results["status"] = "auth_failed"
        results["auth_error"] = err_msg

        print("\n⚠️  PINTEREST API AUTHENTICATION REQUIRED")
        print("────────────────────────────────────────────────────────────────────────")
        print("To create these boards automatically via the Pinterest API v5:")
        print("Run:")
        print("  python -m python_engine.create_official_boards --token <YOUR_PINTEREST_ACCESS_TOKEN>")
        print("\nOr create them directly on Pinterest Web / Mobile app with these specs:\n")
        for idx, (b_name, meta) in enumerate(OFFICIAL_BOARDS.items(), start=1):
            print(f"{idx}. Name: {b_name}")
            print(f"   Privacy: {meta['privacy']}")
            print(f"   Description: {meta['description']}")
            print("   " + "-" * 66)
        print("═" * 72 + "\n")
        return results

    # 2. Iterate through 5 official pillars
    for b_name, meta in OFFICIAL_BOARDS.items():
        clean_key = b_name.lower()
        if clean_key in existing_map:
            board_id = existing_map[clean_key]
            logger.info(f"✓ Board already exists: '{b_name}' (ID: {board_id})")
            results["boards"][b_name] = board_id
            results["existing"].append(b_name)
        else:
            logger.info(f"Creating board on Pinterest: '{b_name}'...")
            try:
                res = client._request(
                    "boards",
                    method="POST",
                    data={
                        "name": b_name,
                        "description": meta["description"],
                        "privacy": meta["privacy"],
                    }
                )
                new_id = res.get("id")
                if new_id:
                    logger.info(f"🎉 Created board: '{b_name}' (ID: {new_id})")
                    results["boards"][b_name] = new_id
                    results["created"].append(b_name)
                else:
                    logger.error(f"Failed to create board '{b_name}': {res}")
                    results["errors"].append({"board": b_name, "error": str(res)})
            except Exception as create_err:
                logger.error(f"Error creating board '{b_name}': {create_err}")
                results["errors"].append({"board": b_name, "error": str(create_err)})

    # 3. Save board map to board_analytics.json
    board_analytics_path = DATA_DIR / "board_analytics.json"
    try:
        board_data = {}
        if board_analytics_path.exists():
            try:
                board_data = json.loads(board_analytics_path.read_text(encoding="utf-8"))
            except Exception:
                board_data = {}

        for b_name, b_id in results["boards"].items():
            if b_name not in board_data:
                board_data[b_name] = {
                    "board_id": b_id,
                    "pin_count": 0,
                    "avg_aes": 0.0,
                    "impressions": 0,
                    "pin_clicks": 0,
                    "outbound_clicks": 0,
                    "saves": 0,
                    "comments": 0,
                    "pin_ctr": 0.0,
                    "outbound_ctr": 0.0,
                }
            else:
                board_data[b_name]["board_id"] = b_id

        board_analytics_path.write_text(json.dumps(board_data, indent=2) + "\n", encoding="utf-8")
        logger.info(f"💾 Updated {board_analytics_path} with board mappings.")
    except Exception as e:
        logger.warning(f"Could not persist board analytics: {e}")

    results["status"] = "success" if not results["errors"] else "partial_success"
    print("\n" + "═" * 72)
    print(f"📊 SUMMARY: {len(results['existing'])} Existing, {len(results['created'])} Created, {len(results['errors'])} Errors")
    print("═" * 72 + "\n")
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create official Smart Spaces Pinterest boards")
    parser.add_argument("--token", type=str, default=None, help="Pinterest API access token")
    args = parser.parse_args()

    sync_or_create_boards(token=args.token)
