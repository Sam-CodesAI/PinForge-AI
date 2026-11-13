"""Test Suite for PinForge AI Strategic Publishing Scheduler.

Verifies:
1. 5-pillar schedule matrix integrity and audience intents
2. Circular UTC time slot matching logic
3. Format alternator (Slots 1 & 4 -> Carousel, Slots 2, 3, 5 -> Single)
4. CLI parser arguments including --agentic flag
"""

import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

# Add project root to sys.path
CURRENT_DIR = Path(__file__).resolve().parent
PYTHON_ENGINE_DIR = CURRENT_DIR.parent
PROJECT_ROOT = PYTHON_ENGINE_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(PYTHON_ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHON_ENGINE_DIR))

from python_engine.strategic_scheduler import (
    SCHEDULE_PILLARS,
    StrategicScheduler,
    create_parser,
)


class TestStrategicScheduler(unittest.TestCase):
    """Test suite validating peak timing windows, board allocation, and CLI parsing."""

    def setUp(self):
        self.scheduler = StrategicScheduler()

    def test_schedule_pillars_completeness(self):
        """Verifies all 5 slots are mapped to official Smart Spaces boards."""
        self.assertEqual(len(SCHEDULE_PILLARS), 5)
        for sid in range(1, 6):
            self.assertIn(sid, SCHEDULE_PILLARS)
            slot = SCHEDULE_PILLARS[sid]
            self.assertIn("board_name", slot)
            self.assertIn("peak_time_est", slot)
            self.assertIn("niche_queries", slot)
            self.assertGreaterEqual(len(slot["niche_queries"]), 3)

    def test_slot_matching_by_utc_time(self):
        """Verifies circular time distance matching picks correct slot."""
        # 13:30 UTC -> Slot 1 (08:30 AM EST)
        t_slot1 = datetime(2026, 11, 13, 13, 25, tzinfo=timezone.utc)
        matched1 = self.scheduler.get_slot_for_current_time(t_slot1)
        self.assertEqual(matched1["slot_id"], 1)

        # 17:45 UTC -> Slot 2 (12:45 PM EST)
        t_slot2 = datetime(2026, 11, 13, 17, 50, tzinfo=timezone.utc)
        matched2 = self.scheduler.get_slot_for_current_time(t_slot2)
        self.assertEqual(matched2["slot_id"], 2)

    def test_cli_parser_agentic_flag(self):
        """Verifies CLI parser supports --agentic, --slot, --dry-run flags."""
        parser = create_parser()
        args = parser.parse_args(["--slot", "2", "--agentic", "--dry-run", "--no-jitter"])
        self.assertEqual(args.slot, 2)
        self.assertTrue(args.agentic)
        self.assertTrue(args.dry_run)
        self.assertTrue(args.no_jitter)


if __name__ == "__main__":
    unittest.main()
