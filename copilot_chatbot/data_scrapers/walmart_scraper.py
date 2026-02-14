"""
Walmart scraper for product data extraction
"""

import asyncio
import aiohttp
import bs4
from typing import List, Dict, Optional, Any
from urllib.parse import urljoin, quote
import logging
from fake_useragent import UserAgent
import time
import random
import json

logger = logging.getLogger(__name__)


class WalmartScraper:
    def __init__(self):
        self.base_url = "https://www.walmart.com"
        self.search_url = "https://www.walmart.com/search"
        self.ua = UserAgent()
        self.session = None
        self.rate_limit_delay = 1.5  # seconds between requests

    async def __aenter__(self):
        """Async context manager entry"""
        connector = aiohttp.TCPConnector(limit=10, limit_per_host=5)
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={
                'User-Agent': self.ua.random,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    async def search_products(
        self,
        query: str,
        max_results: int = 50,
        category: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        sort_by: str = "relevance"
    ) -> List[Dict[str, Any]]:
        """
        Search for products on Walmart
        
        Args:
            query: Search query
            max_results: Maximum number of results to return
            category: Product category filter
            min_price: Minimum price filter
            max_price: Maximum price filter
            sort_by: Sort order (relevance, price_low, price_high, rating, new)
        
        Returns:
            List of product dictionaries
        """
        try:
            # Build search parameters
            params = {
                'q': query,
                'page': 1,
                'ps': min(max_results, 40),  # Results per page
                'sort': sort_by
            }

            # Add price filters
            if min_price is not None or max_price is not None:
                price_range = []
                if min_price is not None:
                    price_range.append(f"{min_price}")
                if max_price is not None:
                    price_range.append(f"{max_price}")
                if price_range:
                    params['price'] = f"{price_range[0]}-{price_range[1] if len(price_range) > 1 else ''}"

            # Make request
            await self._rate_limit()
            async with self.session.get(self.search_url, params=params) as response:
                response.raise_for_status()
                html = await response.text()

            # Parse results
            soup = bs4.BeautifulSoup(html, 'html.parser')
            products = []

            # Look for product items in different possible containers
            items = []
            
            # Try different selectors for product items
            possible_selectors = [
                'div[data-item-id]',  # New Walmart layout
                'div[data-testid="search-result-product-card"]',
                'div.w-25',  # Older layout
                'div.search-result-gridview-item',
                '[data-testid="product-card"]'
            ]
            
            for selector in possible_selectors:
                items = soup.select(selector)
                if items:
                    break

            for item in items[:max_results]:
                try:
                    product = await self._extract_product_data(item)
                    if product:
                        products.append(product)
                except Exception as e:
                    logger.warning(f"Error extracting product data: {e}")
                    continue

            return products

        except Exception as e:
            logger.error(f"Error searching Walmart products: {e}")
            return []

    async def get_product_details(self, product_url: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information for a specific product
        
        Args:
            product_url: Walmart product URL
        
        Returns:
            Product details dictionary or None if error
        """
        try:
            await self._rate_limit()
            async with self.session.get(product_url) as response:
                response.raise_for_status()
                html = await response.text()

            soup = bs4.BeautifulSoup(html, 'html.parser')
            return await self._extract_product_details(soup, product_url)

        except Exception as e:
            logger.error(f"Error getting product details from {product_url}: {e}")
            return None

    async def _extract_product_data(self, item_element) -> Optional[Dict[str, Any]]:
        """Extract product data from search result item"""
        try:
            # Product ID
            item_id = item_element.get('data-item-id')
            
            # Title
            title_elem = (item_element.find('span', {'data-automation-id': 'product-title'}) or
                         item_element.find('a', {'class': 'product-title-link'}) or
                         item_element.find('h2') or
                         item_element.find('span', {'class': 'f6'}))
            
            title = title_elem.get_text(strip=True) if title_elem else "No title"

            # URL
            link_elem = (item_element.find('a', {'data-automation-id': 'product-title'}) or
                        item_element.find('a', {'class': 'product-title-link'}) or
                        item_element.find('a'))
            
            url = urljoin(self.base_url, link_elem.get('href')) if link_elem and link_elem.get('href') else None

            # Price
            price = 0.0
            price_elem = (item_element.find('div', {'data-automation-id': 'product-price'}) or
                         item_element.find('span', {'class': 'price-current'}) or
                         item_element.find('span', {'data-automation-id': 'product-price'}))
            
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                price = self._parse_price(price_text)

            # Original price (if on sale)
            original_price = 0.0
            original_price_elem = (item_element.find('span', {'class': 'price-original'}) or
                                  item_element.find('div', {'data-automation-id': 'product-original-price'}))
            
            if original_price_elem:
                original_price_text = original_price_elem.get_text(strip=True)
                original_price = self._parse_price(original_price_text)

            # Image URL
            img_elem = (item_element.find('img', {'data-automation-id': 'product-image'}) or
                       item_element.find('img', {'class': 'product-image'}) or
                       item_element.find('img'))
            
            image_url = img_elem.get('src') or img_elem.get('data-src') if img_elem else None

            # Rating
            rating = None
            rating_elem = (item_element.find('span', {'class': 'rating-number'}) or
                          item_element.find('span', {'data-automation-id': 'rating'}))
            
            if rating_elem:
                rating_text = rating_elem.get_text(strip=True)
                rating = self._parse_rating(rating_text)

            # Review count
            review_count = None
            review_elem = (item_element.find('span', {'class': 'rating-count'}) or
                          item_element.find('span', {'data-automation-id': 'rating-count'}))
            
            if review_elem:
                review_text = review_elem.get_text(strip=True)
                review_count = self._parse_review_count(review_text)

            # Brand
            brand = None
            brand_elem = (item_element.find('span', {'data-automation-id': 'product-brand'}) or
                        item_element.find('div', {'class': 'brand'}))
            
            if brand_elem:
                brand = brand_elem.get_text(strip=True)

            # Availability
            availability = "Available"
            availability_elem = (item_element.find('div', {'data-automation-id': 'availability'}) or
                                 item_element.find('span', {'class': 'availability'}))
            
            if availability_elem:
                availability_text = availability_elem.get_text(strip=True).lower()
                if 'out of stock' in availability_text or 'unavailable' in availability_text:
                    availability = "Out of Stock"

            return {
                'title': title,
                'url': url,
                'price': price,
                'original_price': original_price,
                'currency': 'USD',
                'image_url': image_url,
                'brand': brand,
                'rating': rating,
                'review_count': review_count,
                'source': 'walmart',
                'source_id': item_id,
                'availability': availability,
                'discount_percentage': round(((original_price - price) / original_price * 100), 1) if original_price > price > 0 else 0
            }

        except Exception as e:
            logger.warning(f"Error extracting product data from item: {e}")
            return None

    async def _extract_product_details(self, soup: bs4.BeautifulSoup, url: str) -> Dict[str, Any]:
        """Extract detailed product information from product page"""
        try:
            # Look for JSON-LD structured data
            json_ld_data = None
            json_scripts = soup.find_all('script', type='application/ld+json')
            
            for script in json_scripts:
                try:
                    data = json.loads(script.string)
                    if isinstance(data, dict) and data.get('@type') == 'Product':
                        json_ld_data = data
                        break
                except (json.JSONDecodeError, AttributeError):
                    continue

            # Extract from JSON-LD if available
            if json_ld_data:
                return self._extract_from_json_ld(json_ld_data, url)

            # Fallback to HTML parsing
            return self._extract_from_html(soup, url)

        except Exception as e:
            logger.error(f"Error extracting product details: {e}")
            return {}

    def _extract_from_json_ld(self, data: Dict, url: str) -> Dict[str, Any]:
        """Extract product data from JSON-LD structured data"""
        try:
            offers = data.get('offers', {})
            if isinstance(offers, list):
                offers = offers[0] if offers else {}

            return {
                'title': data.get('name', 'No title'),
                'url': url,
                'price': self._parse_price(str(offers.get('price', '0'))),
                'currency': offers.get('priceCurrency', 'USD'),
                'description': data.get('description', ''),
                'image_url': data.get('image', [None])[0] if isinstance(data.get('image'), list) else data.get('image'),
                'brand': data.get('brand', {}).get('name') if isinstance(data.get('brand'), dict) else data.get('brand'),
                'rating': float(data.get('aggregateRating', {}).get('ratingValue', 0)) if data.get('aggregateRating') else None,
                'review_count': int(data.get('aggregateRating', {}).get('reviewCount', 0)) if data.get('aggregateRating') else None,
                'category': data.get('category', ''),
                'source': 'walmart',
                'source_id': data.get('sku', ''),
                'availability': 'Available' if offers.get('availability') == 'https://schema.org/InStock' else 'Out of Stock'
            }
        except Exception as e:
            logger.error(f"Error extracting from JSON-LD: {e}")
            return {}

    def _extract_from_html(self, soup: bs4.BeautifulSoup, url: str) -> Dict[str, Any]:
        """Extract product data from HTML parsing"""
        try:
            # Title
            title_elem = (soup.find('h1', {'data-automation-id': 'product-title'}) or
                         soup.find('h1', {'class': 'product-title'}) or
                         soup.find('h1'))
            
            title = title_elem.get_text(strip=True) if title_elem else "No title"

            # Price
            price = 0.0
            price_elem = (soup.find('span', {'data-automation-id': 'product-price'}) or
                         soup.find('span', {'class': 'price-current'}))
            
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                price = self._parse_price(price_text)

            # Description
            desc_elem = (soup.find('div', {'data-automation-id': 'product-description'}) or
                        soup.find('div', {'class': 'product-description'}) or
                        soup.find('div', {'id': 'product-description'}))
            
            description = desc_elem.get_text(strip=True) if desc_elem else None

            # Images
            images = []
            img_elems = soup.find_all('img', {'class': 'product-image'})
            for img in img_elems:
                if 'src' in img.attrs:
                    images.append(img['src'])

            # Brand
            brand = None
            brand_elem = (soup.find('span', {'data-automation-id': 'product-brand'}) or
                        soup.find('div', {'class': 'brand'}))
            
            if brand_elem:
                brand = brand_elem.get_text(strip=True)

            # Category
            category = None
            breadcrumb_elem = soup.find('nav', {'aria-label': 'breadcrumb'})
            if breadcrumb_elem:
                breadcrumb_links = breadcrumb_elem.find_all('a')
                if breadcrumb_links:
                    category = breadcrumb_links[-1].get_text(strip=True)

            return {
                'title': title,
                'url': url,
                'price': price,
                'currency': 'USD',
                'description': description,
                'image_url': images[0] if images else None,
                'all_images': images,
                'brand': brand,
                'category': category,
                'source': 'walmart',
                'availability': 'Available'
            }

        except Exception as e:
            logger.error(f"Error extracting from HTML: {e}")
            return {}

    def _parse_price(self, price_text: str) -> float:
        """Parse price text to float"""
        try:
            # Remove currency symbols and whitespace
            clean_price = price_text.replace('$', '').replace(',', '').strip()
            
            # Handle price ranges (take the lower bound)
            if ' to ' in clean_price.lower():
                clean_price = clean_price.lower().split(' to ')[0]
            
            # Convert to float
            return float(clean_price)
        except (ValueError, AttributeError):
            return 0.0

    def _parse_rating(self, rating_text: str) -> Optional[float]:
        """Parse rating text to float"""
        try:
            # Extract number from rating text
            import re
            match = re.search(r'(\d+\.?\d*)', rating_text)
            if match:
                return float(match.group(1))
        except (ValueError, AttributeError):
            pass
        return None

    def _parse_review_count(self, review_text: str) -> Optional[int]:
        """Parse review count text to integer"""
        try:
            # Extract number from review text
            import re
            match = re.search(r'(\d+,?\d*)', review_text.replace(',', ''))
            if match:
                return int(match.group(1))
        except (ValueError, AttributeError):
            pass
        return None

    async def _rate_limit(self):
        """Apply rate limiting between requests"""
        await asyncio.sleep(self.rate_limit_delay + random.uniform(0, 0.5))

    async def get_categories(self) -> List[Dict[str, Any]]:
        """
        Get Walmart product categories
        
        Returns:
            List of category dictionaries
        """
        try:
            # Walmart categories page
            categories_url = "https://www.walmart.com/browse/all"
            
            await self._rate_limit()
            async with self.session.get(categories_url) as response:
                response.raise_for_status()
                html = await response.text()

            soup = bs4.BeautifulSoup(html, 'html.parser')
            categories = []

            # Extract category links
            category_links = soup.find_all('a', {'class': 'category-link'})
            
            for link in category_links:
                try:
                    name = link.get_text(strip=True)
                    href = link.get('href')
                    
                    if name and href:
                        categories.append({
                            'name': name,
                            'url': urljoin(self.base_url, href),
                            'source': 'walmart'
                        })
                except Exception as e:
                    logger.warning(f"Error extracting category: {e}")
                    continue

            return categories

        except Exception as e:
            logger.error(f"Error getting Walmart categories: {e}")
            return []
