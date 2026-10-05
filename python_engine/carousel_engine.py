"""PinForge AI — Premium E-Commerce Carousel Pin Engine.

Renders 4-Slide Pinterest Carousel suites matching modern mobile shopping apps:
- Slide 1: Hero Showcase & Viral Hook (Aesthetic hero visual + rating + price pill)
- Slide 2: Left-Side Specs & Deep Details (Dimensions, materials, capacity, setup)
- Slide 3: Variant Gallery & Right-Side Thumbnail Stack (Multi-angle up/down list)
- Slide 4: Real-Life Uses & Problem-Solver Transformation (3 use cases + conversion CTA)
- Slide 5 (Bonus): 4-in-1 Composite Grid Pin for ultra-high feed click-through rate.

Supports creative aesthetic styles:
- 'anime': Studio Ghibli / Makoto Shinkai warm anime aesthetic
- 'story': Cinematic 35mm film photography storytelling
- 'luxury_editorial': Architectural Digest / Japandi minimalist
- 'cyber_bento': Modern 2026 dark bento grid with glowing accents
"""

from __future__ import annotations

import io
import logging
import math
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import httpx
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from python_engine.config import BASE_URL, FONTS_DIR, PINS_DIR
from python_engine.models import PinGenerateRequest, PinGenerateResponse
from python_engine.pin_generator import (
    CANVAS_HEIGHT,
    CANVAS_WIDTH,
    download_image,
    draw_star,
    get_font,
    wrap_text,
)

logger = logging.getLogger("pinforge.carousel")

BOLD_FONT_PATH = FONTS_DIR / "Inter-Bold.ttf"
REGULAR_FONT_PATH = FONTS_DIR / "Inter-Regular.ttf"
SERIF_FONT_PATH = FONTS_DIR / "Editorial-Serif.ttf"


def _draw_progress_dots(draw: ImageDraw.ImageDraw, active_index: int, total: int = 4, y: int = 1435):
    """Draws sleek shopping-app pagination indicator dots at bottom."""
    dot_radius = 6
    spacing = 26
    total_w = (total - 1) * spacing
    start_x = (CANVAS_WIDTH - total_w) // 2

    for i in range(total):
        cx = start_x + (i * spacing)
        if i == active_index:
            # Active pill shape
            draw.rounded_rectangle([cx - 14, y - 5, cx + 14, y + 5], radius=6, fill=(245, 158, 11, 255))
        else:
            draw.ellipse([cx - dot_radius, y - dot_radius, cx + dot_radius, y + dot_radius], fill=(100, 116, 139, 180))


def _draw_style_background(style: str) -> Image.Image:
    """Generates base background canvas based on chosen aesthetic style."""
    if style == "anime":
        # Warm golden-hour anime watercolor interior tones
        bg = Image.new("RGBA", (CANVAS_WIDTH, CANVAS_HEIGHT), (254, 243, 199, 255))
        glow = Image.new("RGBA", (CANVAS_WIDTH, CANVAS_HEIGHT), (0, 0, 0, 0))
        g_draw = ImageDraw.Draw(glow)
        # Golden hour sun beam
        g_draw.polygon([(0, 0), (600, 0), (300, 1500), (0, 1500)], fill=(251, 191, 36, 45))
        g_draw.ellipse([500, 200, 1100, 800], fill=(244, 114, 182, 35))
        glow = glow.filter(ImageFilter.GaussianBlur(80))
        return Image.alpha_composite(bg, glow)

    elif style == "story":
        # Warm 35mm film grain, moody espresso and amber tones
        bg = Image.new("RGBA", (CANVAS_WIDTH, CANVAS_HEIGHT), (28, 25, 23, 255))
        glow = Image.new("RGBA", (CANVAS_WIDTH, CANVAS_HEIGHT), (0, 0, 0, 0))
        g_draw = ImageDraw.Draw(glow)
        g_draw.ellipse([200, 150, 800, 750], fill=(217, 119, 6, 40))
        glow = glow.filter(ImageFilter.GaussianBlur(100))
        return Image.alpha_composite(bg, glow)

    elif style == "luxury_editorial":
        # Alabaster linen & soft architectural stone
        bg = Image.new("RGBA", (CANVAS_WIDTH, CANVAS_HEIGHT), (249, 246, 240, 255))
        draw = ImageDraw.Draw(bg)
        draw.rectangle([30, 30, CANVAS_WIDTH - 30, CANVAS_HEIGHT - 30], outline=(226, 221, 212, 255), width=2)
        return bg

    else:
        # cyber_bento default: Deep Obsidian with Cyan/Amber glow
        bg = Image.new("RGBA", (CANVAS_WIDTH, CANVAS_HEIGHT), (11, 15, 25, 255))
        glow = Image.new("RGBA", (CANVAS_WIDTH, CANVAS_HEIGHT), (0, 0, 0, 0))
        g_draw = ImageDraw.Draw(glow)
        g_draw.ellipse([150, 180, 850, 880], fill=(56, 189, 248, 40))
        g_draw.ellipse([250, 700, 850, 1300], fill=(245, 158, 11, 30))
        glow = glow.filter(ImageFilter.GaussianBlur(95))
        return Image.alpha_composite(bg, glow)


# ============================================================================
# SLIDE 1: First Product Showcase (Hero Hook)
# ============================================================================
def render_slide1_showcase(
    title: str,
    price: str,
    rating: float,
    review_count: str,
    product_img: Optional[Image.Image],
    badge_text: str = "VIRAL AMAZON FIND",
    friction_badge: str = "100% RENTER FRIENDLY • NO DRILL",
    style: str = "cyber_bento",
) -> Image.Image:
    """Slide 1: First Product Showcase with bold hero visual, rating, price pill, and Gen-Z friction badge."""
    img = _draw_style_background(style)
    draw = ImageDraw.Draw(img)

    # 1. Top Category Pill
    badge_font = get_font(BOLD_FONT_PATH, 24)
    b_text = f"✦ {badge_text.upper()}"
    bbox = badge_font.getbbox(b_text)
    bw = (bbox[2] - bbox[0]) + 40
    bx0 = (CANVAS_WIDTH - bw) // 2
    draw.rounded_rectangle([bx0, 60, bx0 + bw, 108], radius=24, fill=(15, 23, 42, 230), outline=(245, 158, 11, 255), width=2)
    draw.text((bx0 + 20, 72), b_text, fill=(251, 191, 36, 255), font=badge_font)

    # 2. Hero Headline
    title_font_size = 46 if len(title) < 55 else 38
    title_font = get_font(BOLD_FONT_PATH, title_font_size)
    lines = wrap_text(title, title_font, max_width=860)[:3]
    cur_y = 135
    for line in lines:
        line_bbox = title_font.getbbox(line)
        lw = line_bbox[2] - line_bbox[0]
        lx = (CANVAS_WIDTH - lw) // 2
        fill_color = (248, 250, 252, 255) if style != "luxury_editorial" and style != "anime" else (28, 25, 23, 255)
        draw.text((lx, cur_y), line, fill=fill_color, font=title_font)
        cur_y += title_font_size + 12

    # 3. Center Hero Card
    card_x0, card_y0 = 80, max(cur_y + 25, 290)
    card_w, card_h = 840, 680
    card_x1, card_y1 = card_x0 + card_w, card_y0 + card_h

    # Card shadow
    shadow = Image.new("RGBA", (CANVAS_WIDTH, CANVAS_HEIGHT), (0, 0, 0, 0))
    s_draw = ImageDraw.Draw(shadow)
    s_draw.rounded_rectangle([card_x0 - 5, card_y0 + 10, card_x1 + 5, card_y1 + 25], radius=32, fill=(0, 0, 0, 110))
    shadow = shadow.filter(ImageFilter.GaussianBlur(25))
    img = Image.alpha_composite(img, shadow)

    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([card_x0, card_y0, card_x1, card_y1], radius=28, fill=(255, 255, 255, 255), outline=(226, 232, 240, 255), width=2)

    # Product image composite
    if product_img:
        max_pw, max_ph = card_w - 90, card_h - 90
        p_ratio = min(max_pw / product_img.width, max_ph / product_img.height)
        new_pw, new_ph = int(product_img.width * p_ratio), int(product_img.height * p_ratio)
        resized_p = product_img.resize((new_pw, new_ph), Image.Resampling.LANCZOS)
        px = card_x0 + (card_w - new_pw) // 2
        py = card_y0 + (card_h - new_ph) // 2
        img.paste(resized_p, (px, py), resized_p if resized_p.mode == "RGBA" else None)

    # Prominent Gen-Z Neon Friction Badge on Card
    f_badge = (friction_badge or "100% RENTER FRIENDLY • NO DRILL").upper()
    if not any(f_badge.startswith(p) for p in ["⚡", "🔥", "✦"]):
        f_badge = f"⚡ {f_badge}"
    fb_font = get_font(BOLD_FONT_PATH, 22)
    fb_bbox = fb_font.getbbox(f_badge)
    fb_w = (fb_bbox[2] - fb_bbox[0]) + 40
    fb_x = card_x0 + (card_w - fb_w) // 2
    fb_y = card_y1 - 60
    draw.rounded_rectangle([fb_x, fb_y, fb_x + fb_w, fb_y + 44], radius=22, fill=(15, 23, 42, 245), outline=(16, 185, 129, 255), width=2)
    draw.text((fb_x + 20, fb_y + 10), f_badge, fill=(52, 211, 153, 255), font=fb_font)

    # 4. Rating Bar
    bar_y = card_y1 + 45
    for s in range(5):
        f_color = (251, 191, 36, 255) if s < math.floor(rating) else (100, 116, 139, 255)
        draw_star(draw, 90 + s * 34, bar_y + 12, 13, 6, f_color)

    r_font = get_font(BOLD_FONT_PATH, 26)
    draw.text((275, bar_y - 2), f"{rating:.1f} • {review_count}", fill=(203, 213, 225, 255) if style == "cyber_bento" or style == "story" else (41, 37, 36, 255), font=r_font)

    # Price pill
    p_font = get_font(BOLD_FONT_PATH, 44)
    p_bbox = p_font.getbbox(price)
    pw = p_bbox[2] - p_bbox[0]
    draw.text((CANVAS_WIDTH - 90 - pw, bar_y - 12), price, fill=(52, 211, 153, 255), font=p_font)

    # 5. Swipe Prompt Pill
    btn_y0 = CANVAS_HEIGHT - 185
    draw.rounded_rectangle([80, btn_y0, CANVAS_WIDTH - 80, btn_y0 + 85], radius=24, fill=(14, 165, 233, 255))
    cta_font = get_font(BOLD_FONT_PATH, 30)
    cta_text = "SWIPE FOR PRODUCT SPECS ➔"
    c_bbox = cta_font.getbbox(cta_text)
    draw.text(((CANVAS_WIDTH - (c_bbox[2] - c_bbox[0])) // 2, btn_y0 + 26), cta_text, fill=(255, 255, 255, 255), font=cta_font)

    _draw_progress_dots(draw, active_index=0)
    return img


# ============================================================================
# SLIDE 2: Left-Side Product Details & Specs
# ============================================================================
def render_slide2_specs(
    title: str,
    price: str,
    features: List[str],
    product_img: Optional[Image.Image],
    friction_highlights: Optional[List[str]] = None,
    friction_badge: str = "TOOL-FREE 60S SETUP",
    style: str = "cyber_bento",
) -> Image.Image:
    """Slide 2: Shopping app spec breakdown with details on left side and zoomed product on right."""
    img = _draw_style_background(style)
    draw = ImageDraw.Draw(img)

    # Top Header
    h_font = get_font(BOLD_FONT_PATH, 36)
    draw.text((70, 65), "DEEP SPECIFICATIONS & BUILD", fill=(245, 158, 11, 255), font=h_font)

    sub_font = get_font(REGULAR_FONT_PATH, 24)
    draw.text((70, 115), "Engineered for maximum utility in compact spaces", fill=(148, 163, 184, 255), font=sub_font)

    # Left Side Specs Panel (Width: 440px)
    left_x = 70
    left_w = 420
    panel_y0 = 175

    spec_items = [
        ("📐 EXACT FIT", "Ultra-slim compact profile engineered to slide into narrow gaps."),
        ("🛡️ RENTER-SAFE", "100% damage-free structure with zero drilling or wall holes required."),
        ("⚡ POP-UP SETUP", "Tool-free fast assembly ready straight out of the box in under 60s."),
        ("⚖️ LOAD TESTED", "Heavy-duty reinforced alloy framework with smooth mobility."),
    ]
    if friction_highlights:
        default_headers = ["🛡️ RENTER-SAFE", "⚡ QUICK SETUP", "📐 DIMENSIONS", "⚖️ CAPACITY"]
        for i, h in enumerate(friction_highlights[:4]):
            spec_items[i] = (default_headers[i], f"{h} — Engineered for compact living.")
    elif features:
        for i, f in enumerate(features[:4]):
            spec_items[i] = (f"✓ FEATURE {i+1}", f[:70] + "..." if len(f) > 70 else f)

    card_y = panel_y0
    for title_txt, desc_txt in spec_items:
        draw.rounded_rectangle([left_x, card_y, left_x + left_w, card_y + 130], radius=18, fill=(24, 32, 47, 240), outline=(51, 65, 85, 255), width=2)
        # Spec title
        st_font = get_font(BOLD_FONT_PATH, 22)
        draw.text((left_x + 18, card_y + 14), title_txt, fill=(56, 189, 248, 255), font=st_font)
        # Spec description wrapped
        sd_font = get_font(REGULAR_FONT_PATH, 19)
        d_lines = wrap_text(desc_txt, sd_font, max_width=left_w - 36)[:3]
        d_cur_y = card_y + 44
        for dl in d_lines:
            draw.text((left_x + 18, d_cur_y), dl, fill=(226, 232, 240, 255), font=sd_font)
            d_cur_y += 24

        card_y += 145

    # Right Side Zoomed Product Showcase (Width: 380px)
    right_x = 520
    right_w = 410
    right_h = 565
    draw.rounded_rectangle([right_x, panel_y0, right_x + right_w, panel_y0 + right_h], radius=24, fill=(255, 255, 255, 255), outline=(226, 232, 240, 255), width=2)

    if product_img:
        max_pw, max_ph = right_w - 50, right_h - 50
        p_ratio = min(max_pw / product_img.width, max_ph / product_img.height)
        new_pw, new_ph = int(product_img.width * p_ratio), int(product_img.height * p_ratio)
        resized_p = product_img.resize((new_pw, new_ph), Image.Resampling.LANCZOS)
        px = right_x + (right_w - new_pw) // 2
        py = panel_y0 + (right_h - new_ph) // 2
        img.paste(resized_p, (px, py), resized_p if resized_p.mode == "RGBA" else None)

    # Stamped Gen-Z Neon Friction Badge on right panel
    rz_badge = f"✦ {(friction_badge or 'TOOL-FREE 60S SETUP').upper()}"
    rz_font = get_font(BOLD_FONT_PATH, 16)
    rz_bbox = rz_font.getbbox(rz_badge)
    rz_w = (rz_bbox[2] - rz_bbox[0]) + 28
    rz_x = right_x + (right_w - rz_w) // 2
    draw.rounded_rectangle([rz_x, panel_y0 + 16, rz_x + rz_w, panel_y0 + 48], radius=16, fill=(15, 23, 42, 230), outline=(56, 189, 248, 255), width=2)
    draw.text((rz_x + 14, panel_y0 + 23), rz_badge, fill=(56, 189, 248, 255), font=rz_font)

    # Right Side Price Callout
    draw.rounded_rectangle([right_x + 20, panel_y0 + right_h - 75, right_x + right_w - 20, panel_y0 + right_h - 18], radius=14, fill=(15, 23, 42, 240))
    rp_font = get_font(BOLD_FONT_PATH, 26)
    rp_text = f"PRICE: {price}"
    draw.text((right_x + 35, panel_y0 + right_h - 65), rp_text, fill=(52, 211, 153, 255), font=rp_font)

    # Bottom Swipe Prompt
    btn_y0 = CANVAS_HEIGHT - 185
    draw.rounded_rectangle([70, btn_y0, CANVAS_WIDTH - 70, btn_y0 + 85], radius=24, fill=(56, 189, 248, 255))
    cta_font = get_font(BOLD_FONT_PATH, 30)
    cta_text = "SWIPE FOR PRODUCT VARIANTS ➔"
    c_bbox = cta_font.getbbox(cta_text)
    draw.text(((CANVAS_WIDTH - (c_bbox[2] - c_bbox[0])) // 2, btn_y0 + 26), cta_text, fill=(15, 23, 42, 255), font=cta_font)

    _draw_progress_dots(draw, active_index=1)
    return img


# ============================================================================
# SLIDE 3: Product Variant Images Side List (Right Up / Down)
# ============================================================================
def render_slide3_variants(
    title: str,
    price: str,
    product_img: Optional[Image.Image],
    additional_images: Optional[List[str]] = None,
    style: str = "cyber_bento",
) -> Image.Image:
    """Slide 3: Shopping app variant selector with main view on left and vertical thumbnail list on right."""
    img = _draw_style_background(style)
    draw = ImageDraw.Draw(img)

    # Header
    h_font = get_font(BOLD_FONT_PATH, 36)
    draw.text((70, 65), "ANGLES & DESIGN VARIANTS", fill=(245, 158, 11, 255), font=h_font)

    sub_font = get_font(REGULAR_FONT_PATH, 24)
    draw.text((70, 115), "Multi-perspective inspection & finish options", fill=(148, 163, 184, 255), font=sub_font)

    # Main Left Perspective Card (Width: 540px)
    main_x, main_y0 = 70, 175
    main_w, main_h = 540, 580
    draw.rounded_rectangle([main_x, main_y0, main_x + main_w, main_y0 + main_h], radius=26, fill=(255, 255, 255, 255), outline=(226, 232, 240, 255), width=2)

    if product_img:
        max_pw, max_ph = main_w - 60, main_h - 60
        p_ratio = min(max_pw / product_img.width, max_ph / product_img.height)
        new_pw, new_ph = int(product_img.width * p_ratio), int(product_img.height * p_ratio)
        resized_p = product_img.resize((new_pw, new_ph), Image.Resampling.LANCZOS)
        px = main_x + (main_w - new_pw) // 2
        py = main_y0 + (main_h - new_ph) // 2
        img.paste(resized_p, (px, py), resized_p if resized_p.mode == "RGBA" else None)

    # Right-Side Vertical Thumbnail Stack (Top, Middle, Down - 3 cards)
    right_x = 640
    thumb_w, thumb_h = 290, 175
    thumb_y = main_y0

    # Try downloading additional images if provided, else use crop variants of main
    thumbs = []
    if additional_images:
        for a_url in additional_images[:3]:
            dl = download_image(a_url)
            if dl:
                thumbs.append(dl)

    # If no alternate images, create cropped focus angles from main
    if len(thumbs) < 3 and product_img:
        w, h = product_img.size
        thumbs.append(product_img.crop((0, 0, w, int(h * 0.45))))
        thumbs.append(product_img.crop((int(w * 0.1), int(h * 0.25), int(w * 0.9), int(h * 0.75))))
        thumbs.append(product_img.crop((0, int(h * 0.55), w, h)))

    labels = ["ANGLE 1 (FULL)", "DETAIL (FOLDED)", "BASE & WHEELS"]
    for i in range(3):
        cur_ty = thumb_y + (i * 200)
        border_color = (245, 158, 11, 255) if i == 0 else (51, 65, 85, 255)
        border_width = 3 if i == 0 else 1
        draw.rounded_rectangle([right_x, cur_ty, right_x + thumb_w, cur_ty + thumb_h], radius=18, fill=(255, 255, 255, 255), outline=border_color, width=border_width)

        if i < len(thumbs) and thumbs[i]:
            t_img = thumbs[i]
            t_ratio = min((thumb_w - 30) / t_img.width, (thumb_h - 40) / t_img.height)
            tw, th = int(t_img.width * t_ratio), int(t_img.height * t_ratio)
            resized_t = t_img.resize((tw, th), Image.Resampling.LANCZOS)
            tpx = right_x + (thumb_w - tw) // 2
            tpy = cur_ty + (thumb_h - 20 - th) // 2
            img.paste(resized_t, (tpx, tpy), resized_t if resized_t.mode == "RGBA" else None)

        # Micro label badge
        lbl_font = get_font(BOLD_FONT_PATH, 14)
        lbl_txt = labels[i]
        draw.rounded_rectangle([right_x + 10, cur_ty + thumb_h - 26, right_x + thumb_w - 10, cur_ty + thumb_h - 6], radius=6, fill=(15, 23, 42, 220))
        draw.text((right_x + 20, cur_ty + thumb_h - 24), lbl_txt, fill=(245, 158, 11, 255), font=lbl_font)

    # Color Variant Chips Bar
    chip_y = main_y0 + main_h + 35
    chip_font = get_font(BOLD_FONT_PATH, 20)
    color_chips = [
        ("⚫ Matte Black", (30, 41, 59, 255)),
        ("⚪ Warm Ivory", (71, 85, 105, 255)),
        ("🔘 Slate Gray", (51, 65, 85, 255)),
    ]
    cur_cx = 70
    for c_text, bg_col in color_chips:
        c_bbox = chip_font.getbbox(c_text)
        cw = (c_bbox[2] - c_bbox[0]) + 30
        draw.rounded_rectangle([cur_cx, chip_y, cur_cx + cw, chip_y + 44], radius=22, fill=bg_col, outline=(245, 158, 11, 200), width=1)
        draw.text((cur_cx + 15, chip_y + 10), c_text, fill=(248, 250, 252, 255), font=chip_font)
        cur_cx += cw + 16

    # Bottom Swipe Prompt
    btn_y0 = CANVAS_HEIGHT - 185
    draw.rounded_rectangle([70, btn_y0, CANVAS_WIDTH - 70, btn_y0 + 85], radius=24, fill=(16, 185, 129, 255))
    cta_font = get_font(BOLD_FONT_PATH, 30)
    cta_text = "SWIPE FOR LIFESTYLE USES ➔"
    c_bbox = cta_font.getbbox(cta_text)
    draw.text(((CANVAS_WIDTH - (c_bbox[2] - c_bbox[0])) // 2, btn_y0 + 26), cta_text, fill=(255, 255, 255, 255), font=cta_font)

    _draw_progress_dots(draw, active_index=2)
    return img


# ============================================================================
# SLIDE 4: Real-Life Uses & Problem Solver Transformation
# ============================================================================
def render_slide4_uses(
    title: str,
    price: str,
    product_img: Optional[Image.Image],
    friction_highlights: Optional[List[str]] = None,
    friction_badge: str = "100% RENTER FRIENDLY • NO DRILL",
    style: str = "cyber_bento",
) -> Image.Image:
    """Slide 4: Real-world practical uses in everyday life, before/after transformation, and purchase CTA."""
    img = _draw_style_background(style)
    draw = ImageDraw.Draw(img)

    # Header
    h_font = get_font(BOLD_FONT_PATH, 38)
    draw.text((70, 65), "3 WAYS TO TRANSFORM YOUR SPACE", fill=(245, 158, 11, 255), font=h_font)

    sub_font = get_font(REGULAR_FONT_PATH, 24)
    draw.text((70, 120), "How verified buyers maximize every square inch", fill=(148, 163, 184, 255), font=sub_font)

    use_cases = [
        ("1. SMALL APARTMENTS & STUDIOS • NO DRILL", "Slips into narrow unutilized gaps between appliances or furniture, unlocking immediate vertical storage without wall damage."),
        ("2. BATHROOM & LAUNDRY ESSENTIAL", "Moisture-resistant materials keep damp towels and toiletries organized, off counters, and perfectly ventilated."),
        ("3. TOOL-FREE 60S ASSEMBLY & FOLD", "Reclaims floor space and keeps daily essentials accessible while folding completely flat in seconds when moving."),
    ]
    if friction_highlights:
        default_descs = [
            "Unlocks immediate vertical storage without permanent wall damage or landlord friction.",
            "Instant setup straight out of the box so you reclaim living space immediately.",
            "Engineered to fit tight compact floor plans while maximizing storage utility.",
        ]
        for idx, h in enumerate(friction_highlights[:3]):
            use_cases[idx] = (f"{idx+1}. {h}", default_descs[idx])

    card_y = 185
    for heading, desc in use_cases:
        draw.rounded_rectangle([70, card_y, CANVAS_WIDTH - 70, card_y + 160], radius=20, fill=(24, 32, 47, 240), outline=(245, 158, 11, 160), width=2)
        head_font = get_font(BOLD_FONT_PATH, 24)
        draw.text((95, card_y + 18), heading, fill=(251, 191, 36, 255), font=head_font)
        body_font = get_font(REGULAR_FONT_PATH, 21)
        b_lines = wrap_text(desc, body_font, max_width=CANVAS_WIDTH - 190)[:3]
        by = card_y + 55
        for bl in b_lines:
            draw.text((95, by), bl, fill=(226, 232, 240, 255), font=body_font)
            by += 28

        card_y += 180

    # Stamped Gen-Z Neon Friction Badge on Slide 4
    f_badge = f"✦ {(friction_badge or '100% RENTER FRIENDLY • NO DRILL').upper()}"
    fb_font = get_font(BOLD_FONT_PATH, 22)
    fb_bbox = fb_font.getbbox(f_badge)
    fb_w = min((fb_bbox[2] - fb_bbox[0]) + 40, CANVAS_WIDTH - 140)
    fb_x = (CANVAS_WIDTH - fb_w) // 2
    fb_y = card_y + 20
    draw.rounded_rectangle([fb_x, fb_y, fb_x + fb_w, fb_y + 46], radius=23, fill=(15, 23, 42, 245), outline=(52, 211, 153, 255), width=2)
    draw.text((fb_x + 20, fb_y + 11), f_badge, fill=(52, 211, 153, 255), font=fb_font)

    # Trust Guarantees
    t_y = fb_y + 65
    t_font = get_font(BOLD_FONT_PATH, 22)
    draw.text((70, t_y), "✓ 100% Renter Safe • No Drill", fill=(56, 189, 248, 255), font=t_font)
    draw.text((450, t_y), "✓ Fast Prime 2-Day Delivery", fill=(56, 189, 248, 255), font=t_font)

    # Final Conversion CTA Button
    btn_y0 = CANVAS_HEIGHT - 210
    btn_h = 100
    draw.rounded_rectangle([70, btn_y0, CANVAS_WIDTH - 70, btn_y0 + btn_h], radius=28, fill=(245, 158, 11, 255))

    btn_font = get_font(BOLD_FONT_PATH, 34)
    btn_text = f"CHECK TODAY'S DEAL ({price}) ➔"
    b_bbox = btn_font.getbbox(btn_text)
    draw.text(((CANVAS_WIDTH - (b_bbox[2] - b_bbox[0])) // 2, btn_y0 + 30), btn_text, fill=(15, 23, 42, 255), font=btn_font)

    # FTC Disclosure
    ftc_font = get_font(REGULAR_FONT_PATH, 16)
    ftc_text = "FTC Disclosure: As an Amazon Associate I earn from qualifying purchases"
    f_bbox = ftc_font.getbbox(ftc_text)
    draw.text(((CANVAS_WIDTH - (f_bbox[2] - f_bbox[0])) // 2, CANVAS_HEIGHT - 65), ftc_text, fill=(148, 163, 184, 255), font=ftc_font)

    _draw_progress_dots(draw, active_index=3)
    return img


# ============================================================================
# COMPOSITE 4-IN-1 GRID PIN (For Single-Pin High-CTR Feeds)
# ============================================================================
def render_composite_carousel_preview(slides: List[Image.Image], friction_badge: str = "100% RENTER FRIENDLY • NO DRILL") -> Image.Image:
    """Combines all 4 carousel slides into a high-converting 2x2 grid overview pin."""
    comp = Image.new("RGBA", (CANVAS_WIDTH, CANVAS_HEIGHT), (11, 15, 25, 255))
    draw = ImageDraw.Draw(comp)

    # Top Banner
    b_font = get_font(BOLD_FONT_PATH, 30)
    b_text = "✦ COMPLETE PRODUCT BREAKDOWN & REVIEW ✦"
    b_bbox = b_font.getbbox(b_text)
    draw.text(((CANVAS_WIDTH - (b_bbox[2] - b_bbox[0])) // 2, 45), b_text, fill=(251, 191, 36, 255), font=b_font)

    # 2x2 Grid of Thumbnails
    cell_w, cell_h = 425, 638  # (approx 2:3 aspect)
    positions = [
        (65, 110),     # Slide 1 (Top-Left)
        (510, 110),    # Slide 2 (Top-Right)
        (65, 765),     # Slide 3 (Bottom-Left)
        (510, 765),    # Slide 4 (Bottom-Right)
    ]

    for idx, pos in enumerate(positions):
        if idx < len(slides):
            thumb = slides[idx].resize((cell_w, cell_h), Image.Resampling.LANCZOS)
            comp.paste(thumb, pos)
            draw.rounded_rectangle([pos[0], pos[1], pos[0] + cell_w, pos[1] + cell_h], radius=14, outline=(245, 158, 11, 180), width=2)

    # Center Gen-Z Friction Badge Callout
    center_pill = f"✦ {friction_badge.upper()} ➔"
    cp_font = get_font(BOLD_FONT_PATH, 22)
    cp_bbox = cp_font.getbbox(center_pill)
    cp_w = (cp_bbox[2] - cp_bbox[0]) + 44
    cpx = (CANVAS_WIDTH - cp_w) // 2
    draw.rounded_rectangle([cpx, 725, cpx + cp_w, 775], radius=24, fill=(15, 23, 42, 245), outline=(16, 185, 129, 255), width=2)
    draw.text((cpx + 22, 739), center_pill, fill=(52, 211, 153, 255), font=cp_font)

    # Bottom CTA Button
    btn_y0 = CANVAS_HEIGHT - 85
    draw.rounded_rectangle([65, btn_y0, CANVAS_WIDTH - 65, btn_y0 + 65], radius=18, fill=(245, 158, 11, 255))
    cta_f = get_font(BOLD_FONT_PATH, 26)
    c_txt = "EXPLORE FULL AMAZON DEAL ➔"
    cb = cta_f.getbbox(c_txt)
    draw.text(((CANVAS_WIDTH - (cb[2] - cb[0])) // 2, btn_y0 + 18), c_txt, fill=(15, 23, 42, 255), font=cta_f)

    return comp


# ============================================================================
# MASTER CAROUSEL GENERATOR
# ============================================================================
def generate_carousel_pin_suite(
    title: str,
    price: str,
    rating: float,
    review_count: str,
    image_url: str,
    features: List[str],
    additional_images: Optional[List[str]] = None,
    badge_text: str = "VIRAL AMAZON FIND",
    friction_badge: str = "100% RENTER FRIENDLY • NO DRILL",
    friction_highlights: Optional[List[str]] = None,
    style: str = "cyber_bento",
) -> Dict[str, Any]:
    """Generates the full 4-slide shopping app carousel + 1 composite overview graphic."""
    product_img = download_image(image_url)
    if not product_img:
        try:
            from python_engine.pollinations_engine import (
                build_lifestyle_prompt,
                generate_pollinations_image,
            )
            l_prompt = build_lifestyle_prompt(title, style=style)
            product_img = generate_pollinations_image(l_prompt, timeout=15.0)
            if product_img:
                logger.info(f"✓ Generated high-res Pollinations visual fallback for carousel: '{title[:40]}'")
        except Exception as e:
            logger.warning(f"Could not generate pollinations fallback for carousel: {e}")

    # Generate 4 slides
    s1 = render_slide1_showcase(title, price, rating, review_count, product_img, badge_text, friction_badge, style)
    s2 = render_slide2_specs(title, price, features, product_img, friction_highlights, friction_badge, style)
    s3 = render_slide3_variants(title, price, product_img, additional_images, style)
    s4 = render_slide4_uses(title, price, product_img, friction_highlights, friction_badge, style)

    slides = [s1, s2, s3, s4]
    slide_paths = []
    uid = uuid.uuid4().hex[:8]

    for idx, slide in enumerate(slides, start=1):
        rgb_s = slide.convert("RGB")
        file_name = f"carousel_slide_{idx}_{uid}.jpg"
        f_path = PINS_DIR / file_name
        rgb_s.save(f_path, format="JPEG", quality=92, optimize=True)
        slide_paths.append(str(f_path))

    # Generate composite 4-in-1 overview
    composite = render_composite_carousel_preview(slides, friction_badge=friction_badge)
    rgb_c = composite.convert("RGB")
    comp_file_name = f"carousel_composite_{uid}.jpg"
    comp_path = PINS_DIR / comp_file_name
    rgb_c.save(comp_path, format="JPEG", quality=92, optimize=True)

    return {
        "slide_paths": slide_paths,
        "composite_path": str(comp_path),
        "total_slides": len(slide_paths),
        "style": style,
        "friction_badge": friction_badge,
    }
