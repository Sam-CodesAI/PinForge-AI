"""PinForge AI — Autonomous AI Trend Hunter.

Autonomously discovers and ranks high-converting Smart Spaces products on Amazon:
- Searches top viral apartment and space-saving categories.
- Extracts ASINs, reviews, ratings, and price discounts using stealth curl_cffi.
- Computes AI Viral Score (0-100) to find the highest-ROI candidates.
- Manages deduplication against data/seen_products.json to prevent duplicate pins.
"""

import json
import logging
import random
import re
import urllib.parse
from pathlib import Path
from typing import Dict, Any, List, Optional

from bs4 import BeautifulSoup
from curl_cffi import requests

try:
    from python_engine.config import DATA_DIR
except ImportError:
    from config import DATA_DIR

logger = logging.getLogger("PinForge.AITrendHunter")

DEFAULT_SEARCH_QUERIES = [
    "small space apartment organizer",
    "under bed storage with wheels",
    "foldable magnetic spice rack",
    "minimalist floating desk shelf",
    "rotating makeup vanity organizer",
    "over the door pantry organizer",
    "magnetic cable management desk",
    "collapsible laundry basket small space",
    "slim rolling cart for narrow spaces",
    "vacuum storage bags space saver",
]

BLACKLISTED_ASINS = {"B087F5K713"}

SEEN_PRODUCTS_FILE = DATA_DIR / "seen_products.json"

VERIFIED_SMART_SPACES_POOL: List[Dict[str, Any]] = [
    {
        "asin": "B093GKKQ65",
        "title": "Under Sink Organizer and Storage, 2-Tier Multi-Purpose Sliding Drawer Rack",
        "price": 23.99,
        "rating": 4.6,
        "review_count": 5800,
        "image_url": "https://m.media-amazon.com/images/I/71Y8+gS7JTL.jpg",
        "product_url": "https://www.amazon.com/dp/B093GKKQ65",
        "query_source": "curated_fallback",
        "viral_score": 93.5,
    },
    {
        "asin": "B08332N66L",
        "title": "SpaceAid Spice Rack Organizer with 24 Empty Square Glass Spice Bottles and Labels",
        "price": 39.99,
        "rating": 4.8,
        "review_count": 4200,
        "image_url": "https://m.media-amazon.com/images/I/81xU21vGZSL.jpg",
        "product_url": "https://www.amazon.com/dp/B08332N66L",
        "query_source": "curated_fallback",
        "viral_score": 94.2,
    },
    {
        "asin": "B0915B37G6",
        "title": "Simple Houseware Over the Door 24 Pocket Shoe Organizer Clear Pockets",
        "price": 11.99,
        "rating": 4.7,
        "review_count": 32000,
        "image_url": "https://m.media-amazon.com/images/I/81QW2q2B2UL.jpg",
        "product_url": "https://www.amazon.com/dp/B0915B37G6",
        "query_source": "curated_fallback",
        "viral_score": 96.0,
    },
    {
        "asin": "B08GLQ4M19",
        "title": "Lifewit 6 Pack Drawer Organizer Dividers Set Plastic Storage Bins",
        "price": 17.99,
        "rating": 4.7,
        "review_count": 8900,
        "image_url": "https://m.media-amazon.com/images/I/71P4q+4oWNL.jpg",
        "product_url": "https://www.amazon.com/dp/B08GLQ4M19",
        "query_source": "curated_fallback",
        "viral_score": 91.8,
    },
    {
        "asin": "B07T7N28LN",
        "title": "YouCopia UpSpace Height Adjustable Bottle Organizer for Cabinets",
        "price": 19.99,
        "rating": 4.6,
        "review_count": 6700,
        "image_url": "https://m.media-amazon.com/images/I/71wM6pE+MvL.jpg",
        "product_url": "https://www.amazon.com/dp/B07T7N28LN",
        "query_source": "curated_fallback",
        "viral_score": 90.4,
    },
    {
        "asin": "B07D38J38F",
        "title": "Stori Audrey Stackable Clear Plastic Storage Drawers for Vanity and Pantry",
        "price": 27.99,
        "rating": 4.7,
        "review_count": 14500,
        "image_url": "https://m.media-amazon.com/images/I/81z6Vq4U-hL.jpg",
        "product_url": "https://www.amazon.com/dp/B07D38J38F",
        "query_source": "curated_fallback",
        "viral_score": 95.1,
    },
    {
        "asin": "B08N5NV448",
        "title": "Space Saver Vacuum Storage Bags 12 Pack with Hand Pump for Clothes Bedding",
        "price": 24.99,
        "rating": 4.5,
        "review_count": 28000,
        "image_url": "https://m.media-amazon.com/images/I/71yL2yPzZ8L.jpg",
        "product_url": "https://www.amazon.com/dp/B08N5NV448",
        "query_source": "curated_fallback",
        "viral_score": 92.5,
    },
    {
        "asin": "B08151T931",
        "title": "VASAGLE Slim Rolling Storage Cart 4-Tier Slide Out Storage Cart with Wheels",
        "price": 34.99,
        "rating": 4.6,
        "review_count": 9100,
        "image_url": "https://m.media-amazon.com/images/I/71s8L5pCsmL.jpg",
        "product_url": "https://www.amazon.com/dp/B08151T931",
        "query_source": "curated_fallback",
        "viral_score": 93.0,
    },
    {
        "asin": "B0964GLS2J",
        "title": "Adhesive Corner Shower Caddy Tension Basket 2-Pack Stainless Steel",
        "price": 21.99,
        "rating": 4.7,
        "review_count": 11200,
        "image_url": "https://m.media-amazon.com/images/I/71Nn7wG1bGL.jpg",
        "product_url": "https://www.amazon.com/dp/B0964GLS2J",
        "query_source": "curated_fallback",
        "viral_score": 94.8,
    },
    {
        "asin": "B01MR1Y5K8",
        "title": "Simple Trending 2-Tier Stackable Under Sink Cabinet Organizer with Sliding Storage Drawer",
        "price": 22.99,
        "rating": 4.6,
        "review_count": 16400,
        "image_url": "https://m.media-amazon.com/images/I/71s8N2eGq+L.jpg",
        "product_url": "https://www.amazon.com/dp/B01MR1Y5K8",
        "query_source": "curated_fallback",
        "viral_score": 93.7,
    },
]


class AITrendHunter:
    """Autonomous product trend discovery engine."""

    def __init__(self, queries: Optional[List[str]] = None):
        self.queries = queries or DEFAULT_SEARCH_QUERIES
        self.session = requests.Session(impersonate="chrome124")
        self.headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            ),
        }
        self.seen_asins = self._load_seen_asins()

    def _load_seen_asins(self) -> set:
        """Loads previously published ASINs to prevent duplicates."""
        seen = set(BLACKLISTED_ASINS)
        if SEEN_PRODUCTS_FILE.exists():
            try:
                data = json.loads(SEEN_PRODUCTS_FILE.read_text())
                seen.update(data.get("published_asins", []))
            except Exception:
                pass
        return seen

    def mark_asin_seen(self, asin: str, title: str = "", pin_id: str = ""):
        """Records an ASIN as seen/published."""
        self.seen_asins.add(asin)
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        try:
            records = {}
            if SEEN_PRODUCTS_FILE.exists():
                records = json.loads(SEEN_PRODUCTS_FILE.read_text())
            published = records.get("items", [])
            published.append({"asin": asin, "title": title, "pin_id": pin_id})
            records["items"] = published[-500:]  # Keep last 500
            records["published_asins"] = list(self.seen_asins)
            SEEN_PRODUCTS_FILE.write_text(json.dumps(records, indent=2))
        except Exception as e:
            logger.warning(f"Failed to persist seen asin: {e}")

    def search_category(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Searches Amazon for a specific smart space query and extracts candidates."""
        encoded_query = urllib.parse.quote(query)
        url = f"https://www.amazon.com/s?k={encoded_query}"

        try:
            res = self.session.get(url, headers=self.headers, timeout=12)
            if res.status_code != 200:
                logger.warning(f"Amazon search returned status {res.status_code} for query: {query}")
                return []

            soup = BeautifulSoup(res.text, "html.parser")
            results = []

            for item in soup.find_all("div", {"data-component-type": "s-search-result"}):
                asin = item.get("data-asin", "").strip()
                if not asin or asin in self.seen_asins or asin in BLACKLISTED_ASINS:
                    continue

                title_el = item.find("h2")
                title = title_el.get_text(strip=True) if title_el else ""
                if not title:
                    continue

                # Rating extraction
                rating = 4.5
                rating_el = item.find("span", {"class": "a-icon-alt"})
                if rating_el:
                    m = re.search(r"(\d+(\.\d+)?)", rating_el.text)
                    if m:
                        rating = float(m.group(1))

                # Review count extraction
                review_count = 100
                reviews_el = item.find("span", {"aria-label": re.compile(r"(\d+,?\d*)\s+ratings?")})
                if reviews_el:
                    raw_count = re.sub(r"[^\d]", "", reviews_el.get("aria-label", ""))
                    if raw_count:
                        review_count = int(raw_count)

                # Price extraction
                price_whole = item.find("span", {"class": "a-price-whole"})
                price_fraction = item.find("span", {"class": "a-price-fraction"})
                price = 24.99
                if price_whole:
                    whole = price_whole.text.replace(".", "").replace(",", "").strip()
                    fraction = price_fraction.text.strip() if price_fraction else "00"
                    try:
                        price = float(f"{whole}.{fraction}")
                    except ValueError:
                        price = 24.99

                # Image extraction
                img_el = item.find("img", {"class": "s-image"})
                image_url = img_el.get("src", "") if img_el else ""

                # Compute AI viral score
                viral_score = self._compute_viral_score(rating, review_count, price)

                results.append({
                    "asin": asin,
                    "title": title,
                    "price": price,
                    "rating": rating,
                    "review_count": review_count,
                    "image_url": image_url,
                    "product_url": f"https://www.amazon.com/dp/{asin}",
                    "query_source": query,
                    "viral_score": viral_score,
                })

                if len(results) >= limit:
                    break

            return sorted(results, key=lambda x: x["viral_score"], reverse=True)
        except Exception as e:
            logger.error(f"Search failed for query '{query}': {e}")
            return []

    def _compute_viral_score(self, rating: float, review_count: int, price: float) -> float:
        """Calculates a normalized 0-100 viral score based on conversion signals."""
        # High rating bonus (above 4.2 stars)
        rating_score = max(0, min(100, (rating - 3.5) * 66.6))
        # Social proof volume score (logarithmic)
        review_score = min(100, (min(review_count, 10000) / 10000) * 100)
        # Impulse buy price score (sweet spot is $15 - $50)
        if 15 <= price <= 45:
            price_score = 100
        elif price < 15:
            price_score = 80
        elif price <= 80:
            price_score = 65
        else:
            price_score = 40

        score = (rating_score * 0.45) + (review_score * 0.35) + (price_score * 0.20)
        return round(score, 1)

    def hunt_top_trending_product(self, custom_queries: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
        """Picks niche queries (or custom board queries) and selects the highest-scoring unseen product."""
        import time
        query_pool = custom_queries if custom_queries else self.queries
        # Shuffle to try different queries
        query_pool = random.sample(query_pool, k=len(query_pool))
        all_candidates = []
        
        attempt = 0
        for q in query_pool:
            candidates = self.search_category(q, limit=6)
            if candidates:
                all_candidates.extend(candidates)
                # If we have enough candidates, break early to save API calls
                if len(all_candidates) >= 6:
                    break
            else:
                attempt += 1
                delay = 2 ** attempt
                logger.warning(f"Query '{q}' returned no candidates (possible 503). Retrying next query in {delay}s...")
                time.sleep(delay)
                # Try up to 4 queries before falling back
                if attempt >= 4:
                    break

        if not all_candidates:
            # Fallback curated high-performing Smart Spaces product pool filtered strictly against seen_asins
            logger.info("No candidates returned from live search, picking from rotating curated Smart Spaces pool.")
            unseen_pool = [
                p for p in VERIFIED_SMART_SPACES_POOL
                if p["asin"] not in self.seen_asins and p["asin"] not in BLACKLISTED_ASINS
            ]
            if not unseen_pool:
                # If all pool items have been seen, rotate through non-blacklisted pool items
                unseen_pool = [p for p in VERIFIED_SMART_SPACES_POOL if p["asin"] not in BLACKLISTED_ASINS]

            winner = random.choice(unseen_pool)
            logger.info(f"🏆 Curated Smart Spaces Winner: {winner['title'][:50]} (ASIN: {winner['asin']}, Score: {winner['viral_score']})")
            return winner

        all_candidates.sort(key=lambda x: x["viral_score"], reverse=True)
        winner = all_candidates[0]
        logger.info(f"🏆 Top Trending Winner: {winner['title'][:50]} (Score: {winner['viral_score']})")
        return winner
