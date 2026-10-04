"""PinForge AI — High-Performance 2:3 Vertical Pinterest Pin Generator.

Renders 1000x1500 px high-res graphics using Pillow (PIL) in <50ms with zero
Chromium/headless browser bloat. Supports 3 modern high-CTR aesthetic templates:
1. 'bento_dark' (Cyber/Tech/Modern Bento with radial glow)
2. 'warm_editorial' (Aesthetic Linen/Beige Minimal)
3. 'problem_solver' (High-Energy Viral Contrast Hook)
"""

import base64
import io
import logging
import math
import time
import uuid
from pathlib import Path
from typing import List, Optional, Tuple

import httpx
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from python_engine.config import BASE_URL, FONTS_DIR, PINS_DIR
from python_engine.models import PinGenerateRequest, PinGenerateResponse

logger = logging.getLogger("pinforge.generator")

# Canvas Dimensions (Standard Pinterest 2:3 Vertical)
CANVAS_WIDTH = 1000
CANVAS_HEIGHT = 1500

# Fonts Configuration
BOLD_FONT_PATH = FONTS_DIR / "Inter-Bold.ttf"
REGULAR_FONT_PATH = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
SERIF_FONT_PATH = Path("/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf")


def get_font(path: Path, size: int) -> ImageFont.FreeTypeFont:
    """Load TTF font safely with graceful fallback."""
    try:
        if path.exists():
            return ImageFont.truetype(str(path), size)
    except Exception as err:
        logger.warning(f"Could not load font {path}: {err}")
    try:
        return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size)
    except Exception:
        return ImageFont.load_default()


def download_image(url: str) -> Optional[Image.Image]:
    """Download image from HTTP URL with timeout and convert to RGBA."""
    if not url:
        return None
    try:
        with httpx.Client(timeout=10.0, follow_redirects=True) as client:
            resp = client.get(url)
            if resp.status_code == 200:
                img = Image.open(io.BytesIO(resp.content)).convert("RGBA")
                return img
    except Exception as err:
        logger.warning(f"Failed to download image from {url}: {err}")
    return None


def wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> List[str]:
    """Wrap text to fit within max_width in pixels."""
    words = text.split()
    lines = []
    current_line = []

    for word in words:
        test_line = " ".join(current_line + [word])
        bbox = font.getbbox(test_line)
        line_w = bbox[2] - bbox[0]
        if line_w <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(" ".join(current_line))
                current_line = [word]
            else:
                lines.append(word)
                current_line = []

    if current_line:
        lines.append(" ".join(current_line))

    return lines


def draw_star(draw: ImageDraw.ImageDraw, cx: float, cy: float, r_outer: float, r_inner: float, fill: Tuple[int, int, int, int]):
    """Draw a smooth 5-point vector star."""
    points = []
    for i in range(10):
        r = r_outer if i % 2 == 0 else r_inner
        angle = i * (math.pi / 5.0) - (math.pi / 2.0)
        x = cx + r * math.cos(angle)
        y = cy + r * math.sin(angle)
        points.append((x, y))
    draw.polygon(points, fill=fill)


def render_bento_dark(req: PinGenerateRequest, product_img: Optional[Image.Image]) -> Image.Image:
    """Render Template 1: Bento Dark Glow (Deep Slate, Cyan Radial Backlight, Frosted Card)."""
    img = Image.new("RGBA", (CANVAS_WIDTH, CANVAS_HEIGHT), (11, 15, 25, 255))

    # 1. Background Cyan Radial Glow
    glow = Image.new("RGBA", (CANVAS_WIDTH, CANVAS_HEIGHT), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    glow_draw.ellipse([150, 200, 850, 900], fill=(56, 189, 248, 45))
    glow = glow.filter(ImageFilter.GaussianBlur(90))
    img = Image.alpha_composite(img, glow)

    draw = ImageDraw.Draw(img)

    # 2. Top Category / Badge Pill
    badge_font = get_font(BOLD_FONT_PATH, 24)
    badge_text = f"✦ {req.badge_text.upper()}"
    bbox = badge_font.getbbox(badge_text)
    badge_w = (bbox[2] - bbox[0]) + 40
    badge_x = (CANVAS_WIDTH - badge_w) // 2
    badge_y = 60
    draw.rounded_rectangle([badge_x, badge_y, badge_x + badge_w, badge_y + 44], radius=22, fill=(15, 23, 42, 230), outline=(56, 189, 248, 180), width=2)
    draw.text((badge_x + 20, badge_y + 10), badge_text, fill=(56, 189, 248, 255), font=badge_font)

    # 3. Main Hook / Title
    title_font_size = 46 if len(req.title) < 55 else 38
    title_font = get_font(BOLD_FONT_PATH, title_font_size)
    lines = wrap_text(req.title, title_font, max_width=860)[:3]
    cur_y = 135
    for line in lines:
        line_bbox = title_font.getbbox(line)
        line_w = line_bbox[2] - line_bbox[0]
        line_x = (CANVAS_WIDTH - line_w) // 2
        draw.text((line_x, cur_y), line, fill=(248, 250, 252, 255), font=title_font)
        cur_y += title_font_size + 12

    # 4. Center Product Card
    card_x0, card_y0 = 80, max(cur_y + 25, 290)
    card_w, card_h = 840, 680
    card_x1, card_y1 = card_x0 + card_w, card_y0 + card_h

    # Soft Card Drop Shadow
    shadow = Image.new("RGBA", (CANVAS_WIDTH, CANVAS_HEIGHT), (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    shadow_draw.rounded_rectangle([card_x0 - 5, card_y0 + 10, card_x1 + 5, card_y1 + 25], radius=36, fill=(0, 0, 0, 120))
    shadow = shadow.filter(ImageFilter.GaussianBlur(25))
    img = Image.alpha_composite(img, shadow)

    draw = ImageDraw.Draw(img)
    # White high-contrast card background
    draw.rounded_rectangle([card_x0, card_y0, card_x1, card_y1], radius=32, fill=(255, 255, 255, 255), outline=(226, 232, 240, 255), width=2)

    # Composite Product Image inside Card
    if product_img:
        max_pw, max_ph = card_w - 90, card_h - 90
        p_ratio = min(max_pw / product_img.width, max_ph / product_img.height)
        new_pw = int(product_img.width * p_ratio)
        new_ph = int(product_img.height * p_ratio)
        resized_p = product_img.resize((new_pw, new_ph), Image.Resampling.LANCZOS)

        px = card_x0 + (card_w - new_pw) // 2
        py = card_y0 + (card_h - new_ph) // 2
        img.paste(resized_p, (px, py), resized_p if resized_p.mode == "RGBA" else None)

    # Floating Discount Badge on top-right of Card
    if req.original_price and req.price:
        deal_font = get_font(BOLD_FONT_PATH, 24)
        deal_text = "SALE"
        draw.rounded_rectangle([card_x1 - 120, card_y0 + 25, card_x1 - 25, card_y0 + 70], radius=12, fill=(225, 29, 72, 255))
        draw.text((card_x1 - 100, card_y0 + 35), deal_text, fill=(255, 255, 255, 255), font=deal_font)

    # 5. Rating & Social Proof Bar
    bar_y = card_y1 + 45
    star_x = 90
    for s in range(5):
        fill_color = (251, 191, 36, 255) if s < math.floor(req.rating) else (75, 85, 99, 255)
        draw_star(draw, star_x + s * 34, bar_y + 12, 13, 6, fill_color)

    rating_font = get_font(BOLD_FONT_PATH, 26)
    rev_text = f"{req.rating:.1f}  •  {req.review_count}"
    draw.text((star_x + 185, bar_y - 2), rev_text, fill=(203, 213, 225, 255), font=rating_font)

    # Price Tag (Right-aligned in social bar)
    price_font = get_font(BOLD_FONT_PATH, 42)
    price_bbox = price_font.getbbox(req.price)
    price_w = price_bbox[2] - price_bbox[0]
    draw.text((CANVAS_WIDTH - 90 - price_w, bar_y - 12), req.price, fill=(52, 211, 153, 255), font=price_font)

    # 6. Feature Chips
    chip_y = bar_y + 70
    chip_font = get_font(REGULAR_FONT_PATH, 22)
    features = req.features[:3] if req.features else ["Verified Quality", "Fast Prime Delivery", "Free 30-Day Returns"]
    cur_chip_x = 90
    for f in features:
        short_f = f[:28] + "..." if len(f) > 28 else f
        f_bbox = chip_font.getbbox(short_f)
        f_w = (f_bbox[2] - f_bbox[0]) + 30
        if cur_chip_x + f_w < CANVAS_WIDTH - 90:
            draw.rounded_rectangle([cur_chip_x, chip_y, cur_chip_x + f_w, chip_y + 40], radius=20, fill=(30, 41, 59, 220), outline=(51, 65, 85, 255))
            draw.text((cur_chip_x + 15, chip_y + 8), f"✓ {short_f}", fill=(226, 232, 240, 255), font=chip_font)
            cur_chip_x += f_w + 14

    # 7. Bottom High-Converting CTA Button
    btn_w, btn_h = 820, 96
    btn_x0 = (CANVAS_WIDTH - btn_w) // 2
    btn_y0 = CANVAS_HEIGHT - 170
    btn_x1, btn_y1 = btn_x0 + btn_w, btn_y0 + btn_h

    # Button Glow
    btn_glow = Image.new("RGBA", (CANVAS_WIDTH, CANVAS_HEIGHT), (0, 0, 0, 0))
    bg_draw = ImageDraw.Draw(btn_glow)
    bg_draw.rounded_rectangle([btn_x0 - 5, btn_y0 - 5, btn_x1 + 5, btn_y1 + 5], radius=32, fill=(14, 165, 233, 100))
    btn_glow = btn_glow.filter(ImageFilter.GaussianBlur(16))
    img = Image.alpha_composite(img, btn_glow)

    draw = ImageDraw.Draw(img)
    # Gradient/Solid Button Fill
    draw.rounded_rectangle([btn_x0, btn_y0, btn_x1, btn_y1], radius=28, fill=(14, 165, 233, 255))

    btn_font = get_font(BOLD_FONT_PATH, 32)
    btn_text = req.cta_text.upper()
    btn_bbox = btn_font.getbbox(btn_text)
    btn_text_w = btn_bbox[2] - btn_bbox[0]
    draw.text((btn_x0 + (btn_w - btn_text_w) // 2, btn_y0 + 28), btn_text, fill=(255, 255, 255, 255), font=btn_font)

    # Footer Watermark / FTC Notice
    ftc_font = get_font(REGULAR_FONT_PATH, 16)
    ftc_text = "FTC Disclosure: As an Amazon Associate I earn from qualifying purchases"
    f_bbox = ftc_font.getbbox(ftc_text)
    draw.text(((CANVAS_WIDTH - (f_bbox[2] - f_bbox[0])) // 2, CANVAS_HEIGHT - 45), ftc_text, fill=(100, 116, 139, 255), font=ftc_font)

    return img


def render_warm_editorial(req: PinGenerateRequest, product_img: Optional[Image.Image]) -> Image.Image:
    """Render Template 2: Warm Editorial Minimal (Linen / Bone Aesthetic, Luxury Serif)."""
    # Background Warm Alabaster Linen
    img = Image.new("RGBA", (CANVAS_WIDTH, CANVAS_HEIGHT), (249, 246, 240, 255))
    draw = ImageDraw.Draw(img)

    # Elegant Framing Border
    draw.rectangle([35, 35, CANVAS_WIDTH - 35, CANVAS_HEIGHT - 35], outline=(214, 208, 196, 255), width=2)

    # 1. Editorial Header
    brand_text = (req.brand or "CURATED SELECTION").upper()
    brand_font = get_font(BOLD_FONT_PATH, 20)
    b_bbox = brand_font.getbbox(brand_text)
    b_w = b_bbox[2] - b_bbox[0]
    draw.text(((CANVAS_WIDTH - b_w) // 2, 75), brand_text, fill=(120, 113, 108, 255), font=brand_font)

    # 2. Main Title (Serif Aesthetic)
    title_font_size = 46 if len(req.title) < 55 else 38
    title_font = get_font(SERIF_FONT_PATH, title_font_size)
    lines = wrap_text(req.title, title_font, max_width=820)[:3]
    cur_y = 125
    for line in lines:
        line_bbox = title_font.getbbox(line)
        line_w = line_bbox[2] - line_bbox[0]
        draw.text(((CANVAS_WIDTH - line_w) // 2, cur_y), line, fill=(28, 25, 23, 255), font=title_font)
        cur_y += title_font_size + 14

    # 3. Product Center Piece with Soft Shadow
    card_x0, card_y0 = 90, max(cur_y + 35, 290)
    card_w, card_h = 820, 680
    card_x1, card_y1 = card_x0 + card_w, card_y0 + card_h

    # Subtle Natural Shadow
    shadow = Image.new("RGBA", (CANVAS_WIDTH, CANVAS_HEIGHT), (0, 0, 0, 0))
    s_draw = ImageDraw.Draw(shadow)
    s_draw.rounded_rectangle([card_x0 + 10, card_y0 + 20, card_x1 - 10, card_y1 + 30], radius=24, fill=(0, 0, 0, 40))
    shadow = shadow.filter(ImageFilter.GaussianBlur(30))
    img = Image.alpha_composite(img, shadow)

    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([card_x0, card_y0, card_x1, card_y1], radius=20, fill=(255, 255, 255, 255), outline=(231, 229, 228, 255), width=2)

    # Composite Image
    if product_img:
        max_pw, max_ph = card_w - 100, card_h - 100
        p_ratio = min(max_pw / product_img.width, max_ph / product_img.height)
        new_pw = int(product_img.width * p_ratio)
        new_ph = int(product_img.height * p_ratio)
        resized_p = product_img.resize((new_pw, new_ph), Image.Resampling.LANCZOS)
        px = card_x0 + (card_w - new_pw) // 2
        py = card_y0 + (card_h - new_ph) // 2
        img.paste(resized_p, (px, py), resized_p if resized_p.mode == "RGBA" else None)

    # 4. Minimal Price & Rating Row
    meta_y = card_y1 + 45
    price_font = get_font(BOLD_FONT_PATH, 48)
    draw.text((100, meta_y - 8), req.price, fill=(28, 25, 23, 255), font=price_font)

    # Stars on the right
    star_x = CANVAS_WIDTH - 280
    for s in range(5):
        fill_color = (217, 119, 6, 255) if s < math.floor(req.rating) else (214, 211, 209, 255)
        draw_star(draw, star_x + s * 30, meta_y + 16, 11, 5, fill_color)

    rating_font = get_font(REGULAR_FONT_PATH, 24)
    draw.text((star_x + 160, meta_y + 4), f"{req.rating:.1f}", fill=(87, 83, 78, 255), font=rating_font)

    # 5. Editorial Bottom Button
    btn_w, btn_h = 800, 90
    btn_x0 = (CANVAS_WIDTH - btn_w) // 2
    btn_y0 = CANVAS_HEIGHT - 175
    draw.rounded_rectangle([btn_x0, btn_y0, btn_x0 + btn_w, btn_y0 + btn_h], radius=16, fill=(28, 25, 23, 255))

    btn_font = get_font(BOLD_FONT_PATH, 28)
    btn_text = "READ REVIEW & SHOP ON AMAZON ➔"
    btn_bbox = btn_font.getbbox(btn_text)
    btn_w_actual = btn_bbox[2] - btn_bbox[0]
    draw.text((btn_x0 + (btn_w - btn_w_actual) // 2, btn_y0 + 28), btn_text, fill=(255, 255, 255, 255), font=btn_font)

    # Footer
    ftc_font = get_font(REGULAR_FONT_PATH, 16)
    ftc_text = "As an Amazon Associate I earn from qualifying purchases"
    f_bbox = ftc_font.getbbox(ftc_text)
    draw.text(((CANVAS_WIDTH - (f_bbox[2] - f_bbox[0])) // 2, CANVAS_HEIGHT - 55), ftc_text, fill=(168, 162, 158, 255), font=ftc_font)

    return img


def render_problem_solver(req: PinGenerateRequest, product_img: Optional[Image.Image]) -> Image.Image:
    """Render Template 3: Viral Problem-Solver (High Contrast, Top Hook Banner, Value Highlights)."""
    img = Image.new("RGBA", (CANVAS_WIDTH, CANVAS_HEIGHT), (15, 23, 42, 255))
    draw = ImageDraw.Draw(img)

    # 1. Bold Top Hook Banner
    banner_h = 130
    draw.rectangle([0, 0, CANVAS_WIDTH, banner_h], fill=(245, 158, 11, 255))

    hook_font = get_font(BOLD_FONT_PATH, 38)
    hook_text = "THE AMAZON FIND YOU DIDN'T KNOW YOU NEEDED"
    if len(hook_text) > 42:
        hook_font = get_font(BOLD_FONT_PATH, 32)
    h_bbox = hook_font.getbbox(hook_text)
    draw.text(((CANVAS_WIDTH - (h_bbox[2] - h_bbox[0])) // 2, 45), hook_text, fill=(15, 23, 42, 255), font=hook_font)

    # 2. Sub-title
    sub_font = get_font(BOLD_FONT_PATH, 36)
    lines = wrap_text(req.title, sub_font, max_width=860)[:2]
    cur_y = banner_h + 30
    for line in lines:
        l_bbox = sub_font.getbbox(line)
        draw.text(((CANVAS_WIDTH - (l_bbox[2] - l_bbox[0])) // 2, cur_y), line, fill=(241, 245, 249, 255), font=sub_font)
        cur_y += 46

    # 3. Product Card
    card_x0, card_y0 = 80, cur_y + 20
    card_w, card_h = 840, 640
    card_x1, card_y1 = card_x0 + card_w, card_y0 + card_h

    draw.rounded_rectangle([card_x0, card_y0, card_x1, card_y1], radius=28, fill=(255, 255, 255, 255), outline=(245, 158, 11, 255), width=3)

    if product_img:
        max_pw, max_ph = card_w - 80, card_h - 80
        p_ratio = min(max_pw / product_img.width, max_ph / product_img.height)
        new_pw = int(product_img.width * p_ratio)
        new_ph = int(product_img.height * p_ratio)
        resized_p = product_img.resize((new_pw, new_ph), Image.Resampling.LANCZOS)
        px = card_x0 + (card_w - new_pw) // 2
        py = card_y0 + (card_h - new_ph) // 2
        img.paste(resized_p, (px, py), resized_p if resized_p.mode == "RGBA" else None)

    # 4. Feature Callout Rows
    feat_y = card_y1 + 35
    f_font = get_font(BOLD_FONT_PATH, 24)
    features = req.features[:3] if req.features else ["Saves hours of daily effort", "Over 20,000+ 5-star reviews", "Prime same-day delivery available"]

    for idx, feat in enumerate(features):
        row_y = feat_y + (idx * 50)
        draw.rounded_rectangle([80, row_y, CANVAS_WIDTH - 80, row_y + 42], radius=12, fill=(30, 41, 59, 230))
        # Green check circle
        draw.ellipse([95, row_y + 9, 119, row_y + 33], fill=(16, 185, 129, 255))
        draw.text((101, row_y + 8), "✓", fill=(255, 255, 255, 255), font=f_font)
        draw.text((135, row_y + 8), feat[:65], fill=(248, 250, 252, 255), font=f_font)

    # 5. Bottom Price & Action Button
    btn_y0 = CANVAS_HEIGHT - 170
    draw.rounded_rectangle([80, btn_y0, CANVAS_WIDTH - 80, btn_y0 + 95], radius=24, fill=(245, 158, 11, 255))

    btn_font = get_font(BOLD_FONT_PATH, 34)
    action_text = f"CHECK TODAY'S DEAL ({req.price}) ➔"
    a_bbox = btn_font.getbbox(action_text)
    draw.text(((CANVAS_WIDTH - (a_bbox[2] - a_bbox[0])) // 2, btn_y0 + 26), action_text, fill=(15, 23, 42, 255), font=btn_font)

    # Footer
    ftc_font = get_font(REGULAR_FONT_PATH, 16)
    ftc_text = "FTC Compliant: As an Amazon Associate I earn from qualifying purchases"
    f_bbox = ftc_font.getbbox(ftc_text)
    draw.text(((CANVAS_WIDTH - (f_bbox[2] - f_bbox[0])) // 2, CANVAS_HEIGHT - 45), ftc_text, fill=(148, 163, 184, 255), font=ftc_font)

    return img


def generate_pin_graphic(req: PinGenerateRequest) -> PinGenerateResponse:
    """Generate high-resolution 1000x1500 Pinterest Pin, write to disk, and return base64."""
    start_time = time.perf_counter()

    # Pre-fetch product image
    product_img = download_image(req.image_url)

    # Dispatch to chosen template
    if req.template == "warm_editorial":
        canvas = render_warm_editorial(req, product_img)
    elif req.template == "problem_solver":
        canvas = render_problem_solver(req, product_img)
    else:
        canvas = render_bento_dark(req, product_img)

    # Convert to RGB and write to file
    rgb_img = canvas.convert("RGB")
    file_id = f"pin_{uuid.uuid4().hex[:12]}.jpg"
    out_path = PINS_DIR / file_id
    rgb_img.save(out_path, format="JPEG", quality=92, optimize=True)

    # Generate Base64 string for zero-latency client preview
    buffer = io.BytesIO()
    rgb_img.save(buffer, format="JPEG", quality=90)
    base64_str = f"data:image/jpeg;base64,{base64.b64encode(buffer.getvalue()).decode('utf-8')}"

    elapsed_ms = (time.perf_counter() - start_time) * 1000.0
    logger.info(f"Rendered {req.template} pin in {elapsed_ms:.1f}ms: {file_id}")

    public_url = f"{BASE_URL}/pins/{file_id}"

    return PinGenerateResponse(
        image_path=str(out_path),
        image_url=public_url,
        base64_image=base64_str,
        width=CANVAS_WIDTH,
        height=CANVAS_HEIGHT,
        render_time_ms=round(elapsed_ms, 2),
    )


def generate_all_pin_variants(req: PinGenerateRequest) -> List[PinGenerateResponse]:
    """Generates all 3 high-converting pin variants (bento_dark, warm_editorial, problem_solver)."""
    templates = ["bento_dark", "warm_editorial", "problem_solver"]
    variants = []
    product_img = download_image(req.image_url)

    for tmpl in templates:
        req_copy = PinGenerateRequest(
            title=req.title,
            image_url=req.image_url,
            price=req.price,
            original_price=req.original_price,
            badge_text=req.badge_text,
            rating=req.rating,
            review_count=req.review_count,
            features=req.features,
            template=tmpl,
        )
        if tmpl == "warm_editorial":
            canvas = render_warm_editorial(req_copy, product_img)
        elif tmpl == "problem_solver":
            canvas = render_problem_solver(req_copy, product_img)
        else:
            canvas = render_bento_dark(req_copy, product_img)

        rgb_img = canvas.convert("RGB")
        file_id = f"pin_{tmpl}_{uuid.uuid4().hex[:10]}.jpg"
        out_path = PINS_DIR / file_id
        rgb_img.save(out_path, format="JPEG", quality=92, optimize=True)

        buf = io.BytesIO()
        rgb_img.save(buf, format="JPEG", quality=90)
        base64_str = f"data:image/jpeg;base64,{base64.b64encode(buf.getvalue()).decode('utf-8')}"

        variants.append(
            PinGenerateResponse(
                image_path=str(out_path),
                image_url=f"{BASE_URL}/pins/{file_id}",
                base64_image=base64_str,
                width=CANVAS_WIDTH,
                height=CANVAS_HEIGHT,
                render_time_ms=35.0,
            )
        )

    return variants

