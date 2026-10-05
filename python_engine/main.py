"""PinForge AI — FastAPI Core Engine.

High-velocity REST API serving product scraping, Pillow 2:3 pin graphics,
multi-model AI SEO copy generation, and Pinterest bulk export channels.
"""

from __future__ import annotations

import base64
import io
import json
import logging
import time
from typing import List
import uuid

from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from python_engine.config import (
    HOST,
    PORT,
    STATIC_DIR,
    PINS_DIR,
    BASE_URL,
    IDEOGRAM_API_KEY,
    FAL_KEY,
    POLLINATIONS_API_KEY,
)
from python_engine.csv_exporter import generate_pinterest_bulk_csv
from python_engine.models import (
    AutonomousCycleRequest,
    CopyGenerationRequest,
    CsvExportRequest,
    ExtractRequest,
    PinCopyResponse,
    PinGenerateRequest,
    PinGenerateResponse,
    PinterestPublishRequest,
    ProductData,
    ScheduleItem,
    VisualGenerateRequest,
    VisualGenerateResponse,
)
from python_engine.pin_generator import generate_pin_graphic
from python_engine.rss_generator import generate_pinterest_rss
from python_engine.scraper import fetch_product
from python_engine.seo_engine import generate_pin_copy
from python_engine.visual_engine import (
    generate_visual_with_waterfall,
    render_track_a_lifestyle_pin,
    sanitize_canvas_text,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("pinforge.main")

app = FastAPI(
    title="PinForge AI Engine",
    description="Pinterest & Amazon Affiliate AI Automation Workflow System",
    version="1.0.0",
)

# Enable CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static directory for rendered pins and assets
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.mount("/pins", StaticFiles(directory=PINS_DIR), name="pins")

# In-memory queue of recent forged items for RSS & CSV exports
FORGED_QUEUE: List[ScheduleItem] = []


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {
        "status": "online",
        "service": "PinForge AI Engine",
        "version": "1.0.0",
        "queue_count": len(FORGED_QUEUE),
        "visual_engine": {
            "ideogram_configured": bool(IDEOGRAM_API_KEY),
            "fal_configured": bool(FAL_KEY),
            "pollinations_configured": True,
            "tier4_fallback": "local_aesthetic_gradient",
        },
    }


@app.get("/api/visual/providers")
def get_visual_providers():
    """Return available multi-provider visual generation tiers and active credentials."""
    return {
        "tier1": {
            "provider": "ideogram",
            "model": "ideogram-v2",
            "specialty": "in-image typography, chalkboard jar labels, typography signage",
            "configured": bool(IDEOGRAM_API_KEY),
        },
        "tier2": {
            "provider": "fal",
            "model": "fal-ai/flux/dev",
            "specialty": "photorealistic 2700K Japandi architecture, warm interior textures",
            "configured": bool(FAL_KEY),
        },
        "tier3": {
            "provider": "pollinations",
            "model": "flux",
            "specialty": "free/open web generation with auto-fallback on 402/429",
            "configured": bool(POLLINATIONS_API_KEY),
        },
        "tier4": {
            "provider": "local_aesthetic",
            "model": "procedural_pillow_gradient",
            "specialty": "100% zero-crash 2700K ambient gradient & framing canvas",
            "configured": True,
        },
    }


@app.post("/api/visual/generate", response_model=VisualGenerateResponse)
def generate_visual_endpoint(req: VisualGenerateRequest):
    """Generate high-aesthetic Pinterest visual via 4-tier waterfall fallback or render Track A Pin."""
    start_time = time.perf_counter()
    try:
        # 1. Execute multi-tier waterfall visual generation
        result = generate_visual_with_waterfall(
            product_title=req.product_title,
            board_name=req.board_name,
            category=req.category,
            style=req.style,
            preferred_tier=req.preferred_tier,
        )

        # 2. If Track A requested, apply full-bleed editorial overlay atop the generated visual
        if req.track_a:
            pin_img = render_track_a_lifestyle_pin(
                title=req.product_title,
                board_name=req.board_name,
                category=req.category,
                style=req.style or "aspirational_lifestyle",
                base_image=result.image,
            )
            provider_label = f"track_a_{result.provider}"
        else:
            pin_img = result.image
            provider_label = result.provider

        filename = f"{'track_a_' if req.track_a else 'visual_'}{uuid.uuid4().hex[:10]}.png"
        output_path = PINS_DIR / filename
        pin_img.save(output_path, format="PNG")

        buffered = io.BytesIO()
        pin_img.save(buffered, format="PNG")
        b64_str = base64.b64encode(buffered.getvalue()).decode("utf-8")

        elapsed_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
        return VisualGenerateResponse(
            provider=provider_label,
            tier=result.tier,
            prompt_used=result.prompt_used,
            image_url=f"{BASE_URL}/pins/{filename}",
            base64_image=b64_str,
            render_time_ms=elapsed_ms,
            is_ai_generated=result.is_ai_generated,
            error_trail=result.error_trail,
        )
    except Exception as err:
        logger.error(f"Visual generation failed: {err}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Visual generation failed: {str(err)}")


@app.post("/api/extract", response_model=ProductData)
def extract_product_endpoint(req: ExtractRequest):
    """Extract product data from Amazon URL, shortlink (amzn.to), or ASIN."""
    try:
        product = fetch_product(req.url_or_asin, req.affiliate_tag)
        return product
    except ValueError as val_err:
        raise HTTPException(status_code=400, detail=str(val_err))
    except Exception as err:
        logger.error(f"Error extracting product: {err}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to extract Amazon product: {str(err)}")


@app.post("/api/generate-pin", response_model=PinGenerateResponse)
def generate_pin_endpoint(req: PinGenerateRequest):
    """Generate high-resolution 1000x1500 2:3 Pinterest Pin graphic."""
    try:
        res = generate_pin_graphic(req)
        return res
    except Exception as err:
        logger.error(f"Error generating pin: {err}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Graphic generation failed: {str(err)}")


@app.post("/api/generate-copy", response_model=PinCopyResponse)
def generate_copy_endpoint(req: CopyGenerationRequest):
    """Generate high-CTR title, SEO description, hashtags, board recommendation, and bridge review."""
    try:
        copy_res = generate_pin_copy(req)
        return copy_res
    except Exception as err:
        logger.error(f"Error generating copy: {err}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Copy generation failed: {str(err)}")


@app.post("/api/export-csv")
def export_csv_endpoint(req: CsvExportRequest):
    """Generate RFC-compliant Pinterest Bulk Upload CSV."""
    try:
        csv_text = generate_pinterest_bulk_csv(req)
        return Response(
            content=csv_text,
            media_type="text/csv",
            headers={"Content-Disposition": 'attachment; filename="pinterest_bulk_pins.csv"'},
        )
    except Exception as err:
        logger.error(f"Error generating CSV: {err}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"CSV export failed: {str(err)}")


@app.get("/feed.xml")
def rss_feed_endpoint():
    """Media RSS feed for zero-approval Pinterest Business auto-publishing."""
    try:
        xml_content = generate_pinterest_rss(FORGED_QUEUE)
        return Response(content=xml_content, media_type="application/rss+xml")
    except Exception as err:
        logger.error(f"Error generating RSS: {err}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to render RSS feed")


@app.get("/api/pinterest/account")
def get_pinterest_account():
    """Fetch authenticated @Smart_Spaces profile from Pinterest API v5."""
    try:
        from python_engine.pinterest_client import PinterestClient
    except ImportError:
        from pinterest_client import PinterestClient

    try:
        client = PinterestClient()
        return client.get_user_account()
    except Exception as e:
        logger.error(f"Failed to fetch Pinterest account: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/pinterest/boards")
def get_pinterest_boards():
    """Fetch active boards for @Smart_Spaces from Pinterest API v5."""
    try:
        from python_engine.pinterest_client import PinterestClient
    except ImportError:
        from pinterest_client import PinterestClient

    try:
        client = PinterestClient()
        return client.get_boards(force_refresh=True)
    except Exception as e:
        logger.error(f"Failed to fetch Pinterest boards: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/pinterest/publish")
def publish_pinterest_pin(req: PinterestPublishRequest):
    """Programmatic Pin Creation via Pinterest API v5 (supports single pins and multi-slide carousels)."""
    try:
        from python_engine.pinterest_client import PinterestClient
    except ImportError:
        from pinterest_client import PinterestClient

    try:
        client = PinterestClient()
        if req.slides and len(req.slides) >= 2:
            return client.publish_carousel_pin(
                title=req.title,
                description=req.description,
                board_name=req.board_name_or_id,
                slides=req.slides,
                link=req.link,
            )

        if not req.image_url:
            raise HTTPException(
                status_code=400,
                detail="Must provide either 'image_url' for single pins or 'slides' (>= 2) for carousels.",
            )

        board_id = client.get_or_create_board(req.board_name_or_id)
        result = client.create_pin(
            board_id=board_id,
            title=req.title,
            description=req.description,
            link=req.link or "",
            image_url=req.image_url,
        )
        return result
    except PermissionError as perm_err:
        raise HTTPException(status_code=403, detail=str(perm_err))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to publish pin: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/pinterest/analytics")
def get_pinterest_analytics(days: int = 30):
    """Fetch pin performance metrics for @Smart_Spaces."""
    try:
        from python_engine.pinterest_client import PinterestClient
    except ImportError:
        from pinterest_client import PinterestClient

    try:
        client = PinterestClient()
        return client.get_account_analytics(days=days)
    except Exception as e:
        logger.error(f"Failed to fetch analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/autonomous/run")
def run_autonomous_cycle(req: AutonomousCycleRequest):
    """Run full Antigravity agentic cycle: Scrape -> Copy -> 2:3 Graphic -> Bridge -> Pinterest."""
    try:
        from python_engine.antigravity_orchestrator import AntigravityOrchestrator
    except ImportError:
        from antigravity_orchestrator import AntigravityOrchestrator

    try:
        orchestrator = AntigravityOrchestrator()
        result = orchestrator.execute_autonomous_cycle(
            url_or_asin=req.url_or_asin,
            template_style=req.template_style,
            publish_live=req.publish_live,
            publish_as_carousel=req.publish_as_carousel,
            track_a=req.track_a,
        )
        return result
    except Exception as e:
        logger.error(f"Autonomous cycle failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/canva/app")
def get_canva_app_status():
    """Fetch linked Canva App metadata and preview URLs."""
    try:
        from python_engine.canva_client import CanvaClient
    except ImportError:
        from canva_client import CanvaClient

    client = CanvaClient()
    return client.get_app_info()


@app.post("/api/canva/autofill")
def autofill_canva_template(template_id: str, data: dict):
    """Trigger Canva Brand Template autofill with Amazon product data."""
    try:
        from python_engine.canva_client import CanvaClient
    except ImportError:
        from canva_client import CanvaClient

    client = CanvaClient()
    result = client.create_autofill_job(template_id=template_id, data=data)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Canva autofill failed"))
    return result


@app.post("/api/ai/hunt-and-publish")
def ai_hunt_and_publish(publish_live: bool = True, track_a: bool = False):
    """Autonomously hunt a viral space-saving Amazon product, curate with vision, and publish live."""
    try:
        from python_engine.autonomous_autopilot import AutonomousAutopilot
    except ImportError:
        from autonomous_autopilot import AutonomousAutopilot

    autopilot = AutonomousAutopilot()
    try:
        return autopilot.run_autopilot_cycle(publish_live=publish_live, track_a=track_a)
    except Exception as e:
        logger.error(f"AI hunt and publish failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/ai/autopilot/history")
def get_autopilot_history():
    """Retrieve execution log of autonomous AI runs."""
    from python_engine.config import DATA_DIR
    history_file = DATA_DIR / "autopilot_history.json"
    if history_file.exists():
        try:
            return json.loads(history_file.read_text())
        except Exception:
            return []
    return []


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("python_engine.main:app", host=HOST, port=PORT, reload=True)

