"""
eBay scraper for product data extraction
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

logger = logging.getLogger(__name__)


class EbayScraper:
    def __init__(self):
        self.base_url = "https://www.ebay.com"
        self.search_url = "https://www.ebay.com/sch/i.html"
        self.ua = UserAgent()
        self.session = None
        self.rate_limit_delay = 1.0  # seconds between requests

    async def __aenter__(self):
        """Async context manager entry"""
        connector = aiohttp.TCPConnector(limit=10, limit_per_host=5)
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={'User-Agent': self.ua.random}
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
        condition: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for products on eBay
        
        Args:
            query: Search query
            max_results: Maximum number of results to return
            category: Product category filter
            min_price: Minimum price filter
            max_price: Maximum price filter
            condition: Condition filter (new, used, etc.)
        
        Returns:
            List of product dictionaries
        """
        try:
            # Build search parameters
            params = {
                '_nkw': query,
                '_sacat': 0,  # All categories
                '_ipg': min(max_results, 100),  # Results per page
                'LH_Sold': '1',  # Include sold items for pricing data
                'LH_Complete': '1'  # Include completed listings
            }

            if category:
                params['_sacat'] = category
            
            if min_price is not None:
                params['_udlo'] = min_price
            
            if max_price is not None:
                params['_udhi'] = max_price
            
            if condition:
                condition_map = {
                    'new': '1000',
                    'used': '3000',
                    'like_new': '2750',
                    'good': '4000',
                    'acceptable': '5000'
                }
                if condition.lower() in condition_map:
                    params['LH_ItemCondition'] = condition_map[condition.lower()]

            # Make request
            await self._rate_limit()
            async with self.session.get(self.search_url, params=params) as response:
                response.raise_for_status()
                html = await response.text()

            # Parse results
            soup = bs4.BeautifulSoup(html, 'html.parser')
            products = []

            # Find product items
            items = soup.find_all('div', {'class': 's-item__wrapper'})
            
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
            logger.error(f"Error searching eBay products: {e}")
            return []

    async def get_product_details(self, product_url: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information for a specific product
        
        Args:
            product_url: eBay product URL
        
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
            # Title
            title_elem = item_element.find('h3', {'class': 's-item__title'})
            title = title_elem.get_text(strip=True) if title_elem else "No title"
            
            # Skip placeholder items
            if title == "Shop on eBay":
                return None

            # URL
            link_elem = item_element.find('a', {'class': 's-item__link'})
            url = urljoin(self.base_url, link_elem['href']) if link_elem else None

            # Price
            price_elem = item_element.find('span', {'class': 's-item__price'})
            price_text = price_elem.get_text(strip=True) if price_elem else "0"
            price = self._parse_price(price_text)

            # Image URL
            img_elem = item_element.find('img', {'class': 's-item__image-img'})
            image_url = img_elem.get('src') if img_elem else None

            # Condition
            condition_elem = item_element.find('span', {'class': 'SECONDARY_INFO'})
            condition = condition_elem.get_text(strip=True) if condition_elem else None

            # Seller info
            seller_elem = item_element.find('span', {'class': 's-item__seller-info-text'})
            seller = seller_elem.get_text(strip=True) if seller_elem else None

            # Shipping info
            shipping_elem = item_element.find('span', {'class': 's-item__shipping'})
            shipping = shipping_elem.get_text(strip=True) if shipping_elem else None

            # Rating and review count
            rating_elem = item_element.find('span', {'class': 'reviews-rating'})
            rating = None
            if rating_elem:
                rating_text = rating_elem.get_text(strip=True)
                rating = self._parse_rating(rating_text)

            review_count_elem = item_element.find('span', {'class': 'reviews-count'})
            review_count = None
            if review_count_elem:
                review_text = review_count_elem.get_text(strip=True)
                review_count = self._parse_review_count(review_text)

            # Item ID
            item_id_elem = item_element.find('div', {'class': 's-item__item'})
            item_id = None
            if item_id_elem and 'data-itemid' in item_id_elem.attrs:
                item_id = item_id_elem['data-itemid']

            return {
                'title': title,
                'url': url,
                'price': price,
                'currency': 'USD',
                'image_url': image_url,
                'condition': condition,
                'seller': seller,
                'shipping': shipping,
                'rating': rating,
                'review_count': review_count,
                'source': 'ebay',
                'source_id': item_id,
                'availability': 'Available' if price > 0 else 'Sold'
            }

        except Exception as e:
            logger.warning(f"Error extracting product data from item: {e}")
            return None

    async def _extract_product_details(self, soup: bs4.BeautifulSoup, url: str) -> Dict[str, Any]:
        """Extract detailed product information from product page"""
        try:
            # Title
            title_elem = soup.find('h1', {'class': 'x-item-title__mainTitle'})
            title = title_elem.get_text(strip=True) if title_elem else "No title"

            # Price
            price_elem = soup.find('div', {'class': 'x-price-primary'})
            price_text = price_elem.get_text(strip=True) if price_elem else "0"
            price = self._parse_price(price_text)

            # Description
            desc_elem = soup.find('div', {'id': 'desc_div'})
            description = desc_elem.get_text(strip=True) if desc_elem else None

            # Images
            images = []
            img_elems = soup.find_all('img', {'class': 'ux-image-carousel-image'})
            for img in img_elems:
                if 'src' in img.attrs:
                    images.append(img['src'])

            # Specifications
            specs = {}
            spec_table = soup.find('div', {'class': 'x-item-spec-table'})
            if spec_table:
                rows = spec_table.find_all('div', {'class': 'ux-layout-section-evo__row'})
                for row in rows:
                    label_elem = row.find('div', {'class': 'ux-labels-values__labels'})
                    value_elem = row.find('div', {'class': 'ux-labels-values__values'})
                    if label_elem and value_elem:
                        label = label_elem.get_text(strip=True).rstrip(':')
                        value = value_elem.get_text(strip=True)
                        specs[label] = value

            # Category
            breadcrumb_elem = soup.find('nav', {'class': 'breadcrumbs'})
            category = None
            if breadcrumb_elem:
                breadcrumb_links = breadcrumb_elem.find_all('a')
                if breadcrumb_links:
                    category = breadcrumb_links[-1].get_text(strip=True)

            # Item ID
            item_id_elem = soup.find('div', {'id': 'descItemNumber'})
            item_id = item_id_elem.get_text(strip=True) if item_id_elem else None

            # Seller information
            seller_elem = soup.find('span', {'class': 'x-sellernametxt'})
            seller = seller_elem.get_text(strip=True) if seller_elem else None

            # Feedback score
            feedback_elem = soup.find('span', {'class': 'x-seller-card-feedback'})
            feedback_score = None
            if feedback_elem:
                feedback_text = feedback_elem.get_text(strip=True)
                try:
                    feedback_score = int(feedback_text.replace(',', ''))
                except ValueError:
                    pass

            return {
                'title': title,
                'url': url,
                'price': price,
                'currency': 'USD',
                'description': description,
                'image_url': images[0] if images else None,
                'all_images': images,
                'category': category,
                'source': 'ebay',
                'source_id': item_id,
                'seller': seller,
                'feedback_score': feedback_score,
                'specifications': specs,
                'availability': 'Available'
            }

        except Exception as e:
            logger.error(f"Error extracting product details: {e}")
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
            # Extract number from rating text (e.g., "4.5 out of 5 stars")
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
            # Extract number from review text (e.g., "1,234 reviews")
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
        Get eBay product categories
        
        Returns:
            List of category dictionaries
        """
        try:
            # eBay categories page
            categories_url = "https://www.ebay.com/b/all-categories/bn_7000259857"
            
            await self._rate_limit()
            async with self.session.get(categories_url) as response:
                response.raise_for_status()
                html = await response.text()

            soup = bs4.BeautifulSoup(html, 'html.parser')
            categories = []

            # Extract category links
            category_links = soup.find_all('a', {'class': 'b-textlink'})
            
            for link in category_links:
                try:
                    name = link.get_text(strip=True)
                    href = link.get('href')
                    
                    if name and href:
                        # Extract category ID from URL if present
                        category_id = None
                        if 'i.html' in href:
                            import re
                            match = re.search(r'_sacat=(\d+)', href)
                            if match:
                                category_id = int(match.group(1))
                        
                        categories.append({
                            'name': name,
                            'url': urljoin(self.base_url, href),
                            'category_id': category_id,
                            'source': 'ebay'
                        })
                except Exception as e:
                    logger.warning(f"Error extracting category: {e}")
                    continue

            return categories

        except Exception as e:
            logger.error(f"Error getting eBay categories: {e}")
            return []
