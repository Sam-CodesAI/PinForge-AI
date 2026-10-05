"""PinForge AI — Pydantic Data Models.

Strict validation for products, graphic configs, and SEO requests.
"""

from __future__ import annotations

from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field


class ProductData(BaseModel):
    asin: str = Field(..., description="Amazon 10-character ASIN")
    title: str = Field(..., description="Cleaned product title")
    brand: Optional[str] = Field(None, description="Product brand name")
    category: str = Field(default="Lifestyle & Gadgets", description="Recommended category")
    price: str = Field(default="$29.99", description="Formatted current price")
    original_price: Optional[str] = Field(None, description="List/strike-through price")
    discount_percent: Optional[int] = Field(None, description="Discount percentage if on sale")
    rating: float = Field(default=4.7, ge=1.0, le=5.0, description="Star rating")
    review_count: str = Field(default="1,200+", description="Formatted review count")
    image_url: str = Field(..., description="High-resolution primary product image URL")
    additional_images: List[str] = Field(default_factory=list, description="Additional image URLs")
    features: List[str] = Field(default_factory=list, description="Top key feature bullets")
    friction_highlights: List[str] = Field(default_factory=list, description="Mined buyer friction highlights (renter friendly, dimensions, tool-free)")
    friction_badge: Optional[str] = Field(None, description="High-converting prominent badge for pin graphics")
    mounting_type: Optional[str] = Field(default=None, description="Mounting type classification")
    is_renter_safe: bool = Field(default=True, description="True if no drilling or permanent damage required")
    deal_badge: Optional[str] = Field(default=None, description="Amazon deal badge e.g. Limited time deal")
    coupon_text: Optional[str] = Field(default=None, description="Digital coupon text e.g. Save $5 with coupon")
    bought_past_month: Optional[str] = Field(default=None, description="Monthly sales social proof e.g. 50K+ bought in past month")
    affiliate_url: str = Field(..., description="Destination affiliate link with tag")
    bridge_slug: str = Field(..., description="Unique slug for the Next.js bridge page")
    raw_source: str = Field(default="stealth_scraper", description="Source of extraction")


class ExtractRequest(BaseModel):
    url_or_asin: str = Field(..., description="Amazon product URL, shortlink (amzn.to), or 10-char ASIN")
    affiliate_tag: Optional[str] = Field(None, description="Optional override for Amazon Associate tag")


class BridgeReview(BaseModel):
    verdict: str
    pros: List[str]
    cons: List[str]
    who_is_it_for: str


class CopyGenerationRequest(BaseModel):
    product_title: str
    brand: Optional[str] = None
    category: str = "Lifestyle & Tech"
    price: str = "$49.99"
    features: List[str] = Field(default_factory=list)
    rating: float = 4.7
    affiliate_tag: Optional[str] = None


class PinCopyResponse(BaseModel):
    pin_title: str = Field(..., max_length=100, description="Pinterest title <= 100 chars")
    pin_description: str = Field(..., max_length=500, description="Pinterest description <= 500 chars with FTC disclosure")
    hashtags: List[str] = Field(default_factory=list)
    board_recommendation: str = Field(...)
    call_to_action: str = Field(...)
    hook: str = Field(...)
    bridge_review: BridgeReview


class PinGenerateRequest(BaseModel):
    title: str = Field(..., description="Title to render on the graphic")
    image_url: str = Field(..., description="High-res product image URL")
    price: str = Field(default="$49.99")
    original_price: Optional[str] = None
    rating: float = Field(default=4.8)
    review_count: str = Field(default="4,500+")
    badge_text: str = Field(default="TOP RATED 2026")
    friction_badge: Optional[str] = Field(default="100% RENTER FRIENDLY • NO DRILL", description="Prominent friction badge stamped on graphic")
    friction_highlights: List[str] = Field(default_factory=list, description="Buyer friction highlights")
    template: Literal[
        "bento_dark",
        "warm_editorial",
        "problem_solver",
        "pollinations_lifestyle",
        "aspirational_lifestyle",
        "track_a_lifestyle",
    ] = Field(default="bento_dark", description="Visual graphic layout")
    brand: Optional[str] = None
    category: Optional[str] = Field(default="Smart Home & Space Saving")
    board_name: Optional[str] = Field(default="Smart Spaces")
    features: List[str] = Field(default_factory=list)
    cta_text: str = Field(default="TAP TO VIEW ON AMAZON ->")


class PinGenerateResponse(BaseModel):
    image_path: str = Field(..., description="Local path to rendered image")
    image_url: str = Field(..., description="Public HTTP URL of rendered image")
    base64_image: str = Field(..., description="Base64 encoded image string for instant preview")
    width: int = 1000
    height: int = 1500
    render_time_ms: float
    template: Optional[str] = None


class ScheduleItem(BaseModel):
    board_name: str
    title: str
    description: str
    link: str
    image_url: str
    published_at: str


class CsvExportRequest(BaseModel):
    items: List[ScheduleItem]
    interval_hours: int = 4
    start_date: Optional[str] = None


class PinterestPublishRequest(BaseModel):
    board_name_or_id: str = Field(..., description="Target Pinterest Board Name or Board ID")
    title: str = Field(..., description="Pin title")
    description: str = Field(..., description="Pin description")
    link: Optional[str] = Field(default="", description="Affiliate or bridge link")
    image_url: Optional[str] = Field(default=None, description="Direct image URL or public URL")
    slides: Optional[List[Dict[str, Any]]] = Field(default=None, description="Optional carousel slide items for multiple_image_base64")


class AutonomousCycleRequest(BaseModel):
    url_or_asin: str = Field(..., description="Amazon product URL or ASIN")
    template_style: Literal[
        "bento_dark",
        "warm_editorial",
        "problem_solver",
        "pollinations_lifestyle",
        "aspirational_lifestyle",
        "track_a_lifestyle",
        "anime",
        "story",
        "luxury_editorial",
        "cyber_bento",
    ] = Field(default="bento_dark", description="Visual graphic layout style")
    publish_live: bool = Field(default=False, description="Whether to publish live to Pinterest immediately")
    publish_as_carousel: bool = Field(default=False, description="Whether to publish as a 4-slide carousel pin")
    track_a: bool = Field(default=False, description="Generate Track A Aspirational Lifestyle Pin (zero promo boxes, zero buttons, zero prices)")


class VisualGenerateRequest(BaseModel):
    product_title: str = Field(default="Modern Space Saving Organizer", description="Subject for visual generation")
    board_name: Optional[str] = Field(default="Small Apartment Hacks", description="Target Pinterest board for aesthetic tuning")
    category: Optional[str] = Field(default="Home Organization", description="Category context")
    style: Optional[str] = Field(default="aspirational_lifestyle", description="Aesthetic style preset")
    preferred_tier: Optional[int] = Field(default=None, ge=1, le=4, description="Target waterfall tier (1: Ideogram, 2: Fal, 3: Pollinations, 4: Local)")
    track_a: bool = Field(default=False, description="Whether to render as Track A Aspirational Lifestyle Pin")


class VisualGenerateResponse(BaseModel):
    provider: str
    tier: int
    prompt_used: str
    image_url: str
    base64_image: str
    render_time_ms: float
    is_ai_generated: bool
    error_trail: List[str] = Field(default_factory=list)
