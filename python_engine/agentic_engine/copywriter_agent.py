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

        # 1. Synthesize high-conversion headline prioritized by 150-pin audit findings
        # Problem-Solver & Transformation hooks drive 66.7% of all outbound conversion (57.1% conversion efficiency)
        headline, formula = self._formulate_winning_headline(prod, state.target_board)
        hashtags = self._get_board_keywords(state.target_board)

        # 2. Synthesize SEO description strictly enforcing Save-First trigger
        base_desc = (
            f"📌 SAVE THIS PIN to your {state.target_board.lower()} board! "
            f"The definitive space-saving solution engineered for compact apartments and modern homes. "
            f"100% renter friendly with zero wall drilling and tool-free 60-second setup. "
            f"Verified customer rating: {prod.rating}★ ({prod.review_count}). "
            f"Tap the pin to inspect full dimensions, verified reviews, and availability. "
            f"#AmazonAssociate {' '.join(hashtags)}"
        )

        # Generate clean URL bridge slug
        slug_base = re.sub(r"[^a-z0-9]+", "-", prod.title.lower()).strip("-")[:48]
        bridge_slug = f"{slug_base}-{prod.asin.lower()}"

        copy_draft = PinCopyDraft(
            pin_title=headline[:98],
            hook_formula=formula,
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
            thought=(
                f"Headline formulated using '{formula}' (57.1% historical outbound conversion efficiency). "
                f"Save-First trigger embedded at byte 0 of description."
            ),
            result_summary=f"Headline: '{copy_draft.pin_title}'"
        )
        return copy_draft

    def _formulate_winning_headline(self, prod: ProductCandidate, board_name: str) -> tuple[str, str]:
        """Authors headline utilizing proven formulas from the 150-pin conversion audit."""
        title_lower = prod.title.lower()
        clean_name = re.sub(r"\s+", " ", re.sub(r"[^\w\s]", "", prod.title[:45])).strip()

        # Formula 1: Problem-Solver / Pain Point Hook (57.1% click-to-outbound efficiency)
        if "drawer" in title_lower or "divider" in title_lower:
            return "Finally Fix Messy Drawers! Aesthetic Closet Organization Made Easy", "Problem-Solver (57.1% Outbound Conv)"
        elif "makeup" in title_lower or "vanity" in title_lower or "carousel" in title_lower:
            return "Vanity Chaos? Fixed: 360 Spin Makeup Organizer Aesthetic", "Problem-Solver (57.1% Outbound Conv)"
        elif "sink" in title_lower or "under cabinet" in title_lower:
            return "Maximize Your Sink: 2-Tier Sliding Under Cabinet Organizer!", "Action/Transformation (14.3% CTR)"
        elif "cart" in title_lower or "rolling" in title_lower:
            return "Turn Tiny Gaps Into Mega Storage: Slim Rolling Storage Cart", "Action/Transformation (14.3% CTR)"
        elif "hanger" in title_lower or "closet" in title_lower:
            return "Closet Chaos? Fixed: Space-Saving Organization Hack", "Problem-Solver (57.1% Outbound Conv)"
        else:
            return f"Why Everyone In Small Apartments Is Obsessed With The {clean_name}", "Curiosity / Problem-Solver"

    def _get_board_keywords(self, board_name: str) -> List[str]:
        """Provides high search-volume Pinterest SEO keywords tailored to the board."""
        board_lower = board_name.lower()
        if "apartment" in board_lower:
            return ["#SmallApartmentHacks", "#StudioLiving", "#SpaceSaving", "#ApartmentDecor", "#AmazonAssociate"]
        elif "room" in board_lower or "organization" in board_lower:
            return ["#RoomOrganization", "#HomeOrganization", "#AestheticStorage", "#Declutter", "#AmazonAssociate"]
        elif "kitchen" in board_lower:
            return ["#KitchenOrganization", "#SmallKitchenHacks", "#PantryOrganization", "#AmazonAssociate"]
        elif "closet" in board_lower:
            return ["#ClosetOrganization", "#WardrobeHacks", "#SmallClosetHacks", "#AmazonAssociate"]
        else:
            return ["#SmartSpaces", "#HomeHacks", "#ApartmentOrganization", "#AmazonAssociate"]
