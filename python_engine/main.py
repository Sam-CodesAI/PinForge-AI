"""PinForge AI — FastAPI Core Engine.

High-velocity REST API serving product scraping, Pillow 2:3 pin graphics,
multi-model AI SEO copy generation, and Pinterest bulk export channels.
"""

import logging
from typing import List

from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from python_engine.config import HOST, PORT, STATIC_DIR
from python_engine.csv_exporter import generate_pinterest_bulk_csv
from python_engine.models import (
    CopyGenerationRequest,
    CsvExportRequest,
    ExtractRequest,
    PinCopyResponse,
    PinGenerateRequest,
    PinGenerateResponse,
    ProductData,
    ScheduleItem,
)
from python_engine.pin_generator import generate_pin_graphic
from python_engine.rss_generator import generate_pinterest_rss
from python_engine.scraper import fetch_product
from python_engine.seo_engine import generate_pin_copy

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
    }


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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("python_engine.main:app", host=HOST, port=PORT, reload=True)
