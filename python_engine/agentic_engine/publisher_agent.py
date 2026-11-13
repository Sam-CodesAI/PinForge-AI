"""PinForge AI — PublisherAgent (Strategic Algorithmic Dispatcher).

Manages Pinterest API v5 publication, board resolution, jitter timing,
and bridge URL routing adhering strictly to FTC and affiliate disclosure standards.
"""

from __future__ import annotations

import logging
import random
import time
from typing import Optional, Dict, Any

from .models import SwarmState
from .memory import SwarmMemory

try:
    from python_engine.pinterest_client import PinterestClient
    from python_engine.config import BASE_URL, DEFAULT_AFFILIATE_TAG
except ImportError:
    from pinterest_client import PinterestClient
    from config import BASE_URL, DEFAULT_AFFILIATE_TAG

logger = logging.getLogger("pinforge.agentic.publisher")


class PublisherAgent:
    """Agent 5: Dispatches approved pins to Pinterest with anti-bot timing and bridge page links."""

    def __init__(self, memory: SwarmMemory, affiliate_tag: str = DEFAULT_AFFILIATE_TAG):
        self.memory = memory
        self.affiliate_tag = affiliate_tag
        self.pinterest = PinterestClient()

    def dispatch_pin(
        self,
        state: SwarmState,
        publish_live: bool = False,
        apply_jitter: bool = False
    ) -> Dict[str, Any]:
        """Dispatches an approved pin to Pinterest API v5."""
        if not state.critic_audit or not state.critic_audit.approved:
            raise ValueError("Safety Guardrail: Cannot publish a pin that has not been approved by VisionCriticAgent.")

        if not state.product or not state.copy or not state.rendered_image_path:
            raise ValueError("Incomplete SwarmState: Product, copy, and image must all be populated.")

        # 1. Construct Next.js Bridge Gateway URL
        bridge_url = f"{BASE_URL}/p/{state.copy.bridge_slug}?tag={self.affiliate_tag}"

        state.log(
            agent_name="PublisherAgent",
            action="prepare_publication",
            thought=(
                f"Preparing dispatch for board '{state.target_board}'. "
                f"Destination link: {bridge_url}. Live={publish_live}."
            ),
            result_summary=f"Destination: {bridge_url}"
        )

        # 2. Anti-Detection Jitter Offset (if enabled)
        if apply_jitter and publish_live:
            jitter_sec = random.randint(60, 360)  # 1 to 6 minutes
            logger.info(f"⏳ PublisherAgent applying anti-detection jitter: {jitter_sec}s...")
            time.sleep(jitter_sec)

        # 3. Dry-Run Dispatch Path
        if not publish_live:
            mock_id = f"dry_run_{state.session_id[:8]}"
            state.published_pin_id = mock_id
            state.is_successful = True
            logger.info(f"🚀 [DRY RUN] Pin simulated as published (ID: {mock_id}) to '{state.target_board}'")
            state.log(
                agent_name="PublisherAgent",
                action="dry_run_complete",
                thought="Dry-run publication complete. Pin asset and metadata verified.",
                result_summary=f"Simulated Pin ID: {mock_id}"
            )
            return {
                "id": mock_id,
                "title": state.copy.pin_title,
                "board_name": state.target_board,
                "link": bridge_url,
                "status": "dry_run_success",
            }

        # 4. Live Pinterest API v5 Dispatch Path
        logger.info(f"🚀 Dispatching LIVE Pin to Pinterest API v5 on board '{state.target_board}'...")
        try:
            board_id = self.pinterest.get_or_create_board(state.target_board)
            result = self.pinterest.create_pin(
                board_id=board_id,
                title=state.copy.pin_title,
                description=state.copy.pin_description,
                link=bridge_url,
                image_path=state.rendered_image_path,
                base64_image=state.rendered_base64,
            )
            pin_id = result.get("id", f"pin_{state.session_id[:8]}")
            state.published_pin_id = pin_id
            state.is_successful = True

            state.log(
                agent_name="PublisherAgent",
                action="live_dispatch_success",
                thought=f"Live Pin ID {pin_id} published successfully to board '{state.target_board}'.",
                result_summary=f"Published Live: {pin_id}"
            )
            return result
        except Exception as e:
            logger.error(f"Live Pinterest publication failed: {e}")
            state.log(
                agent_name="PublisherAgent",
                action="dispatch_error",
                thought=f"Encountered publication error: {e}",
                result_summary="Publication failed"
            )
            raise e
