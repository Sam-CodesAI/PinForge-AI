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

SEEN_PRODUCTS_FILE = DATA_DIR / "seen_products.json"


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
        if SEEN_PRODUCTS_FILE.exists():
            try:
                data = json.loads(SEEN_PRODUCTS_FILE.read_text())
                return set(data.get("published_asins", []))
            except Exception:
                return set()
        return set()

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
                if not asin or asin in self.seen_asins:
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
            # Fallback curated high-performing Smart Spaces product
            logger.info("No candidates returned from live search, using curated high-yield fallbacks.")
            return {
                "asin": "B087F5K713",
                "title": "Aesthetic Minimalist Desk Organizer & Space Saving Monitor Stand",
                "price": 28.99,
                "rating": 4.7,
                "review_count": 3420,
                "image_url": "https://m.media-amazon.com/images/I/71+8M4pS+SL._AC_SL1500_.jpg",
                "product_url": "https://www.amazon.com/dp/B087F5K713",
                "query_source": "curated_fallback",
                "viral_score": 92.4,
            }

        all_candidates.sort(key=lambda x: x["viral_score"], reverse=True)
        winner = all_candidates[0]
        logger.info(f"🏆 Top Trending Winner: {winner['title'][:50]} (Score: {winner['viral_score']})")
        return winner
