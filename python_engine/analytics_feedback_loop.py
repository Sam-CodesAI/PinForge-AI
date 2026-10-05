"""PinForge AI — Closed-Loop Performance Analytics & Algorithmic Feedback Loop.

Queries Pinterest API v5 to evaluate pin engagement, calculates the Algorithmic
Engagement Score (AES), and updates the performance ledger for continuous self-learning:
    AES = (5 * outbound_click + 3 * save + 1.5 * pin_click + 2 * comment) / max(impressions, 10) * 100

Saves rankings and board metrics to:
    python_engine/data/performance_ledger.json
"""

from __future__ import annotations

import argparse
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from python_engine.pinterest_client import PinterestClient
    from python_engine.config import DATA_DIR
except ImportError:
    from pinterest_client import PinterestClient
    from config import DATA_DIR

logger = logging.getLogger("PinForge.AnalyticsLoop")
PERFORMANCE_LEDGER_FILE = DATA_DIR / "performance_ledger.json"
PUBLISHED_PINS_FILE = DATA_DIR / "published_pins.json"


def calculate_aes(
    impressions: int,
    saves: int,
    outbound_clicks: int,
    pin_clicks: int,
    comments: int,
) -> float:
    """Computes the Algorithmic Engagement Score (AES).

    Formula:
    (5 * outbound_click + 3 * save + 1.5 * pin_click + 2 * comment) / max(impressions, 10) * 100
    """
    denominator = max(impressions, 10)
    raw_score = (
        (5.0 * outbound_clicks)
        + (3.0 * saves)
        + (1.5 * pin_clicks)
        + (2.0 * comments)
    ) / denominator * 100.0

    return round(raw_score, 2)


class AnalyticsFeedbackLoop:
    """Closed-loop analytics aggregator and self-learning feedback system."""

    def __init__(self, client: Optional[PinterestClient] = None):
        self.client = client or PinterestClient()

    def fetch_published_pins(self, page_size: int = 100) -> List[Dict[str, Any]]:
        """Fetch pins from Pinterest API v5 and merge with local published_pins ledger."""
        pins_by_id: Dict[str, Dict[str, Any]] = {}

        # 1. Load local published pins ledger
        if PUBLISHED_PINS_FILE.exists():
            try:
                local_pins = json.loads(PUBLISHED_PINS_FILE.read_text())
                for p in local_pins:
                    p_id = str(p.get("id", "")).strip()
                    if p_id:
                        pins_by_id[p_id] = p
            except Exception as e:
                logger.warning(f"Could not read published_pins.json: {e}")

        # 2. Query Pinterest API if configured
        if self.client.is_configured:
            try:
                endpoint = f"pins?page_size={min(page_size, 100)}"
                res = self.client._request(endpoint)
                items = res.get("items", [])
                for item in items:
                    p_id = str(item.get("id", "")).strip()
                    if p_id:
                        if p_id in pins_by_id:
                            pins_by_id[p_id].update(item)
                        else:
                            pins_by_id[p_id] = item
                logger.info(f"Fetched {len(items)} pins from Pinterest API v5.")
            except Exception as e:
                logger.warning(f"Failed to fetch live pins from Pinterest API: {e}")

        return list(pins_by_id.values())

    def fetch_pin_metrics(self, pin_id: str) -> Dict[str, int]:
        """Fetch engagement metrics for a specific pin from Pinterest API v5."""
        metrics = {
            "impressions": 0,
            "saves": 0,
            "outbound_clicks": 0,
            "pin_clicks": 0,
            "comments": 0,
        }

        if not self.client.is_configured:
            return metrics

        try:
            endpoint = f"pins/{pin_id}?pin_metrics=true"
            data = self.client._request(endpoint)

            # Pinterest v5 metrics structure extraction
            raw_metrics = (
                data.get("pin_metrics")
                or data.get("lifetime_metrics")
                or data.get("metrics", {})
            )

            if isinstance(raw_metrics, dict):
                # Check for nested lifetime metrics if present
                sub = raw_metrics.get("lifetime_metrics") or raw_metrics
                metrics["impressions"] = int(sub.get("impression") or sub.get("IMPRESSION") or 0)
                metrics["saves"] = int(sub.get("save") or sub.get("SAVE") or 0)
                metrics["outbound_clicks"] = int(
                    sub.get("outbound_click") or sub.get("OUTBOUND_CLICK") or sub.get("clickthrough") or 0
                )
                metrics["pin_clicks"] = int(
                    sub.get("pin_click") or sub.get("PIN_CLICK") or sub.get("closeup") or 0
                )
                metrics["comments"] = int(sub.get("comment") or sub.get("COMMENT") or 0)

        except Exception as e:
            logger.warning(f"Could not fetch metrics for pin {pin_id}: {e}")

        return metrics

    def run_analytics_loop(self, dry_run: bool = False, limit: int = 100) -> Dict[str, Any]:
        """Executes full analytics evaluation cycle, computes AES, and persists performance ledger."""
        logger.info("📊 Starting Closed-Loop Performance Analytics cycle...")
        DATA_DIR.mkdir(parents=True, exist_ok=True)

        pins = self.fetch_published_pins(page_size=limit)
        evaluated_pins: List[Dict[str, Any]] = []
        board_metrics: Dict[str, Dict[str, Any]] = {}

        if not pins and dry_run:
            # Generate deterministic sample records for dry-run verification
            pins = [
                {
                    "id": "dry_run_pin_001",
                    "title": "Magnetic Foldable Spice Rack Organizer",
                    "board_id": "Space Saving Kitchens",
                    "link": "https://www.amazon.com/dp/B0BYP6DZ53?tag=smartspace07-21",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "simulated_metrics": {
                        "impressions": 1420,
                        "saves": 58,
                        "outbound_clicks": 42,
                        "pin_clicks": 95,
                        "comments": 7,
                    },
                },
                {
                    "id": "dry_run_pin_002",
                    "title": "Ultra-Slim 5.1\" Rolling Cart Narrow Gap Organizer",
                    "board_id": "Small Apartment Hacks",
                    "link": "https://www.amazon.com/dp/B08C1W5N87?tag=smartspace07-21",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "simulated_metrics": {
                        "impressions": 2100,
                        "saves": 89,
                        "outbound_clicks": 74,
                        "pin_clicks": 140,
                        "comments": 12,
                    },
                },
                {
                    "id": "dry_run_pin_003",
                    "title": "Cascade Clothes Hanger Space Saving Organizer",
                    "board_id": "Closet & Wardrobe Organization",
                    "link": "https://www.amazon.com/dp/B09XS7JWHH?tag=smartspace07-21",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "simulated_metrics": {
                        "impressions": 980,
                        "saves": 35,
                        "outbound_clicks": 22,
                        "pin_clicks": 54,
                        "comments": 4,
                    },
                },
            ]

        for p in pins[:limit]:
            p_id = str(p.get("id") or "").strip()
            p_title = p.get("title") or "Smart Spaces Pin"
            b_name = p.get("board_id") or p.get("board_name") or "Room Organization"
            p_link = p.get("link") or ""

            if dry_run and "simulated_metrics" in p:
                m = p["simulated_metrics"]
            elif self.client.is_configured and p_id and not p_id.startswith("dry_run"):
                m = self.fetch_pin_metrics(p_id)
            else:
                m = {
                    "impressions": 0,
                    "saves": 0,
                    "outbound_clicks": 0,
                    "pin_clicks": 0,
                    "comments": 0,
                }

            score = calculate_aes(
                impressions=m["impressions"],
                saves=m["saves"],
                outbound_clicks=m["outbound_clicks"],
                pin_clicks=m["pin_clicks"],
                comments=m["comments"],
            )

            record = {
                "pin_id": p_id,
                "title": p_title,
                "board": b_name,
                "link": p_link,
                "metrics": m,
                "aes_score": score,
                "evaluated_at": datetime.now(timezone.utc).isoformat(),
            }
            evaluated_pins.append(record)

            # Aggregate by board
            if b_name not in board_metrics:
                board_metrics[b_name] = {
                    "total_pins": 0,
                    "total_impressions": 0,
                    "total_saves": 0,
                    "total_outbound_clicks": 0,
                    "total_pin_clicks": 0,
                    "total_comments": 0,
                    "sum_aes": 0.0,
                }
            bm = board_metrics[b_name]
            bm["total_pins"] += 1
            bm["total_impressions"] += m["impressions"]
            bm["total_saves"] += m["saves"]
            bm["total_outbound_clicks"] += m["outbound_clicks"]
            bm["total_pin_clicks"] += m["pin_clicks"]
            bm["total_comments"] += m["comments"]
            bm["sum_aes"] += score

        # Compute board averages
        board_summary = {}
        for b_name, bm in board_metrics.items():
            cnt = max(bm["total_pins"], 1)
            board_summary[b_name] = {
                "pin_count": bm["total_pins"],
                "avg_aes": round(bm["sum_aes"] / cnt, 2),
                "total_outbound_clicks": bm["total_outbound_clicks"],
                "total_saves": bm["total_saves"],
                "total_impressions": bm["total_impressions"],
            }

        # Sort pins by AES descending
        ranked_pins = sorted(evaluated_pins, key=lambda x: x["aes_score"], reverse=True)

        ledger_payload = {
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "formula": "AES = (5 * outbound_click + 3 * save + 1.5 * pin_click + 2 * comment) / max(impressions, 10) * 100",
            "total_pins_evaluated": len(ranked_pins),
            "top_performing_pins": ranked_pins[:20],
            "board_performance_summary": board_summary,
            "all_ranked_pins": ranked_pins,
        }

        try:
            PERFORMANCE_LEDGER_FILE.write_text(json.dumps(ledger_payload, indent=2))
            logger.info(f"💾 Performance ledger successfully saved to {PERFORMANCE_LEDGER_FILE}")
        except Exception as e:
            logger.error(f"Failed to write performance ledger: {e}")

        return ledger_payload


def main():
    parser = argparse.ArgumentParser(description="PinForge AI Closed-Loop Performance Analytics")
    parser.add_argument("--dry-run", action="store_true", help="Run in test mode with mock data")
    parser.add_argument("--limit", type=int, default=100, help="Maximum pins to evaluate")
    parser.add_argument("--verbose", action="store_true", help="Print complete ranked report")

    args = parser.parse_args()
    loop = AnalyticsFeedbackLoop()
    report = loop.run_analytics_loop(dry_run=args.dry_run, limit=args.limit)

    print("\n================ PINFORGE CLOSED-LOOP PERFORMANCE LEDGER ================")
    print(f"Timestamp: {report.get('last_updated')}")
    print(f"Total Pins Evaluated: {report.get('total_pins_evaluated')}")
    print("\n--- Top Performing Pins (Ranked by AES) ---")
    for idx, pin in enumerate(report.get("top_performing_pins", [])[:5], start=1):
        m = pin["metrics"]
        print(f"  #{idx} [AES: {pin['aes_score']}] {pin['title']}")
        print(f"      Board: {pin['board']} | Outbound: {m['outbound_clicks']} | Saves: {m['saves']} | Impr: {m['impressions']}")

    print("\n--- Board Pillar Performance Summary ---")
    for b_name, b_data in report.get("board_performance_summary", {}).items():
        print(f"  - Board: '{b_name}' -> Avg AES: {b_data['avg_aes']} | Clicks: {b_data['total_outbound_clicks']} | Pins: {b_data['pin_count']}")
    print("========================================================================\n")


if __name__ == "__main__":
    main()
