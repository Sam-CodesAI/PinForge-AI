"""PinForge AI — Pydantic Data Models.

Strict validation for products, graphic configs, and SEO requests.
"""

from typing import List, Optional, Literal
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
    template: Literal["bento_dark", "warm_editorial", "problem_solver"] = Field(
        default="bento_dark", description="Visual graphic layout"
    )
    brand: Optional[str] = None
    features: List[str] = Field(default_factory=list)
    cta_text: str = Field(default="TAP TO VIEW ON AMAZON ➔")


class PinGenerateResponse(BaseModel):
    image_path: str = Field(..., description="Local path to rendered image")
    image_url: str = Field(..., description="Public HTTP URL of rendered image")
    base64_image: str = Field(..., description="Base64 encoded image string for instant preview")
    width: int = 1000
    height: int = 1500
    render_time_ms: float


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
