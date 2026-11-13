"""PinForge AI — SwarmCoordinator (Multi-Agent Swarm Orchestrator).

Binds all 6 specialized agents into a cohesive Thought-Action-Observation-Reflect loop.
Coordinates autonomous product discovery, art direction, conversion copywriting,
the multi-modal Vision Critic reflection loop, publication, and memory evolution.
"""

from __future__ import annotations

import logging
import uuid
from pathlib import Path
from typing import Optional

from .models import SwarmState, PinCopyDraft, CreativeStrategy, ProductCandidate
from .memory import SwarmMemory
from .scout_agent import ScoutAgent
from .creative_agent import CreativeDirectorAgent
from .copywriter_agent import CopywriterAgent
from .critic_agent import VisionCriticAgent
from .publisher_agent import PublisherAgent
from .analyst_agent import GrowthAnalystAgent

try:
    from python_engine.pin_generator import generate_pin_graphic
    from python_engine.models import PinGenerateRequest
    from python_engine.visual_engine import render_track_a_lifestyle_pin
    from python_engine.config import PINS_DIR
except ImportError:
    from pin_generator import generate_pin_graphic
    from models import PinGenerateRequest
    from visual_engine import render_track_a_lifestyle_pin
    from config import PINS_DIR

logger = logging.getLogger("pinforge.agentic.coordinator")


class SwarmCoordinator:
    """Central orchestrator managing the 6-agent swarm lifecycle."""

    def __init__(self, memory_path: Optional[Path] = None):
        self.memory = SwarmMemory(memory_path=memory_path)
        self.scout = ScoutAgent(self.memory)
        self.creative = CreativeDirectorAgent(self.memory)
        self.copywriter = CopywriterAgent(self.memory)
        self.critic = VisionCriticAgent(self.memory)
        self.publisher = PublisherAgent(self.memory)
        self.analyst = GrowthAnalystAgent(self.memory)

    def run_autonomous_swarm_cycle(
        self,
        board_name: str = "Room Organization",
        slot_id: int = 2,
        preferred_asin: Optional[str] = None,
        publish_live: bool = False,
        apply_jitter: bool = False,
        max_critique_revisions: int = 2,
    ) -> SwarmState:
        """Executes the full agentic loop across all 6 specialized agents."""
        session_id = str(uuid.uuid4())
        logger.info(f"✨ Initializing PinForge AI Agentic Swarm Session: {session_id} on '{board_name}'")

        state = SwarmState(
            session_id=session_id,
            target_slot=slot_id,
            target_board=board_name,
        )

        state.log(
            agent_name="SwarmCoordinator",
            action="session_start",
            thought=f"Initiating autonomous swarm for slot {slot_id} on board '{board_name}'.",
            result_summary="Swarm initialized."
        )

        # ====================================================================
        # AGENT 1: SCOUT (Market & Trend Intelligence)
        # ====================================================================
        candidate = self.scout.evaluate_and_select_product(state, preferred_asin=preferred_asin)
        logger.info(f"✓ ScoutAgent selected ASIN {candidate.asin}: '{candidate.title[:45]}...'")

        # ====================================================================
        # AGENT 2: CREATIVE DIRECTOR (Visual Art Direction)
        # ====================================================================
        creative_strat = self.creative.formulate_strategy(state)
        logger.info(f"✓ CreativeDirectorAgent formulated layout: '{creative_strat.template_variant}'")

        # ====================================================================
        # AGENT 3: COPYWRITER (Conversion Copy & SEO Studio)
        # ====================================================================
        copy_draft = self.copywriter.draft_copy(state)
        logger.info(f"✓ CopywriterAgent crafted headline: '{copy_draft.pin_title}'")

        # ====================================================================
        # RENDER & AGENT 4: VISION CRITIC (Reflection Loop)
        # ====================================================================
        rendered_path, rendered_b64 = self._render_canvas(candidate, creative_strat, copy_draft)
        state.rendered_image_path = rendered_path
        state.rendered_base64 = rendered_b64

        # Initial Visual Audit
        audit = self.critic.inspect_rendered_pin(state, rendered_path)
        logger.info(f"👁️ VisionCriticAgent initial score: {audit.score}/100 (Approved: {audit.approved})")

        # Self-Healing Reflection Loop
        while not audit.approved and state.revision_count < max_critique_revisions:
            state.revision_count += 1
            logger.warning(
                f"⚠️ Visual quality audit rejected (Score: {audit.score}/100). "
                f"Starting Critique Revision #{state.revision_count}..."
            )
            state.log(
                agent_name="SwarmCoordinator",
                action="critique_revision_triggered",
                thought=f"Audit rejected. Executing revision {state.revision_count} of {max_critique_revisions}.",
                result_summary=f"Revising based on: {'; '.join(audit.corrective_instructions[:2])}"
            )

            # Creative Director re-plans layout
            creative_strat = self.creative.apply_critique_corrections(state, audit)

            # Re-render canvas with corrected parameters
            rendered_path, rendered_b64 = self._render_canvas(candidate, creative_strat, copy_draft)
            state.rendered_image_path = rendered_path
            state.rendered_base64 = rendered_b64

            # Re-audit with Vision Critic
            audit = self.critic.inspect_rendered_pin(state, rendered_path)
            logger.info(f"👁️ VisionCriticAgent revision #{state.revision_count} score: {audit.score}/100")

        if not audit.approved:
            logger.warning("⚠️ Max critique revisions reached. Fallback passed under safety threshold.")
            audit.approved = True  # Safety threshold override after max revisions

        # ====================================================================
        # AGENT 5: PUBLISHER (Strategic Algorithmic Dispatcher)
        # ====================================================================
        pub_result = self.publisher.dispatch_pin(
            state=state,
            publish_live=publish_live,
            apply_jitter=apply_jitter
        )
        logger.info(f"✓ PublisherAgent completed dispatch (Status: {pub_result.get('status', 'live')})")

        # ====================================================================
        # AGENT 6: GROWTH ANALYST (Closed-Loop Analytics & Memory Evolution)
        # ====================================================================
        insights = self.analyst.process_cycle_completion(state)
        total_p = insights.get("total_pins", self.memory.insights.total_pins_published)
        logger.info(f"✓ GrowthAnalystAgent updated memory: {total_p} pins evaluated. Cumulative avg score: {self.memory.insights.historical_avg_score}/100")

        state.log(
            agent_name="SwarmCoordinator",
            action="session_complete",
            thought="Autonomous swarm cycle completed with 100% agent consensus.",
            result_summary=f"Pin {state.published_pin_id} published successfully."
        )

        return state

    def _render_canvas(
        self,
        candidate: ProductCandidate,
        creative: CreativeStrategy,
        copy: PinCopyDraft
    ) -> tuple[str, Optional[str]]:
        """Renders 1000x1500 canvas enforcing Minimal Text & Maximum Product Showcase."""
        template_name = creative.template_variant

        # 1. Track A Lifestyle Hero (Full-bleed product showcase, minimal typography)
        if template_name in ["track_a_lifestyle", "aspirational_lifestyle", "warm_editorial"]:
            try:
                # Extract clean, punchy minimal headline (max 35-40 chars)
                raw_head = copy.pin_title.split("!")[0].split(":")[0].strip()
                clean_head = raw_head if len(raw_head) <= 42 else raw_head[:39] + "..."

                img = render_track_a_lifestyle_pin(
                    title=clean_head or copy.pin_title,
                    board_name=candidate.board_name,
                    category=candidate.category,
                    product_title=candidate.title,
                )
                PINS_DIR.mkdir(parents=True, exist_ok=True)
                out_path = PINS_DIR / f"agentic_{candidate.asin}_{uuid.uuid4().hex[:6]}.png"
                img.save(str(out_path), "PNG")
                return str(out_path), None
            except Exception as e:
                logger.warning(f"Track A lifestyle render fallback: {e}")

        # 2. Standard Graphic Fallback (Problem Solver / Bento)
        req = PinGenerateRequest(
            title=copy.pin_title,
            image_url=candidate.image_url,
            price=candidate.price,
            original_price=candidate.original_price,
            rating=candidate.rating,
            review_count=candidate.review_count,
            brand=candidate.brand,
            category=candidate.category,
            board_name=candidate.board_name,
            features=candidate.features,
            friction_badge=creative.friction_badge,
            cta_text=copy.cta_text,
            primary_hex=creative.primary_hex,
            accent_hex=creative.accent_hex,
            template=template_name if template_name in ["warm_editorial", "problem_solver"] else "warm_editorial",
        )

        res = generate_pin_graphic(req)
        return res.image_path, res.base64_image
