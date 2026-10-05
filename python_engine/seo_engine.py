"""PinForge AI — AI Copy & SEO Studio.

Generates high-CTR Pinterest titles (<100 chars), SEO descriptions (<500 chars),
FTC disclosures (#AmazonAssociate), board suggestions, and bridge landing page reviews.
Uses multi-LLM resiliency: Google Gemini -> Groq -> Deterministic Rules.
"""

import json
import logging
import re
from typing import Dict, List, Optional

from python_engine.config import GEMINI_API_KEY, GROQ_API_KEY
from python_engine.models import BridgeReview, CopyGenerationRequest, PinCopyResponse

logger = logging.getLogger("pinforge.seo")


OFFICIAL_BOARDS = [
    'Small Apartment Hacks',
    'Space Saving Kitchens',
    'Closet & Wardrobe Organization',
    'Studio Living Ideas',
    'Room Organization',
]

GENZ_COMMENT_HOOKS = [
    "Would you use this in your kitchen or bathroom? Drop your vote below! 👇",
    "Small space challenge: Could you fit everything in this setup? 🏠",
    "Be honest: is your space organized or chaotic right now? Tell me below! 😂👇",
    "Which room needs this most? Drop your vote below! ✨",
    "Renter friendly or permanent upgrade? What do you think? 👇",
    "Could this solve your storage clutter? Let us know below! 💬",
]


def select_official_board(category: str, title: str, candidate_board: Optional[str] = None) -> str:
    """Ensure board selection strictly routes into one of the 5 official Smart Spaces pillars."""
    if candidate_board:
        clean = candidate_board.strip()
        for b in OFFICIAL_BOARDS:
            if clean.lower() == b.lower() or clean.lower() == b.lower().rstrip("s"):
                return b

    # Map intelligently based on candidate_board, category, and title keywords
    combined = f"{candidate_board or ''} {category} {title}".lower()
    if any(k in combined for k in ["kitchen", "spice", "sink", "cooking", "fridge", "refrigerator", "pantry", "dish"]):
        return "Space Saving Kitchens"
    elif any(k in combined for k in ["closet", "wardrobe", "hanger", "clothes", "shoe", "drawer", "apparel"]):
        return "Closet & Wardrobe Organization"
    elif any(k in combined for k in ["studio", "desk", "floating", "ottoman", "multifunctional", "decor", "aesthetic", "lamp"]):
        return "Studio Living Ideas"
    elif any(k in combined for k in ["apartment", "under bed", "cart", "rolling", "foldable", "narrow", "gap", "small space"]):
        return "Small Apartment Hacks"
    else:
        return "Room Organization"


def format_pin_description_with_hook(raw_desc: str, title: str, category: str) -> str:
    """Injects Gen-Z conversational comment hooks and guarantees FTC compliance within 500 chars ending with #AmazonAssociate."""
    disclosure = "#AmazonAssociate"
    clean_desc = raw_desc.strip()

    # Strip any existing #AmazonAssociate (case-insensitive) to prevent duplication or placement in the middle
    clean_desc = re.sub(r"#AmazonAssociate\b", "", clean_desc, flags=re.IGNORECASE).strip()

    # Check if a conversational comment hook / CTA is already present
    has_hook = any(q in clean_desc.lower() for q in [
        "vote below", "drop a comment", "tell me below", "drop your vote",
        "tell us below", "comments below", "in the comments", "drop your thoughts", "👇", "💬"
    ])

    if not has_hook:
        c_low = f"{category} {title}".lower()
        if "kitchen" in c_low or "bathroom" in c_low:
            hook = "Would you use this in your kitchen or bathroom? Drop your vote below! 👇"
        elif "small" in c_low or "studio" in c_low or "apartment" in c_low:
            hook = "Small space challenge: Could you fit everything in this setup? 🏠"
        elif "closet" in c_low or "clothes" in c_low:
            hook = "Which room needs this most? Drop your vote below! ✨"
        else:
            hook = "Renter friendly or permanent upgrade? What do you think? 👇"
    else:
        hook = ""

    # Total max: 500 chars. Disclosure = 16 chars + 1 space = 17 chars.
    if hook:
        max_body = 483 - len(hook) - 1
        if len(clean_desc) > max_body:
            clean_desc = f"{clean_desc[:max_body - 3].rstrip()}..."
        final_desc = f"{clean_desc} {hook} {disclosure}".strip()
    else:
        if len(clean_desc) > 483:
            clean_desc = f"{clean_desc[:480].rstrip()}..."
        final_desc = f"{clean_desc} {disclosure}".strip()

    return final_desc[:500]


def generate_with_gemini(req: CopyGenerationRequest) -> Optional[PinCopyResponse]:
    """Generate Pinterest copy using Google Gemini."""
    if not GEMINI_API_KEY:
        return None

    try:
        from google import genai
        client = genai.Client(api_key=GEMINI_API_KEY)

        prompt = f"""You are an elite Pinterest affiliate marketing strategist and copywriter for the @Smart_Spaces brand.
Create an irresistible, high-converting Pinterest Pin campaign and FTC-compliant review for this Amazon product.

Product: {req.product_title}
Brand: {req.brand or 'Amazon Choice'}
Category: {req.category}
Price: {req.price}
Key Features: {', '.join(req.features[:3]) if req.features else 'Top rated, highly functional, premium build quality'}

REQUIREMENTS:
1. pin_title: MUST BE STRICTLY UNDER 100 CHARACTERS. Include high-intent search keywords and an emotional hook.
2. pin_description: MUST BE STRICTLY UNDER 500 CHARACTERS. Explain why this product is a space-saving essential, include keywords naturally, inject an engaging Gen-Z conversational comment hook to drive high viral algorithmic engagement (e.g., 'Would you use this in your kitchen or bathroom? Drop your vote below! 👇' or 'Small space challenge: Could you fit everything in this setup? 🏠'), and end with the mandatory FTC disclosure hashtag: #AmazonAssociate
3. hashtags: 5-7 popular Pinterest search tags (e.g. #SmallSpaceLiving, #OrganizationHacks, #AmazonFinds, #AmazonAssociate)
4. board_recommendation: MUST BE EXACTLY ONE OF THESE 5 OFFICIAL BOARDS:
   - 'Small Apartment Hacks'
   - 'Space Saving Kitchens'
   - 'Closet & Wardrobe Organization'
   - 'Studio Living Ideas'
   - 'Room Organization'
5. call_to_action: Short high-converting CTA (e.g. "Tap to check today's price & read full review")
6. hook: 4-7 word punchy visual hook
7. bridge_review: An objective, trustworthy review:
   - verdict: 1 punchy sentence summarizing why this product stands out
   - pros: exactly 3 specific bullet highlights
   - cons: 1 honest, minor consideration
   - who_is_it_for: 1 sentence targeting the exact persona

Return ONLY a valid JSON object matching this exact schema:
{{
  "pin_title": "string (<= 100 chars)",
  "pin_description": "string (<= 500 chars)",
  "hashtags": ["#tag1", "#tag2", ...],
  "board_recommendation": "string",
  "call_to_action": "string",
  "hook": "string",
  "bridge_review": {{
    "verdict": "string",
    "pros": ["pro 1", "pro 2", "pro 3"],
    "cons": ["con 1"],
    "who_is_it_for": "string"
  }}
}}"""

        import time
        import random

        models = ["gemini-3.8-flash", "gemini-3.5-flash-lite"]
        for model_name in models:
            for attempt in range(1, 4):
                try:
                    resp = client.models.generate_content(
                        model=model_name,
                        contents=prompt
                    )
                    text = resp.text.strip()
                    clean_json = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.MULTILINE).strip()
                    data = json.loads(clean_json)

                    # Ensure strict character boundaries and Gen-Z comment hook
                    pin_title = data.get("pin_title", req.product_title)[:100]
                    raw_desc = data.get("pin_description", "")
                    pin_desc = format_pin_description_with_hook(raw_desc, req.product_title, req.category)

                    board_rec = select_official_board(
                        category=req.category,
                        title=req.product_title,
                        candidate_board=data.get("board_recommendation")
                    )

                    return PinCopyResponse(
                        pin_title=pin_title,
                        pin_description=pin_desc,
                        hashtags=data.get("hashtags", ["#SmallSpaceHacks", "#AmazonFinds", "#AmazonAssociate"]),
                        board_recommendation=board_rec,
                        call_to_action=data.get("call_to_action", "Tap here to check today's price & details!"),
                        hook=data.get("hook", "The Small Space Find You Need"),
                        bridge_review=BridgeReview(
                            verdict=data.get("bridge_review", {}).get("verdict", "An exceptional space-saving solution engineered for compact living."),
                            pros=data.get("bridge_review", {}).get("pros", ["Space-efficient design", "High durability build", "Fast Prime delivery"]),
                            cons=data.get("bridge_review", {}).get("cons", ["High demand frequently leads to temporary backorders"]),
                            who_is_it_for=data.get("bridge_review", {}).get("who_is_it_for", "Anyone looking to maximize every square foot with verified top-tier utility."),
                        )
                    )
                except Exception as e:
                    if "503" in str(e) and attempt < 3:
                        delay = (2 ** attempt) + random.uniform(0, 1)
                        logger.warning(f"Gemini {model_name} 503 error, retrying in {delay:.2f}s...")
                        time.sleep(delay)
                        continue
                    logger.warning(f"Gemini {model_name} failed: {e}")
                    break
    except Exception as err:
        logger.warning(f"Gemini client initialization failed: {err}")

    return None


def generate_with_groq(req: CopyGenerationRequest) -> Optional[PinCopyResponse]:
    """Generate Pinterest copy using Groq (openai/gpt-oss-120b)."""
    if not GROQ_API_KEY:
        return None

    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)

        prompt = f"""You are an elite Pinterest marketing strategist for the @Smart_Spaces brand.
Create high-converting Pinterest copy and a bridge review for this product.
Product: {req.product_title}
Price: {req.price}
Category: {req.category}

REQUIREMENTS:
1. pin_title: Max 95 chars catchy title
2. pin_description: Max 480 chars description with an engaging Gen-Z conversational comment hook (e.g. 'Would you use this in your kitchen or bathroom? Drop your vote below! 👇' or 'Small space challenge: Could you fit everything in this setup? 🏠') and ending with #AmazonAssociate
3. board_recommendation: MUST BE EXACTLY ONE OF: 'Small Apartment Hacks', 'Space Saving Kitchens', 'Closet & Wardrobe Organization', 'Studio Living Ideas', 'Room Organization'

Return ONLY valid JSON matching this schema:
{{
  "pin_title": "Catchy title under 95 chars",
  "pin_description": "Description with Gen-Z comment hook and #AmazonAssociate",
  "hashtags": ["#SmallSpaceHacks", "#AmazonFinds", "#HomeOrganization", "#AmazonAssociate"],
  "board_recommendation": "One of the 5 official boards",
  "call_to_action": "Tap here to view on Amazon",
  "hook": "Punchy hook",
  "bridge_review": {{
    "verdict": "Clear summary verdict",
    "pros": ["Pro 1", "Pro 2", "Pro 3"],
    "cons": ["One minor consideration"],
    "who_is_it_for": "Target persona"
  }}
}}"""

        models = ["openai/gpt-oss-120b", "openai/gpt-oss-20b", "qwen/qwen3.8-27b"]

        for model_name in models:
            try:
                chat = client.chat.completions.create(
                    model=model_name,
                    messages=[{"role": "user", "content": prompt}],
                    response_format={"type": "json_object"}
                )
                content = chat.choices[0].message.content or ""
                clean_json = re.sub(r"^```(?:json)?\s*|\s*```$", "", content.strip(), flags=re.MULTILINE).strip()
                data = json.loads(clean_json)

                pin_title = data.get("pin_title", req.product_title)[:100]
                raw_desc = data.get("pin_description", "")
                pin_desc = format_pin_description_with_hook(raw_desc, req.product_title, req.category)

                board_rec = select_official_board(
                    category=req.category,
                    title=req.product_title,
                    candidate_board=data.get("board_recommendation")
                )

                logger.info(f"Groq copy generation successful with model: {model_name}")
                return PinCopyResponse(
                    pin_title=pin_title,
                    pin_description=pin_desc,
                    hashtags=data.get("hashtags", ["#SmallSpaceHacks", "#MustHaves", "#AmazonAssociate"]),
                    board_recommendation=board_rec,
                    call_to_action=data.get("call_to_action", "Tap here to check today's price & details!"),
                    hook=data.get("hook", "The Small Space Game Changer"),
                    bridge_review=BridgeReview(
                        verdict=data.get("bridge_review", {}).get("verdict", "An exceptional product with thousands of glowing reviews."),
                        pros=data.get("bridge_review", {}).get("pros", ["Verified customer favorite", "Exceptional ergonomics", "Fast Prime delivery"]),
                        cons=data.get("bridge_review", {}).get("cons", ["Stock sells out quickly during peak promotional events"]),
                        who_is_it_for=data.get("bridge_review", {}).get("who_is_it_for", "Ideal for anyone who values reliability and premium functionality."),
                    )
                )
            except Exception as m_err:
                logger.warning(f"Groq model {model_name} failed: {m_err}")
                continue

    except Exception as err:
        logger.warning(f"Groq copy generation failed: {err}")
        return None


def generate_fallback_rules(req: CopyGenerationRequest) -> PinCopyResponse:
    """Deterministic, FTC-compliant fallback generator if all AI models are unreachable."""
    title = f"Why Everyone Is Obsessed With The {req.product_title}"[:95]
    board_rec = select_official_board(req.category, req.product_title)

    raw_desc = (
        f"Looking for the ultimate {req.category.lower()} space-saving upgrade? "
        f"The {req.product_title} delivers outstanding reliability, smart storage efficiency, and verified customer ratings."
    )
    desc = format_pin_description_with_hook(raw_desc, req.product_title, req.category)

    return PinCopyResponse(
        pin_title=title,
        pin_description=desc,
        hashtags=["#SmallSpaceHacks", "#SpaceSaving", "#AmazonFinds", "#HomeDecor", "#AmazonAssociate"],
        board_recommendation=board_rec,
        call_to_action="Tap to check today's deal on Amazon ➔",
        hook="The Space-Saving Find You Need",
        bridge_review=BridgeReview(
            verdict=f"One of the highest-rated solutions in {req.category}, combining durability and compact space optimization.",
            pros=[
                "Overwhelmingly positive verified customer ratings",
                "Built with durable, premium materials engineered for longevity",
                "Backed by fast Prime delivery and 30-day hassle-free returns",
            ],
            cons=["Popular color variants frequently experience temporary stock shortages"],
            who_is_it_for=f"Anyone seeking a dependable, space-efficient upgrade for compact living.",
        )
    )


def generate_pin_copy(req: CopyGenerationRequest) -> PinCopyResponse:
    """Multi-tiered copy generation pipeline with guaranteed success."""
    # 1. Google Gemini
    res = generate_with_gemini(req)
    if res:
        return res

    # 2. Groq
    res = generate_with_groq(req)
    if res:
        return res

    # 3. Deterministic rule-based fallback
    return generate_fallback_rules(req)
