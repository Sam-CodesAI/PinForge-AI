"""PinForge AI — Agentic Swarm Persistent Memory Store.

Persists learned strategies, template performance weights, winning hook patterns,
and quality score history in agent_memory.json across publishing cycles.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional

from .models import MemoryInsights

logger = logging.getLogger("pinforge.agentic.memory")

# Locate persistent data directory
CURRENT_DIR = Path(__file__).resolve().parent
DATA_DIR = CURRENT_DIR.parent / "data"
MEMORY_FILE = DATA_DIR / "agent_memory.json"


class SwarmMemory:
    """Manages persistent knowledge, heuristics, and performance feedback."""

    def __init__(self, memory_path: Optional[Path] = None):
        self.path = memory_path or MEMORY_FILE
        self.insights: MemoryInsights = self._load()

    def _load(self) -> MemoryInsights:
        """Loads memory from disk or instantiates default baseline insights."""
        if self.path.exists():
            try:
                data = json.loads(self.path.read_text(encoding="utf-8"))
                return MemoryInsights.model_validate(data)
            except Exception as e:
                logger.warning(f"Failed to load agent memory from {self.path}: {e}. Initializing baseline.")
        return MemoryInsights()

    def save(self) -> None:
        """Persists memory state atomically to disk."""
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(
                self.insights.model_dump_json(indent=2),
                encoding="utf-8"
            )
            logger.info(f"💾 Swarm memory saved to {self.path.name} (Total pins: {self.insights.total_pins_published})")
        except Exception as e:
            logger.error(f"Failed to write agent memory to {self.path}: {e}")

    def record_successful_pin(
        self,
        pin_id: str,
        board: str,
        template: str,
        score: float
    ) -> None:
        """Records a successful pin generation and updates running score statistics."""
        prev_total = self.insights.total_pins_published
        self.insights.total_pins_published += 1
        
        # Incremental moving average calculation
        curr_avg = self.insights.historical_avg_score
        new_avg = ((curr_avg * prev_total) + score) / self.insights.total_pins_published
        self.insights.historical_avg_score = round(new_avg, 2)

        # Ensure board is prioritized
        if board not in self.insights.high_converting_boards:
            self.insights.high_converting_boards.insert(0, board)

        self.save()

    def get_preferred_template_for_board(self, board_name: str) -> str:
        """Selects optimal template variant based on historical board performance."""
        board_lower = board_name.lower()
        if "studio" in board_lower or "apartment" in board_lower:
            return "track_a_lifestyle"
        elif "kitchen" in board_lower or "closet" in board_lower:
            return "carousel_suite"
        else:
            return "warm_editorial"
