"""
Shopify store scraper for product data extraction
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


class ShopifyScraper:
    def __init__(self, store_domain: str = None):
        """
        Initialize Shopify scraper for a specific store
        
        Args:
            store_domain: Shopify store domain (e.g., 'mystore.myshopify.com' or 'mystore.com')
        """
        self.store_domain = store_domain
        self.base_url = f"https://{store_domain}" if store_domain else None
        self.ua = UserAgent()
        self.session = None
        self.rate_limit_delay = 2.0  # seconds between requests

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
        collection: Optional[str] = None,
        product_type: Optional[str] = None,
        vendor: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for products in Shopify store
        
        Args:
            query: Search query
            max_results: Maximum number of results to return
            collection: Collection filter
            product_type: Product type filter
            vendor: Vendor filter
            min_price: Minimum price filter
            max_price: Maximum price filter
        
        Returns:
            List of product dictionaries
        """
        if not self.base_url:
            logger.error("Store domain not specified")
            return []

        try:
            # Build search URL - Shopify uses /search for search and /collections for browsing
            if query:
                search_url = f"{self.base_url}/search"
                params = {
                    'q': query,
                    'type': 'product',
                    'page': 1
                }
            elif collection:
                search_url = f"{self.base_url}/collections/{collection}"
                params = {'page': 1}
            else:
                # Default to all products
                search_url = f"{self.base_url}/collections/all"
                params = {'page': 1}

            # Add filters
            if product_type:
                params['filter.p.product_type'] = product_type
            if vendor:
                params['filter.p.vendor'] = vendor
            if min_price is not None or max_price is not None:
                price_range = []
                if min_price is not None:
                    price_range.append(str(min_price))
                if max_price is not None:
                    price_range.append(str(max_price))
                if price_range:
                    params['filter.v.price'] = f"{price_range[0]}-{price_range[1] if len(price_range) > 1 else ''}"

            # Make request
            await self._rate_limit()
            async with self.session.get(search_url, params=params) as response:
                response.raise_for_status()
                html = await response.text()

            # Parse results
            soup = bs4.BeautifulSoup(html, 'html.parser')
            products = []

            # Look for product items
            items = []
            
            # Try different selectors for product items
            possible_selectors = [
                'div.product-item',
                'div.grid__item',
                'div.product-card',
                '[data-product-card]',
                '.product-item-wrapper',
                '.collection-product'
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
            logger.error(f"Error searching Shopify products: {e}")
            return []

    async def get_product_details(self, product_url: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information for a specific product
        
        Args:
            product_url: Shopify product URL
        
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
            title_elem = (item_element.find('h2', {'class': 'product-item__title'}) or
                         item_element.find('h3', {'class': 'product-card__title'}) or
                         item_element.find('a', {'class': 'product-item__title'}) or
                         item_element.find('h2') or
                         item_element.find('h3'))
            
            title = title_elem.get_text(strip=True) if title_elem else "No title"

            # URL
            link_elem = (item_element.find('a', {'class': 'product-item__title'}) or
                        item_element.find('a', {'class': 'product-card__link'}) or
                        item_element.find('a'))
            
            url = urljoin(self.base_url, link_elem.get('href')) if link_elem and link_elem.get('href') else None

            # Price
            price = 0.0
            price_elem = (item_element.find('span', {'class': 'price'}) or
                         item_element.find('span', {'class': 'product-item__price'}) or
                         item_element.find('span', {'class': 'product-card__price'}))
            
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                price = self._parse_price(price_text)

            # Original price (if on sale)
            original_price = 0.0
            original_price_elem = (item_element.find('span', {'class': 'price--compare-at-price'}) or
                                  item_element.find('s', {'class': 'compare-at-price'}))
            
            if original_price_elem:
                original_price_text = original_price_elem.get_text(strip=True)
                original_price = self._parse_price(original_price_text)

            # Image URL
            img_elem = (item_element.find('img', {'class': 'product-item__image'}) or
                       item_element.find('img', {'class': 'product-card__image'}) or
                       item_element.find('img'))
            
            image_url = img_elem.get('src') or img_elem.get('data-src') if img_elem else None

            # Vendor/Brand
            vendor = None
            vendor_elem = (item_element.find('div', {'class': 'product-item__vendor'}) or
                         item_element.find('span', {'class': 'product-card__vendor'}))
            
            if vendor_elem:
                vendor = vendor_elem.get_text(strip=True)

            # Product type
            product_type = None
            type_elem = (item_element.find('div', {'class': 'product-item__type'}) or
                        item_element.find('span', {'class': 'product-card__type'}))
            
            if type_elem:
                product_type = type_elem.get_text(strip=True)

            # Availability
            availability = "Available"
            availability_elem = (item_element.find('span', {'class': 'sold-out'}) or
                                 item_element.find('div', {'class': 'product-item__sold-out'}))
            
            if availability_elem:
                availability = "Out of Stock"

            # Product ID from data attributes
            product_id = None
            if item_element.get('data-product-id'):
                product_id = item_element.get('data-product-id')

            return {
                'title': title,
                'url': url,
                'price': price,
                'original_price': original_price,
                'currency': 'USD',  # Default, should be extracted from store settings
                'image_url': image_url,
                'vendor': vendor,
                'category': product_type,
                'source': 'shopify',
                'source_id': product_id,
                'store_domain': self.store_domain,
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
                'category': data.get('category', ''),
                'source': 'shopify',
                'source_id': data.get('sku', ''),
                'store_domain': self.store_domain,
                'availability': 'Available' if offers.get('availability') == 'https://schema.org/InStock' else 'Out of Stock'
            }
        except Exception as e:
            logger.error(f"Error extracting from JSON-LD: {e}")
            return {}

    def _extract_from_html(self, soup: bs4.BeautifulSoup, url: str) -> Dict[str, Any]:
        """Extract product data from HTML parsing"""
        try:
            # Title
            title_elem = (soup.find('h1', {'class': 'product__title'}) or
                         soup.find('h1', {'itemprop': 'name'}) or
                         soup.find('h1'))
            
            title = title_elem.get_text(strip=True) if title_elem else "No title"

            # Price
            price = 0.0
            price_elem = (soup.find('span', {'class': 'price'}) or
                         soup.find('span', {'itemprop': 'price'}) or
                         soup.find('span', {'class': 'product__price'}))
            
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                price = self._parse_price(price_text)

            # Description
            desc_elem = (soup.find('div', {'class': 'product__description'}) or
                        soup.find('div', {'itemprop': 'description'}) or
                        soup.find('div', {'id': 'product-description'}))
            
            description = desc_elem.get_text(strip=True) if desc_elem else None

            # Images
            images = []
            img_elems = soup.find_all('img', {'class': 'product__photo'})
            for img in img_elems:
                if 'src' in img.attrs:
                    images.append(img['src'])

            # Brand/Vendor
            brand = None
            brand_elem = (soup.find('span', {'class': 'product__vendor'}) or
                        soup.find('span', {'itemprop': 'brand'}) or
                        soup.find('div', {'class': 'vendor'}))
            
            if brand_elem:
                brand = brand_elem.get_text(strip=True)

            # Product type
            product_type = None
            type_elem = (soup.find('span', {'class': 'product__type'}) or
                        soup.find('span', {'itemprop': 'category'}))
            
            if type_elem:
                product_type = type_elem.get_text(strip=True)

            return {
                'title': title,
                'url': url,
                'price': price,
                'currency': 'USD',
                'description': description,
                'image_url': images[0] if images else None,
                'all_images': images,
                'brand': brand,
                'category': product_type,
                'source': 'shopify',
                'store_domain': self.store_domain,
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

    async def _rate_limit(self):
        """Apply rate limiting between requests"""
        await asyncio.sleep(self.rate_limit_delay + random.uniform(0, 0.5))

    async def get_collections(self) -> List[Dict[str, Any]]:
        """
        Get collections from Shopify store
        
        Returns:
            List of collection dictionaries
        """
        if not self.base_url:
            logger.error("Store domain not specified")
            return []

        try:
            # Try to access collections page
            collections_url = f"{self.base_url}/collections"
            
            await self._rate_limit()
            async with self.session.get(collections_url) as response:
                response.raise_for_status()
                html = await response.text()

            soup = bs4.BeautifulSoup(html, 'html.parser')
            collections = []

            # Extract collection links
            collection_links = soup.find_all('a', href=lambda x: x and '/collections/' in x)
            
            for link in collection_links:
                try:
                    name = link.get_text(strip=True)
                    href = link.get('href')
                    
                    if name and href and not href.endswith('/all'):
                        collections.append({
                            'name': name,
                            'url': urljoin(self.base_url, href),
                            'handle': href.replace('/collections/', ''),
                            'source': 'shopify',
                            'store_domain': self.store_domain
                        })
                except Exception as e:
                    logger.warning(f"Error extracting collection: {e}")
                    continue

            return collections

        except Exception as e:
            logger.error(f"Error getting Shopify collections: {e}")
            return []

    async def get_store_info(self) -> Dict[str, Any]:
        """
        Get general store information
        
        Returns:
            Store information dictionary
        """
        if not self.base_url:
            logger.error("Store domain not specified")
            return {}

        try:
            await self._rate_limit()
            async with self.session.get(self.base_url) as response:
                response.raise_for_status()
                html = await response.text()

            soup = bs4.BeautifulSoup(html, 'html.parser')
            
            # Extract store name from title
            title_elem = soup.find('title')
            store_name = title_elem.get_text(strip=True) if title_elem else "Unknown Store"
            
            # Look for shop info in JSON
            shop_data = None
            json_scripts = soup.find_all('script')
            
            for script in json_scripts:
                if script.string and 'Shopify.shop' in script.string:
                    try:
                        # Extract shop data from JavaScript
                        import re
                        match = re.search(r'Shopify\.shop\s*=\s*"([^"]+)"', script.string)
                        if match:
                            shop_data = {'name': match.group(1)}
                    except Exception:
                        pass

            return {
                'name': shop_data['name'] if shop_data else store_name,
                'domain': self.store_domain,
                'url': self.base_url,
                'platform': 'shopify'
            }

        except Exception as e:
            logger.error(f"Error getting store info: {e}")
            return {}
