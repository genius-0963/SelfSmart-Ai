"""
SmartShelf AI - Integrations Module
External service integrations
"""

from .amazon_scraper import amazon_scraper, ProductData

__all__ = [
    "amazon_scraper",
    "ProductData"
]
