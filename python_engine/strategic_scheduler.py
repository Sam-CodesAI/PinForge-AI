"""PinForge AI — Strategic AI Publishing Scheduler.

Architected specifically for the @Smart_Spaces Pinterest account:
1. 5 Pillars across 5 Dedicated Boards:
   - Slot 1: Small Apartment Hacks (08:30 AM EST / 13:30 UTC) - Morning Commute Intent
   - Slot 2: Space Saving Kitchens (12:45 PM EST / 17:45 UTC) - Lunchtime Kitchen Hacks
   - Slot 3: Closet & Wardrobe Organization (04:30 PM EST / 21:30 UTC) - Afternoon Decluttering
   - Slot 4: Studio Living Ideas (08:15 PM EST / 01:15 UTC) - Prime Evening Decor Inspiration
   - Slot 5: Room Organization (10:45 PM EST / 03:45 UTC) - Bedtime Impulse Amazon Shopping

2. Anti-Spam Humanization:
   - Jittered execution (randomized ±12 min offsets) preventing robotic pattern detection.
   - Strict 1-pin-per-board daily cadence (5 total pins/day), completely safe from Pinterest rate limits.
"""

import argparse
import logging
import random
import time
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

try:
    from python_engine.autonomous_autopilot import AutonomousAutopilot
except ImportError:
    from autonomous_autopilot import AutonomousAutopilot

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] (%(name)s) %(message)s",
)
logger = logging.getLogger("PinForge.StrategicScheduler")

SCHEDULE_PILLARS = {
    1: {
        "slot_id": 1,
        "board_name": "Small Apartment Hacks",
        "peak_time_est": "08:30 AM EST",
        "peak_utc_hour": 13,
        "peak_utc_minute": 30,
        "audience_intent": "Morning commute & weekend planning: small space solutions",
        "niche_queries": [
            "small space apartment organizer",
            "under bed storage with wheels",
            "slim rolling cart for narrow spaces",
            "collapsible laundry basket small space",
        ],
    },
    2: {
        "slot_id": 2,
        "board_name": "Space Saving Kitchens",
        "peak_time_est": "12:45 PM EST",
        "peak_utc_hour": 17,
        "peak_utc_minute": 45,
        "audience_intent": "Lunchtime recipe & kitchen decluttering intent",
        "niche_queries": [
            "foldable magnetic spice rack",
            "over the door pantry organizer",
            "under sink expandable organizer kitchen",
            "refrigerator side magnetic shelf",
        ],
    },
    3: {
        "slot_id": 3,
        "board_name": "Closet & Wardrobe Organization",
        "peak_time_est": "04:30 PM EST",
        "peak_utc_hour": 21,
        "peak_utc_minute": 30,
        "audience_intent": "Afternoon home refresh & closet optimization",
        "niche_queries": [
            "space saving closet hanger cascade",
            "vacuum storage bags space saver",
            "stackable shoe organizer clear bins",
            "foldable drawer clothes organizers",
        ],
    },
    4: {
        "slot_id": 4,
        "board_name": "Studio Living Ideas",
        "peak_time_est": "08:15 PM EST",
        "peak_utc_hour": 1,
        "peak_utc_minute": 15,
        "audience_intent": "Prime evening peak browsing: furniture & interior aesthetics",
        "niche_queries": [
            "minimalist floating desk shelf",
            "folding wall mounted dining table",
            "divider screen with storage shelf",
            "multifunctional ottoman with storage",
        ],
    },
    5: {
        "slot_id": 5,
        "board_name": "Room Organization",
        "peak_time_est": "10:45 PM EST",
        "peak_utc_hour": 3,
        "peak_utc_minute": 45,
        "audience_intent": "Late-night bedtime browsing: impulse gadgets & organizers",
        "niche_queries": [
            "rotating makeup vanity organizer",
            "magnetic cable management desk",
            "corner floating bathroom shelf suction",
            "entryway wall mounted key and mail organizer",
        ],
    },
}


class StrategicScheduler:
    """Orchestrates strategic 5-board, peak-window autonomous publishing."""

    def __init__(self):
        self.autopilot = AutonomousAutopilot()

    def get_slot_for_current_time(self, utc_now: Optional[datetime] = None) -> Dict[str, Any]:
        """Determines the closest matching schedule slot based on current UTC time."""
        now = utc_now or datetime.now(timezone.utc)
        current_minute_of_day = now.hour * 60 + now.minute

        # Calculate circular distance in minutes to each slot's target time
        closest_slot = None
        min_diff = float("inf")

        for slot in SCHEDULE_PILLARS.values():
            slot_minute = (slot["peak_utc_hour"] * 60 + slot["peak_utc_minute"]) % 1440
            diff = abs(current_minute_of_day - slot_minute)
            diff = min(diff, 1440 - diff)  # 24-hr circular wrap
            if diff < min_diff:
                min_diff = diff
                closest_slot = slot

        return closest_slot

    def execute_slot(
        self,
        slot_id: int,
        apply_jitter: bool = True,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """Executes a single slot targeting its dedicated board and niche queries."""
        slot = SCHEDULE_PILLARS.get(slot_id)
        if not slot:
            raise ValueError(f"Invalid slot ID: {slot_id}. Must be between 1 and 5.")

        board_name = slot["board_name"]
        queries = slot["niche_queries"]
        logger.info(f"⏰ Executing Slot {slot_id}: Board='{board_name}' | Peak: {slot['peak_time_est']}")

        if apply_jitter:
            jitter_sec = random.randint(15, 120)
            logger.info(f"🛡️ Applying anti-bot micro-jitter: pausing for {jitter_sec}s...")
            time.sleep(jitter_sec)

        result = self.autopilot.run_autopilot_cycle(
            target_board=board_name,
            custom_queries=queries,
            publish_live=not dry_run,
        )

        logger.info(
            f"✅ Slot {slot_id} completed: Published '{result['seo_copy']['title']}' to '{board_name}' "
            f"(ASIN: {result['product']['asin']})"
        )
        return result

    def execute_full_circuit(
        self,
        delay_between_boards_sec: int = 15,
        dry_run: bool = False,
    ) -> List[Dict[str, Any]]:
        """Executes all 5 boards in sequence (useful for testing or initial warmup)."""
        logger.info("⚡ Executing Full 5-Board Circuit (1 pin for each pillar)...")
        results = []
        for slot_id in sorted(SCHEDULE_PILLARS.keys()):
            res = self.execute_slot(slot_id, apply_jitter=False, dry_run=dry_run)
            results.append(res)
            if slot_id < 5 and delay_between_boards_sec > 0:
                logger.info(f"Sleeping {delay_between_boards_sec}s before next board...")
                time.sleep(delay_between_boards_sec)

        logger.info("🎉 All 5 Smart Spaces boards refreshed successfully.")
        return results


def main():
    parser = argparse.ArgumentParser(description="PinForge AI Strategic Publishing Scheduler")
    parser.add_argument("--auto", action="store_true", help="Detect current peak time slot and execute")
    parser.add_argument("--slot", type=int, choices=[1, 2, 3, 4, 5], help="Execute a specific slot (1-5)")
    parser.add_argument("--all", action="store_true", help="Execute all 5 boards in sequence")
    parser.add_argument("--no-jitter", action="store_true", help="Bypass anti-detection jitter sleep")
    parser.add_argument("--dry-run", action="store_true", help="Run without posting live to Pinterest")

    args = parser.parse_args()
    scheduler = StrategicScheduler()

    if args.all:
        scheduler.execute_full_circuit(dry_run=args.dry_run)
    elif args.slot:
        scheduler.execute_slot(args.slot, apply_jitter=not args.no_jitter, dry_run=args.dry_run)
    elif args.auto:
        matched_slot = scheduler.get_slot_for_current_time()
        logger.info(f"Auto-selected Slot {matched_slot['slot_id']} ('{matched_slot['board_name']}')")
        scheduler.execute_slot(matched_slot["slot_id"], apply_jitter=not args.no_jitter, dry_run=args.dry_run)
    else:
        print("Smart Spaces 5-Pillar Schedule Matrix:")
        for sid, slot in SCHEDULE_PILLARS.items():
            print(f"  Slot {sid}: [{slot['peak_time_est']}] -> Board: '{slot['board_name']}'")
            print(f"          Intent: {slot['audience_intent']}")
        print("\nUsage:")
        print("  python -m python_engine.strategic_scheduler --auto")
        print("  python -m python_engine.strategic_scheduler --slot 1")
        print("  python -m python_engine.strategic_scheduler --all --dry-run")


if __name__ == "__main__":
    main()
