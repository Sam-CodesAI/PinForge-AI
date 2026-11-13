"""PinForge AI — Agentic Swarm Data Models.

Defines strongly-typed Pydantic schemas for multi-agent communication,
shared blackboard state, visual critique audits, and persistent swarm memory.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class ProductCandidate(BaseModel):
    """Product selected by the ScoutAgent for current publishing window."""
    asin: str = Field(..., description="Amazon 10-char ASIN")
    title: str = Field(..., description="Cleaned product title")
    brand: str = Field(default="Smart Spaces Selection")
    category: str = Field(default="Room Organization")
    board_name: str = Field(default="Room Organization")
    price: str = Field(default="$24.99")
    original_price: Optional[str] = None
    rating: float = Field(default=4.7, ge=1.0, le=5.0)
    review_count: str = Field(default="5,000+ ratings")
    image_url: str = Field(..., description="Primary product image URL")
    additional_images: List[str] = Field(default_factory=list)
    features: List[str] = Field(default_factory=list)
    strategic_rationale: str = Field(
        default="",
        description="Reasoning provided by ScoutAgent for selecting this product"
    )
    viral_score: float = Field(default=95.0, ge=0.0, le=100.0)


class CreativeStrategy(BaseModel):
    """Art direction and layout strategy authored by CreativeDirectorAgent."""
    template_variant: str = Field(
        default="warm_editorial",
        description="One of: track_a_lifestyle, warm_editorial, problem_solver, carousel_suite"
    )
    lighting_prompt: str = Field(
        default="2700K warm ambient sunlight, soft Japandi shadows, natural limestone and bleached oak textures"
    )
    visual_focal_point: str = Field(
        default="Center-aligned product on honed travertine slab with minimal linen backdrop"
    )
    accent_hex: str = Field(default="#D97706", description="2700K warm amber accent")
    primary_hex: str = Field(default="#F9F6F0", description="Alabaster linen primary")
    friction_badge: str = Field(default="100% RENTER FRIENDLY • NO DRILL")
    applied_corrections: List[str] = Field(
        default_factory=list,
        description="Corrections applied in response to VisionCriticAgent feedback"
    )


class PinCopyDraft(BaseModel):
    """Conversion copy authored by CopywriterAgent."""
    pin_title: str = Field(..., description="Curiosity or problem-solver hook title")
    hook_formula: str = Field(
        default="Curiosity Gap",
        description="Conversion formula used: Curiosity Gap, Pain-Agitate-Solve, Before-After"
    )
    pin_description: str = Field(..., description="SEO-optimized description with Save CTA")
    cta_text: str = Field(default="📌 SAVE THIS PIN • TAP FOR FULL GUIDE ->")
    hashtags: List[str] = Field(default_factory=list)
    board_recommendation: str = Field(default="Room Organization")
    bridge_slug: str = Field(..., description="URL slug for the Next.js bridge page")


class VisionCriticEvaluation(BaseModel):
    """Multi-modal visual audit produced by VisionCriticAgent."""
    score: float = Field(..., ge=0.0, le=100.0, description="Overall aesthetic & conversion score")
    approved: bool = Field(..., description="True if score >= 85 and zero critical defects")
    text_legibility_score: float = Field(default=90.0, ge=0.0, le=100.0)
    brand_compliance_score: float = Field(default=90.0, ge=0.0, le=100.0)
    mobile_readability_score: float = Field(default=90.0, ge=0.0, le=100.0)
    contrast_score: float = Field(default=90.0, ge=0.0, le=100.0)
    critique_notes: List[str] = Field(default_factory=list)
    corrective_instructions: List[str] = Field(
        default_factory=list,
        description="Actionable directives for CreativeDirectorAgent if rejected"
    )
    auditor_model: str = Field(default="gemini-2.5-flash / heuristic-vision")

    @property
    def rubric_score(self) -> float:
        return self.score


class AgentLogEntry(BaseModel):
    """Individual entry in the swarm's transparent thought & action log."""
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    agent_name: str
    action: str
    thought: str
    result_summary: str


class MemoryInsights(BaseModel):
    """Persistent insights accumulated across publishing cycles and 150-pin audit."""
    top_performing_templates: List[str] = Field(
        default_factory=lambda: ["carousel_suite", "warm_editorial", "track_a_lifestyle"]
    )
    winning_hook_prefixes: List[str] = Field(
        default_factory=lambda: [
            "Finally Fix Messy Drawers! Aesthetic Closet Organization Made Easy",
            "Vanity Chaos? Fixed:",
            "Maximize Your Sink:",
            "Turn Tiny Gaps Into Mega Storage:",
            "Why Everyone In Small Apartments Is Obsessed With",
        ]
    )
    optimal_price_floor: float = 18.00
    optimal_price_ceiling: float = 35.00
    high_converting_boards: List[str] = Field(
        default_factory=lambda: [
            "Room Organization",
            "Small Apartment Hacks",
            "Studio Living Ideas",
            "Space Saving Kitchens",
            "Closet & Wardrobe Organization",
        ]
    )
    approved_friction_badges: List[str] = Field(
        default_factory=lambda: [
            "100% RENTER FRIENDLY • NO DRILL",
            "ZERO WALL HOLES",
            "TOOL-FREE POP-UP READY",
            "FITS ANY CABINET • NO TOOLS NEEDED",
            "EXPANDABLE & DAMAGE FREE",
        ]
    )
    total_pins_published: int = 150
    historical_avg_score: float = 93.4
    template_benchmarks: Dict[str, Any] = Field(default_factory=dict)
    winning_asins: List[Dict[str, Any]] = Field(default_factory=list)
    hook_architecture_metrics: Dict[str, Any] = Field(default_factory=dict)
    peak_schedule_matrix: Dict[str, Any] = Field(default_factory=dict)

    def get_top_asin_for_board(self, board_name: str) -> Optional[str]:
        """Returns the proven highest-converting ASIN for a given board if present."""
        for item in self.winning_asins:
            if item.get("board", "").lower() == board_name.lower():
                return item.get("asin")
        return None


class SwarmState(BaseModel):
    """Central blackboard state holding the complete lifecycle of an autonomous pin."""
    session_id: str
    target_slot: int = 1
    target_board: str = "Room Organization"
    product: Optional[ProductCandidate] = None
    creative_direction: Optional[CreativeStrategy] = None
    pin_copy: Optional[PinCopyDraft] = Field(default=None, description="SEO and conversion copy draft")
    rendered_image_path: Optional[str] = None
    rendered_base64: Optional[str] = None
    critic_audit: Optional[VisionCriticEvaluation] = None
    revision_count: int = 0
    published_pin_id: Optional[str] = None
    is_successful: bool = False
    execution_log: List[AgentLogEntry] = Field(default_factory=list)

    def log(self, agent_name: str, action: str, thought: str, result_summary: str) -> None:
        """Appends an execution step to the transparent swarm log."""
        self.execution_log.append(
            AgentLogEntry(
                agent_name=agent_name,
                action=action,
                thought=thought,
                result_summary=result_summary,
            )
        )

    @property
    def copy(self) -> Optional[PinCopyDraft]:
        return self.pin_copy

    @copy.setter
    def copy(self, val: Optional[PinCopyDraft]) -> None:
        self.pin_copy = val

    @property
    def creative_strategy(self) -> Optional[CreativeStrategy]:
        return self.creative_direction

    @creative_strategy.setter
    def creative_strategy(self, val: Optional[CreativeStrategy]) -> None:
        self.creative_direction = val

    @property
    def critic_evaluation(self) -> Optional[VisionCriticEvaluation]:
        return self.critic_audit

    @critic_evaluation.setter
    def critic_evaluation(self, val: Optional[VisionCriticEvaluation]) -> None:
        self.critic_audit = val
