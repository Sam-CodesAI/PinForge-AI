# PinForge AI ⚡

> **Autonomous Pinterest & Amazon Affiliate AI Automation Workflow System**  
> Turn any Amazon product URL or ASIN into viral, high-converting 1000x1500 px (2:3) Pinterest pins in 35ms, complete with search-optimized AI copy, FTC-compliant bridge landing pages, and triple-channel auto-publishing.

---

## 1. System Architecture

```
                                [ Amazon Product URL / ASIN ]
                                              │
                                              ▼
                                 ┌─────────────────────────┐
                                 │   Stealth Resolver      │
                                 │   (curl_cffi Chrome 124 │
                                 │   + Amazon Media CDN)   │
                                 └────────────┬────────────┘
                                              │
               ┌──────────────────────────────┼──────────────────────────────┐
               │                              │                              │
               ▼                              ▼                              ▼
   ┌───────────────────────┐      ┌───────────────────────┐      ┌───────────────────────┐
   │  Pillow 2:3 Compositor│      │  Multi-Model AI Copy  │      │  FTC Bridge Gateway   │
   │  1000x1500 (35ms CPU) │      │  (Gemini + Groq 120B) │      │  /p/[slug] Sub-Second │
   │  3 Aesthetic Systems  │      │  Strict Char Limits   │      │  Live Price Notices   │
   └───────────────────────┘      └───────────────────────┘      └───────────────────────┘
               │                              │                              │
               └──────────────────────────────┼──────────────────────────────┘
                                              │
                                              ▼
                                  ┌───────────────────────┐
                                  │  Triple-Channel Out   │
                                  │ 1. Bulk CSV (RFC 4180)│
                                  │ 2. Media RSS 2.0      │
                                  │ 3. Direct Web Intent  │
                                  └───────────────────────┘
```

---

## 2. Key Pillars & Core Invariants

### A. 35ms Pillow 2:3 Graphic Engine
- **Local CPU Processing:** Generates pixel-perfect 1000x1500 (2:3 Pinterest standard) graphics in **35ms–50ms** on standard CPU.
- **Zero Headless Browser Bloat:** Eliminates heavy Chromium, Puppeteer, or Satori memory leaks ($0.00 compute overhead).
- **3 High-Converting Design Systems:**
  1. `bento_dark`: Deep slate backdrop (`#0B0F19`), cyan radial glow, frosted white card, vector star ratings, and glowing deal pills.
  2. `warm_editorial`: Minimal alabaster/linen aesthetic (`#F9F6F0`), luxury serif typography, and natural shadow framing.
  3. `problem_solver`: High-contrast amber/navy hook banner, feature highlight checkmarks, deal alert badges, and action pills.

### B. Multi-Model AI SEO & Copy Studio
- **Multi-Model Resiliency:** Google Gemini (`gemini-flash-lite-latest` / `gemini-3.8-flash`) with automatic fallback to Groq (`openai/gpt-oss-120b`).
- **Strict Pinterest Limits:**
  * Pin Title: **Strictly under 100 characters** with search-intent keywords.
  * Pin Description: **Strictly under 500 characters** with mandatory FTC disclosure `#AmazonAssociate`.
  * Board Recommendations & Niche Hashtags.
  * Objective Bridge Reviews: Verdict, 3 pros, 1 con, and target persona.

### C. Zero-Shadowban FTC Bridge Gateway (`/p/[slug]`)
- **Direct Link Anti-Ban Protection:** Direct Amazon affiliate redirects trigger Pinterest spam filters and shadowbans. Intermediary bridge landing pages eliminate this risk entirely.
- **FTC & Amazon Compliance:**
  * Mandatory top/bottom disclosure: *"As an Amazon Associate I earn from qualifying purchases at no extra cost to you."*
  * Live price disclaimers protecting against Amazon Operating Agreement violations.
  * Schema.org structured data (`Product`, `AggregateRating`, `Offer`).

### D. Triple-Channel Publishing & Auto-Scheduling
1. **Channel 1 — Zero-Approval Media RSS (`/feed.xml`):** Pinterest Business accounts can connect this feed directly to auto-publish pins 24/7 without API approvals or token expiration.
2. **Channel 2 — Official Bulk Upload CSV:** Conforms strictly to Pinterest's lowercase snake_case schema (`board_name,title,description,link,image_url,published_at`) with automated staggering across peak viral hours.
3. **Channel 3 — Direct Web Intent:** 1-click pinning directly into the Pinterest pin creation modal.

---

## 3. Unit Economics

| Metric | PinForge AI | Traditional Headless SaaS |
| :--- | :--- | :--- |
| **Compute Cost** | **$0.0015 / Pin** (~$0.75 for 500 pins/mo) | $49 – $79 / month |
| **Render Latency** | **35ms – 50ms** (Pillow local CPU) | 2,500ms – 4,000ms (Puppeteer/Chromium) |
| **Shadowban Risk** | **0% Risk** (Intermediary bridge landing pages) | High (Direct shortlinks flagged by spam filters) |
| **Publishing Channels**| Triple Channel (Bulk CSV + Media RSS + Intent) | Single channel or API-locked |

---

## 4. Quickstart & Local Execution

### Prerequisites
- Node.js 20+ (with `pnpm`)
- Python 3.11+ (with `uv` recommended)

### 1. Launch the Python Engine
```bash
./scripts/start-engine.sh
```
*FastAPI runs on `http://127.0.0.1:8000` with Swagger docs available at `/docs`.*

### 2. Launch the Web Studio
```bash
pnpm install
pnpm run dev
```
*Opens the Next.js 16 Web Studio at `http://localhost:3000`.*

---

## 5. Repository & Architecture Details

- **GitHub Repository:** [`Sam-CodesAI/PinForge-AI`](https://github.com/Sam-CodesAI/PinForge-AI)
- **Primary Architect:** Samarth Kallappa Nimangre (SAM CODES)
- **License:** MIT
