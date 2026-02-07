"""\
SmartShelf AI - Competitor Intelligence API v1

Best-effort competitor scraping (demo) + persistence into competitor_prices.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
import re

import requests

from ...database import get_db
from ...database import Product, CompetitorPrice
from ...core.exceptions import ValidationError, NotFoundError

logger = logging.getLogger(__name__)
router = APIRouter()


def _extract_price(text: str) -> Optional[float]:
    if not text:
        return None
    # match $12.34 or 12.34
    m = re.search(r"\$\s*(\d+(?:\.\d{1,2})?)", text)
    if m:
        return float(m.group(1))
    m = re.search(r"\b(\d+(?:\.\d{1,2})?)\b", text)
    if m:
        return float(m.group(1))
    return None


def _scrape_competitor_page(url: str) -> Dict[str, Any]:
    """Very lightweight scraping with regex heuristics (demo)."""
    r = requests.get(url, timeout=15, headers={"User-Agent": "SmartShelfAI/1.0"})
    r.raise_for_status()
    html = r.text

    # naive title
    title_match = re.search(r"<title>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
    title = title_match.group(1).strip() if title_match else None

    # naive price search near common patterns
    price = None
    for pat in [r"\$\s*\d+(?:\.\d{2})?", r"price\s*[:=]\s*\$?\s*\d+(?:\.\d{2})?"]:
        m = re.search(pat, html, re.IGNORECASE)
        if m:
            price = _extract_price(m.group(0))
            if price is not None:
                break

    return {"title": title, "price": price}


@router.post("/scrape", response_model=Dict[str, Any])
async def scrape_and_store_competitor_price(
    product_id: int,
    competitor: str,
    url: str,
    db: Session = Depends(get_db),
):
    """Scrape a competitor product page, extract price, and store in competitor_prices."""
    if not competitor.strip():
        raise ValidationError("competitor is required")
    if not url.startswith("http"):
        raise ValidationError("url must be http/https")

    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise NotFoundError("Product", product_id)

    scraped = _scrape_competitor_page(url)
    if scraped.get("price") is None:
        raise ValidationError("Could not extract price from page. Provide a different URL or adjust parsing rules.")

    your_price = float(product.base_price)
    competitor_price = float(scraped["price"])
    diff_pct = ((your_price - competitor_price) / competitor_price * 100) if competitor_price else None

    rec = CompetitorPrice(
        product_id=product.id,
        sku=product.sku,
        competitor=competitor.strip(),
        competitor_price=competitor_price,
        price_difference_percent=diff_pct or 0.0,
        in_stock=True,
        last_updated=datetime.utcnow(),
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)

    return {
        "product_id": product.id,
        "product_name": product.product_name,
        "competitor": competitor.strip(),
        "scraped": scraped,
        "stored": {
            "id": rec.id,
            "competitor_price": rec.competitor_price,
            "price_difference_percent": rec.price_difference_percent,
            "last_updated": rec.last_updated.isoformat(),
        },
    }


@router.get("/summary/{product_id}", response_model=Dict[str, Any])
async def competitor_summary(product_id: int, db: Session = Depends(get_db)):
    """Summarize competitor pricing for a product from stored competitor_prices."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise NotFoundError("Product", product_id)

    cps = db.query(CompetitorPrice).filter(CompetitorPrice.product_id == product_id).order_by(CompetitorPrice.last_updated.desc()).all()
    if not cps:
        return {
            "product_id": product_id,
            "product_name": product.product_name,
            "your_price": float(product.base_price),
            "competitors": [],
            "analysis": "No competitor data available",
        }

    avg = sum(cp.competitor_price for cp in cps) / len(cps)
    position = "above_market" if product.base_price > avg else "below_market"

    return {
        "product_id": product_id,
        "product_name": product.product_name,
        "your_price": float(product.base_price),
        "market_average": float(avg),
        "price_position": position,
        "competitors": [
            {
                "competitor": cp.competitor,
                "competitor_price": float(cp.competitor_price),
                "price_difference_percent": float(cp.price_difference_percent or 0.0),
                "last_updated": cp.last_updated.isoformat(),
            }
            for cp in cps[:10]
        ],
        "generated_at": datetime.utcnow().isoformat(),
    }
