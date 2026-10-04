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


def generate_with_gemini(req: CopyGenerationRequest) -> Optional[PinCopyResponse]:
    """Generate Pinterest copy using Google Gemini."""
    if not GEMINI_API_KEY:
        return None

    try:
        from google import genai
        client = genai.Client(api_key=GEMINI_API_KEY)

        prompt = f"""You are an elite Pinterest affiliate marketing strategist and copywriter.
Create an irresistible, high-converting Pinterest Pin campaign and FTC-compliant review for this Amazon product.

Product: {req.product_title}
Brand: {req.brand or 'Amazon Choice'}
Category: {req.category}
Price: {req.price}
Key Features: {', '.join(req.features[:3]) if req.features else 'Top rated, highly functional, premium build quality'}

REQUIREMENTS:
1. pin_title: MUST BE STRICTLY UNDER 100 CHARACTERS. Include high-intent search keywords and an emotional hook.
2. pin_description: MUST BE STRICTLY UNDER 500 CHARACTERS. Explain why this product is worth buying, include keywords naturally, and end with the mandatory FTC disclosure hashtag: #AmazonAssociate
3. hashtags: 5-7 popular Pinterest search tags (e.g. #TechGadgets, #AestheticDesk, #AmazonFinds, #AmazonAssociate)
4. board_recommendation: 2-4 word Pinterest board name (e.g. "Smart Home Tech", "Viral Amazon Finds")
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

        # Real production Gemini 2026 models
        import time
        import random
        
        models = ["gemini-3.8-flash", "gemini-3.5-flash-lite"]
        valid_boards = ['Small Apartment Hacks', 'Space Saving Kitchens', 'Closet & Wardrobe Organization', 'Studio Living Ideas', 'Room Organization']
        for model_name in models:
            for attempt in range(1, 4):
                try:
                    resp = client.models.generate_content(
                        model=model_name,
                        contents=prompt
                    )
                    text = resp.text.strip()
                    # Remove code blocks if present
                    clean_json = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.MULTILINE).strip()
                    data = json.loads(clean_json)
    
                    # Ensure strict character boundaries
                    pin_title = data.get("pin_title", req.product_title)[:100]
                    pin_desc = data.get("pin_description", "")[:500]
                    if "#AmazonAssociate" not in pin_desc:
                        if len(pin_desc) + 18 <= 500:
                            pin_desc += " #AmazonAssociate"
                        else:
                            pin_desc = pin_desc[:480] + "... #AmazonAssociate"
    
                    board_rec = data.get("board_recommendation", "Room Organization")
                    if board_rec not in valid_boards:
                        board_rec = "Room Organization"
    
                    return PinCopyResponse(
                        pin_title=pin_title,
                        pin_description=pin_desc,
                        hashtags=data.get("hashtags", ["#AmazonFinds", "#Trending", "#AmazonAssociate"]),
                        board_recommendation=board_rec,
                        call_to_action=data.get("call_to_action", "Tap here to check today's price & details!"),
                        hook=data.get("hook", "The Amazon Find You Need"),
                        bridge_review=BridgeReview(
                            verdict=data.get("bridge_review", {}).get("verdict", "An exceptional blend of performance and value."),
                            pros=data.get("bridge_review", {}).get("pros", ["Premium design", "High reliability", "Prime delivery"]),
                            cons=data.get("bridge_review", {}).get("cons", ["High demand frequently leads to backorders"]),
                            who_is_it_for=data.get("bridge_review", {}).get("who_is_it_for", "Anyone looking to upgrade their daily setup with a verified top-tier product."),
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

        prompt = f"""You are an elite Pinterest marketing strategist.
Create high-converting Pinterest copy and a bridge review for this product.
Product: {req.product_title}
Price: {req.price}
Category: {req.category}

Return ONLY valid JSON matching this schema:
{{
  "pin_title": "Max 95 chars catchy title",
  "pin_description": "Max 480 chars description with #AmazonAssociate",
  "hashtags": ["#tag1", "#tag2", "#tag3", "#AmazonAssociate"],
  "board_recommendation": "Board Name",
  "call_to_action": "Tap here to view on Amazon",
  "hook": "Punchy hook",
  "bridge_review": {{
    "verdict": "Clear summary verdict",
    "pros": ["Pro 1", "Pro 2", "Pro 3"],
    "cons": ["One minor consideration"],
    "who_is_it_for": "Target persona"
  }}
}}"""

        valid_boards = [
            'Small Apartment Hacks',
            'Space Saving Kitchens',
            'Closet & Wardrobe Organization',
            'Studio Living Ideas',
            'Room Organization'
        ]
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
                pin_desc = data.get("pin_description", "")[:500]
                if "#AmazonAssociate" not in pin_desc:
                    pin_desc = (pin_desc[:480] + " #AmazonAssociate")[:500]

                board_rec = data.get("board_recommendation", "Room Organization")
                if board_rec not in valid_boards:
                    board_rec = "Room Organization"

                logger.info(f"Groq copy generation successful with model: {model_name}")
                return PinCopyResponse(
                    pin_title=pin_title,
                    pin_description=pin_desc,
                    hashtags=data.get("hashtags", ["#AmazonFinds", "#MustHaves", "#AmazonAssociate"]),
                    board_recommendation=board_rec,
                    call_to_action=data.get("call_to_action", "Tap here to check today's price & details!"),
                    hook=data.get("hook", "The Amazon Find You Need"),
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
    desc = (
        f"Looking for the ultimate {req.category.lower()} upgrade? "
        f"The {req.product_title} delivers outstanding reliability, premium craftsmanship, and verified customer ratings. "
        f"Tap here to explore today's best deal and full customer reviews! #AmazonFinds #{req.category.replace(' ', '')} #AmazonAssociate"
    )[:495]

    return PinCopyResponse(
        pin_title=title,
        pin_description=desc,
        hashtags=["#AmazonFinds", f"#{req.category.replace(' ', '')}", "#MustHaves", "#Trending", "#AmazonAssociate"],
        board_recommendation=f"{req.category} Favorites",
        call_to_action="Tap to check today's deal on Amazon ➔",
        hook="The Viral Amazon Find You Need",
        bridge_review=BridgeReview(
            verdict=f"One of the highest-rated products in {req.category}, combining durability and everyday convenience.",
            pros=[
                "Overwhelmingly positive verified customer ratings",
                "Built with durable, premium materials engineered for longevity",
                "Backed by fast Prime delivery and 30-day hassle-free returns",
            ],
            cons=["Popular color variants frequently experience temporary stock shortages"],
            who_is_it_for=f"Anyone seeking a dependable, high-performance upgrade in {req.category.lower()}.",
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
