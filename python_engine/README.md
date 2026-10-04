# PinForge AI — Python Core Engine

High-performance e-commerce scraping, 1000x1500 px (2:3) vertical Pinterest graphic generation, multi-model AI SEO copywriting, and Pinterest bulk export channels.

---

## 1. Architecture Overview

```
                                  [ User Input / Amazon URL / ASIN ]
                                                  │
                                                  ▼
                                      ┌──────────────────────┐
                                      │   FastAPI Router     │
                                      │   (python_engine)    │
                                      └──────────┬───────────┘
                                                 │
                   ┌─────────────────────────────┼─────────────────────────────┐
                   │                             │                             │
                   ▼                             ▼                             ▼
       ┌──────────────────────┐      ┌──────────────────────┐      ┌──────────────────────┐
       │   Product Scraper    │      │  Pillow 2:3 Graphic  │      │   AI SEO & Copy      │
       │ (curl_cffi + Amazon) │      │  Compositor (35ms)   │      │   (Gemini + Groq)    │
       └──────────────────────┘      └──────────────────────┘      └──────────────────────┘
                   │                             │                             │
                   └─────────────────────────────┼─────────────────────────────┘
                                                 │
                                                 ▼
                                     ┌──────────────────────┐
                                     │  Triple-Channel Out  │
                                     │ 1. Bulk CSV (RFC)    │
                                     │ 2. Media RSS 2.0     │
                                     │ 3. Next.js Bridge    │
                                     └──────────────────────┘
```

---

## 2. API Endpoints

| Method | Endpoint | Description | Payload / Response |
| :--- | :--- | :--- | :--- |
| `GET` | `/health` | Health & status check | Status JSON + queue count |
| `POST` | `/api/extract` | Extract Amazon product | `{ "url_or_asin": "B09XS7JWHH", "affiliate_tag": "tag-20" }` |
| `POST` | `/api/generate-pin` | Render 1000x1500 Pin in Pillow | `{ "title": "...", "image_url": "...", "template": "bento_dark" }` |
| `POST` | `/api/generate-copy`| Multi-model AI copy & SEO | `{ "product_title": "...", "price": "$348.00" }` |
| `POST` | `/api/export-csv` | Pinterest Bulk Upload CSV | Conforms to official Pinterest snake_case schema |
| `GET` | `/feed.xml` | Media RSS 2.0 XML | Zero-approval auto-publishing feed |

---

## 3. Pinterest Compliance & Character Limits

- **Pin Title:** Max **100 characters** (high-intent search keywords + emotional hook).
- **Pin Description:** Max **500 characters** (FTC disclosure `#AmazonAssociate` mandatory).
- **Aspect Ratio:** **2:3 Vertical (1000 x 1500 pixels)**.
- **Bulk CSV Schema:** `board_name,title,description,link,image_url,published_at` (all lowercase snake_case).
- **Bridge Gateway:** Intermediary landing page (`/p/[slug]`) prevents shadowbans and includes FTC disclosures and live price disclaimers.

---

## 4. Launching the Engine

```bash
# Launch directly using the workspace script
./scripts/start-pinforge-engine.sh

# Or run with uvicorn in the virtual environment
python_engine/.venv/bin/uvicorn python_engine.main:app --host 0.0.0.0 --port 8000 --reload
```
