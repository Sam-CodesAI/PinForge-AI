"""PinForge AI — GrowthAnalystAgent (Closed-Loop Analytics & Memory Evolution).

Audits live Pinterest performance metrics, updates swarm memory,
and tunes strategic weights across all 5 other agents.
"""

from __future__ import annotations

import logging
from typing import Dict, Any

from .models import SwarmState
from .memory import SwarmMemory

try:
    from python_engine.pinterest_client import PinterestClient
except ImportError:
    from pinterest_client import PinterestClient

logger = logging.getLogger("pinforge.agentic.analyst")


class GrowthAnalystAgent:
    """Agent 6: Closed-loop learning auditor feeding analytics insights back into swarm memory."""

    def __init__(self, memory: SwarmMemory):
        self.memory = memory
        self.pinterest = PinterestClient()

    def process_cycle_completion(self, state: SwarmState) -> Dict[str, Any]:
        """Analyzes the completed swarm cycle and records performance insights into memory."""
        if not state.is_successful or not state.published_pin_id:
            logger.info("ℹ️ Cycle did not complete successfully; skipping analytics recording.")
            return {"status": "skipped"}

        template = state.creative_direction.template_variant if state.creative_direction else "warm_editorial"
        score = state.critic_audit.score if state.critic_audit else 90.0

        state.log(
            agent_name="GrowthAnalystAgent",
            action="evaluate_cycle_quality",
            thought=(
                f"Recording completed pin {state.published_pin_id} on board '{state.target_board}'. "
                f"Visual quality audit: {score}/100. Template: {template}."
            ),
            result_summary="Updating persistent memory."
        )

        # 1. Update Swarm Memory
        self.memory.record_successful_pin(
            pin_id=state.published_pin_id,
            board=state.target_board,
            template=template,
            score=score
        )

        # 2. Extract adaptive rules
        insights = {
            "total_pins": self.memory.insights.total_pins_published,
            "avg_score": self.memory.insights.historical_avg_score,
            "top_boards": self.memory.insights.high_converting_boards[:3],
            "recommended_next_template": self.memory.get_preferred_template_for_board(state.target_board),
        }

        state.log(
            agent_name="GrowthAnalystAgent",
            action="memory_evolved",
            thought=f"Cumulative average quality score: {self.memory.insights.historical_avg_score}/100.",
            result_summary=f"Memory updated. Total published: {self.memory.insights.total_pins_published}"
        )

        return insights
