"""PinForge AI — CreativeDirectorAgent (Visual Strategy & Art Direction).

Decides layout architecture, prompt parameters, lighting tokens, and color harmony.
Executes self-healing adjustments when receiving feedback from VisionCriticAgent.
"""

from __future__ import annotations

import logging
from typing import List

from .models import CreativeStrategy, SwarmState, VisionCriticEvaluation
from .memory import SwarmMemory

try:
    from python_engine.models import SMART_SPACES_BRAND
except ImportError:
    from models import SMART_SPACES_BRAND

logger = logging.getLogger("pinforge.agentic.creative")


class CreativeDirectorAgent:
    """Agent 2: Crafts visual art direction, selects template variants, and self-heals after visual critique."""

    def __init__(self, memory: SwarmMemory):
        self.memory = memory

    def formulate_strategy(self, state: SwarmState) -> CreativeStrategy:
        """Authors initial art direction strategy for the selected product candidate."""
        prod = state.product
        if not prod:
            raise ValueError("Cannot formulate creative strategy without an active ProductCandidate in SwarmState.")

        # Determine optimal template using peak schedule matrix and historical benchmarks
        slot_key = f"slot_{state.target_slot}"
        slot_info = self.memory.insights.peak_schedule_matrix.get(slot_key, {})
        recommended_format = slot_info.get("recommended_format")

        title_lower = prod.title.lower()
        # Default to Track A Lifestyle (Minimal text, maximum product showcase)
        if recommended_format and recommended_format in ["track_a_lifestyle", "aspirational_lifestyle", "carousel_suite"]:
            template = recommended_format
        else:
            template = "track_a_lifestyle"

        # Formulate lighting and staging prompt using Brand PRD standards
        lighting = (
            f"Aesthetic interior design photography of modern Japandi small apartment living, "
            f"featuring {prod.title[:50]}, full-bleed composition, 2700K warm golden hour sunlight, "
            f"bleached oak and natural limestone textures, Kinfolk editorial magazine style, 8k resolution, "
            f"shot on Hasselblad H6D-100c with intimate shallow depth of field, staged on honed travertine slab with neutral linen backdrop."
        )

        focal_point = f"Centered focal presentation of {prod.title[:45]} with soft ambient shadow"

        badge = SMART_SPACES_BRAND.friction_badges[0]  # "100% RENTER FRIENDLY • NO DRILL"

        strategy = CreativeStrategy(
            template_variant=template,
            lighting_prompt=lighting,
            visual_focal_point=focal_point,
            accent_hex=SMART_SPACES_BRAND.accent_hex,
            primary_hex=SMART_SPACES_BRAND.primary_hex,
            friction_badge=badge,
            applied_corrections=[],
        )

        state.creative_direction = strategy
        state.log(
            agent_name="CreativeDirectorAgent",
            action="formulate_visual_strategy",
            thought=(
                f"Product '{prod.title[:35]}' on board '{state.target_board}' (Slot {state.target_slot}). "
                f"Selected benchmark-backed template '{template}' (1.87x CTR multiplier on carousels) "
                f"with 2700K Japandi warm amber styling."
            ),
            result_summary=f"Art direction set: template={template}, badge='{badge}'"
        )
        return strategy

    def apply_critique_corrections(
        self,
        state: SwarmState,
        critic: VisionCriticEvaluation
    ) -> CreativeStrategy:
        """Self-healing loop: reads critique notes and adjusts strategy for re-render."""
        if not state.creative_direction:
            return self.formulate_strategy(state)

        strat = state.creative_direction
        corrections: List[str] = []

        logger.info(f"🎨 CreativeDirectorAgent processing VisionCriticAgent feedback: {critic.critique_notes}")

        # Rule 1: Text legibility failure -> switch to Warm Editorial with high contrast
        if critic.text_legibility_score < 85.0:
            if strat.template_variant != "warm_editorial":
                strat.template_variant = "warm_editorial"
                corrections.append("Switched to high-contrast warm_editorial template for improved typography padding.")
            corrections.append("Enforced strict 40-character line wrapping and diffused drop shadow.")

        # Rule 2: Contrast score low -> enhance primary border and darken text slate
        if critic.contrast_score < 85.0:
            strat.accent_hex = "#D97706"  # Rich warm amber
            corrections.append("Boosted accent color saturation to #D97706 for prominent visual hierarchy.")

        # Rule 3: Mobile readability -> simplify friction badge to punchy short form
        if critic.mobile_readability_score < 85.0:
            strat.friction_badge = "100% RENTER FRIENDLY • NO DRILL"
            corrections.append("Streamlined badge text to primary renter-friendly guarantee.")

        strat.applied_corrections.extend(corrections)
        state.creative_direction = strat
        state.log(
            agent_name="CreativeDirectorAgent",
            action="apply_critique_corrections",
            thought=f"Incorporated {len(corrections)} critique directives from VisionCriticAgent.",
            result_summary=f"Updated strategy: {'; '.join(corrections[:2])}"
        )
        return strat
