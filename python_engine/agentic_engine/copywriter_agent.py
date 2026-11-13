"""PinForge AI — CopywriterAgent (Conversion Copy & Pinterest SEO Studio).

Generates curiosity-gap headlines, friction-reducing badges, and search-optimized
descriptions strictly enforcing the 'Save-First' algorithmic trigger.
"""

from __future__ import annotations

import logging
import re
from typing import List

from .models import PinCopyDraft, SwarmState
from .memory import SwarmMemory

try:
    from python_engine.seo_engine import generate_pin_copy
    from python_engine.models import CopyGenerationRequest
except ImportError:
    from seo_engine import generate_pin_copy
    from models import CopyGenerationRequest

logger = logging.getLogger("pinforge.agentic.copywriter")


class CopywriterAgent:
    """Agent 3: Synthesizes high-converting hooks, SEO descriptions, and Save-First callouts."""

    def __init__(self, memory: SwarmMemory):
        self.memory = memory

    def draft_copy(self, state: SwarmState) -> PinCopyDraft:
        """Authors search-ranked Pinterest copy enforcing the Save-First contract."""
        prod = state.product
        if not prod:
            raise ValueError("Cannot author copy without an active ProductCandidate in SwarmState.")

        state.log(
            agent_name="CopywriterAgent",
            action="draft_conversion_copy",
            thought=(
                f"Generating curiosity hook and SEO description for ASIN {prod.asin}. "
                f"Enforcing Save-First algorithmic contract and #AmazonAssociate disclosure."
            ),
            result_summary="Formulating high-AES headline and description."
        )

        # 1. Synthesize baseline copy using SEO engine
        try:
            req = CopyGenerationRequest(
                product_title=prod.title,
                brand=prod.brand,
                category=state.target_board,
                price=prod.price,
                features=prod.features,
                rating=prod.rating,
            )
            raw_res = generate_pin_copy(req)
            base_title = raw_res.pin_title
            base_desc = raw_res.pin_description
            hashtags = raw_res.hashtags
        except Exception as e:
            logger.warning(f"SEO engine fallback invoked for {prod.asin}: {e}")
            clean_name = re.sub(r"\s+", " ", re.sub(r"[^\w\s]", "", prod.title[:45])).strip()
            base_title = f"Why Everyone Is Obsessed With The {clean_name}"
            base_desc = (
                f"The ultimate space-saving solution for small apartments and modern homes. "
                f"Durable, tool-free setup with zero wall damage. Verified customer rating: {prod.rating}★. "
                f"📌 SAVE THIS PIN to your home board! Tap for full dimensions & reviews. "
                f"#AmazonAssociate #SmartSpaces #SmallApartmentHacks #HomeOrganization"
            )
            hashtags = ["#SmallApartmentHacks", "#HomeOrganization", "#SmartSpaces", "#AmazonAssociate"]

        # 2. Strict Save-First Copy Contract Enforcement
        save_trigger = "📌 SAVE THIS PIN"
        if save_trigger not in base_desc.upper():
            base_desc = f"{save_trigger} to your board! {base_desc}"

        # Ensure #AmazonAssociate disclosure is always present
        if "#AMAZONASSOCIATE" not in base_desc.upper():
            base_desc = f"{base_desc} #AmazonAssociate"

        # Generate clean URL bridge slug
        slug_base = re.sub(r"[^a-z0-9]+", "-", prod.title.lower()).strip("-")[:48]
        bridge_slug = f"{slug_base}-{prod.asin.lower()}"

        copy_draft = PinCopyDraft(
            pin_title=base_title[:98],
            hook_formula="Curiosity Gap / Problem Solver",
            pin_description=base_desc[:495],
            cta_text="📌 SAVE THIS PIN • TAP FOR FULL GUIDE ->",
            hashtags=hashtags[:6],
            board_recommendation=state.target_board,
            bridge_slug=bridge_slug,
        )

        state.copy = copy_draft
        state.log(
            agent_name="CopywriterAgent",
            action="copy_finalized",
            thought=f"Headline: '{copy_draft.pin_title}'. Save CTA verified in description.",
            result_summary=f"Copy drafted for slug: /p/{bridge_slug}"
        )
        return copy_draft
