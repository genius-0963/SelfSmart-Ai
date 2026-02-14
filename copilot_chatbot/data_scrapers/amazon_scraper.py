"""
Amazon Product Data Scraper

Collects product data from Amazon for training the copilot suggestion system.
"""

import asyncio
import aiohttp
import asyncio
import json
import time
import random
import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from urllib.parse import urljoin, quote
import logging
from bs4 import BeautifulSoup
import re

logger = logging.getLogger(__name__)


@dataclass
class AmazonProduct:
    """Amazon product data structure."""
    
    product_id: str
    title: str
    brand: str
    price: float
    original_price: Optional[float]
    rating: float
    review_count: int
    category: str
    subcategory: str
    description: str
    features: List[str]
    images: List[str]
    availability: str
    prime_eligible: bool
    best_seller_rank: Optional[int]
    url: str
    scraped_at: str


class AmazonScraper:
    """Amazon product data scraper."""
    
    def __init__(self, delay_range: tuple = (1, 3)):
        """
        Initialize Amazon scraper.
        
        Args:
            delay_range: Tuple of (min, max) seconds to delay between requests
        """
        self.base_url = "https://www.amazon.com"
        self.delay_range = delay_range
        self.session = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
    
    async def __aenter__(self):
        """Async context manager entry."""
        # Check for proxy environment variables
        proxy = None
        if os.getenv('HTTP_PROXY') or os.getenv('HTTPS_PROXY'):
            proxy = os.getenv('HTTPS_PROXY') or os.getenv('HTTP_PROXY')
            logger.info(f"Using proxy: {proxy}")
        
        # Configure connector with proxy support
        connector = aiohttp.TCPConnector(
            limit=10, 
            limit_per_host=5,
            ttl_dns_cache=300,
            use_dns_cache=True,
        )
        
        # Increase timeout for better reliability
        timeout = aiohttp.ClientTimeout(
            total=60,  # Increased from 30
            connect=30,
            sock_read=30
        )
        
        # Create session with proxy if available
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers=self.headers,
            trust_env=True  # This enables proxy from environment variables
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def _random_delay(self):
        """Add random delay to avoid rate limiting."""
        delay = random.uniform(*self.delay_range)
        await asyncio.sleep(delay)
    
    async def _get_page(self, url: str) -> Optional[str]:
        """
        Fetch page content.
        
        Args:
            url: URL to fetch
            
        Returns:
            Page HTML content or None if failed
        """
        try:
            await self._random_delay()
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    logger.warning(f"Failed to fetch {url}: {response.status}")
                    return None
                    
        except aiohttp.ClientProxyConnectionError as e:
            logger.error(f"Proxy connection error for {url}: {e}")
            logger.info("Check your proxy settings or try without proxy")
            return None
        except aiohttp.ClientConnectorError as e:
            logger.error(f"Connection error for {url}: {e}")
            logger.info("Network connectivity issue - check internet connection")
            return None
        except aiohttp.ClientSSLError as e:
            logger.error(f"SSL error for {url}: {e}")
            logger.info("SSL certificate issue - may need proxy or different configuration")
            return None
        except asyncio.TimeoutError as e:
            logger.error(f"Timeout error for {url}: {e}")
            logger.info("Request timed out - network may be slow or proxy issue")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching {url}: {e}")
            return None
    
    def _extract_price(self, price_text: str) -> Optional[float]:
        """Extract price from text."""
        if not price_text:
            return None
        
        # Remove currency symbols and convert to float
        price_clean = re.sub(r'[^\d.]', '', price_text)
        try:
            return float(price_clean)
        except ValueError:
            return None
    
    def _extract_rating(self, rating_text: str) -> float:
        """Extract rating from text."""
        if not rating_text:
            return 0.0
        
        # Extract number before "out of"
        match = re.search(r'(\d+\.?\d*)\s*out of', rating_text)
        if match:
            return float(match.group(1))
        return 0.0
    
    def _extract_review_count(self, review_text: str) -> int:
        """Extract review count from text."""
        if not review_text:
            return 0
        
        # Extract number and handle commas
        match = re.search(r'([\d,]+)\s*ratings?', review_text.lower())
        if match:
            return int(match.group(1).replace(',', ''))
        return 0
    
    async def scrape_product_page(self, product_url: str) -> Optional[AmazonProduct]:
        """
        Scrape a single Amazon product page.
        
        Args:
            product_url: URL of the Amazon product page
            
        Returns:
            AmazonProduct object or None if failed
        """
        html = await self._get_page(product_url)
        if not html:
            return None
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extract product ID from URL
            product_id_match = re.search(r'/dp/([A-Z0-9]{10})', product_url)
            product_id = product_id_match.group(1) if product_id_match else ""
            
            # Basic product info
            title = soup.find('span', {'id': 'productTitle'})
            title = title.get_text(strip=True) if title else ""
            
            brand = soup.find('a', {'id': 'bylineInfo'})
            if brand:
                brand_text = brand.get_text(strip=True)
                brand = brand_text.replace('Brand: ', '').replace('Visit the ', '').replace(' Store', '')
            else:
                brand = ""
            
            # Price information
            price_whole = soup.find('span', {'class': 'a-price-whole'})
            price_fraction = soup.find('span', {'class': 'a-price-fraction'})
            if price_whole and price_fraction:
                price = float(f"{price_whole.get_text()}.{price_fraction.get_text()}")
            else:
                price = 0.0
            
            # Original price (if discounted)
            original_price_elem = soup.find('span', {'class': 'a-price a-text-price'})
            original_price = None
            if original_price_elem:
                original_price_text = original_price_elem.get_text(strip=True)
                original_price = self._extract_price(original_price_text)
            
            # Rating and reviews
            rating_elem = soup.find('span', {'class': 'a-icon-alt'})
            rating = self._extract_rating(rating_elem.get_text() if rating_elem else "")
            
            review_count_elem = soup.find('span', {'id': 'acrCustomerReviewText'})
            review_count = self._extract_review_count(
                review_count_elem.get_text() if review_count_elem else ""
            )
            
            # Category breadcrumbs
            breadcrumbs = soup.find('ul', {'class': 'a-unordered-list a-horizontal a-size-small'})
            category_parts = []
            if breadcrumbs:
                for li in breadcrumbs.find_all('li'):
                    link = li.find('a')
                    if link:
                        category_parts.append(link.get_text(strip=True))
            
            category = category_parts[0] if len(category_parts) > 0 else ""
            subcategory = category_parts[1] if len(category_parts) > 1 else ""
            
            # Product description
            description_elem = soup.find('div', {'id': 'productDescription'})
            description = ""
            if description_elem:
                description = description_elem.get_text(strip=True)
            
            # Product features (bullet points)
            features = []
            feature_list = soup.find('div', {'id': 'feature-bullets'})
            if feature_list:
                for li in feature_list.find_all('li'):
                    feature_text = li.get_text(strip=True)
                    if feature_text and not feature_text.startswith('›'):
                        features.append(feature_text)
            
            # Product images
            images = []
            img_container = soup.find('div', {'id': 'altImages'})
            if img_container:
                for img in img_container.find_all('img'):
                    src = img.get('src')
                    if src and 'images-I51' in src:  # Product image pattern
                        images.append(src)
            
            # Availability
            availability = soup.find('div', {'id': 'availability'})
            availability_text = availability.get_text(strip=True) if availability else "Unknown"
            
            # Prime eligibility
            prime_elem = soup.find('i', {'class': 'a-icon-prime'})
            prime_eligible = prime_elem is not None
            
            # Best seller rank
            rank_elem = soup.find('th', string=re.compile(r'Best Sellers Rank'))
            best_seller_rank = None
            if rank_elem:
                rank_td = rank_elem.find_next_sibling('td')
                if rank_td:
                    rank_text = rank_td.get_text(strip=True)
                    # Extract first number from rank text
                    rank_match = re.search(r'#([\d,]+)', rank_text)
                    if rank_match:
                        best_seller_rank = int(rank_match.group(1).replace(',', ''))
            
            product = AmazonProduct(
                product_id=product_id,
                title=title,
                brand=brand,
                price=price,
                original_price=original_price,
                rating=rating,
                review_count=review_count,
                category=category,
                subcategory=subcategory,
                description=description,
                features=features,
                images=images,
                availability=availability_text,
                prime_eligible=prime_eligible,
                best_seller_rank=best_seller_rank,
                url=product_url,
                scraped_at=time.strftime('%Y-%m-%d %H:%M:%S')
            )
            
            logger.info(f"Successfully scraped product: {title[:50]}...")
            return product
            
        except Exception as e:
            logger.error(f"Error parsing product page {product_url}: {e}")
            return None
    
    async def search_products(self, keyword: str, max_pages: int = 5) -> List[str]:
        """
        Search for products and return product URLs.
        
        Args:
            keyword: Search keyword
            max_pages: Maximum number of pages to scrape
            
        Returns:
            List of product URLs
        """
        product_urls = []
        
        for page in range(1, max_pages + 1):
            search_url = f"{self.base_url}/s?k={quote(keyword)}&page={page}"
            
            html = await self._get_page(search_url)
            if not html:
                continue
            
            try:
                soup = BeautifulSoup(html, 'html.parser')
                
                # Find product links
                product_links = soup.find_all('a', {'class': 'a-link-normal s-underline-text s-underline-link-text s-link-style a-text-normal'})
                
                for link in product_links:
                    href = link.get('href')
                    if href and '/dp/' in href:
                        full_url = urljoin(self.base_url, href)
                        if full_url not in product_urls:
                            product_urls.append(full_url)
                
                logger.info(f"Found {len(product_links)} products on page {page}")
                
            except Exception as e:
                logger.error(f"Error parsing search results page {page}: {e}")
        
        return product_urls[:50]  # Limit to 50 products
    
    async def scrape_category_products(self, category: str, max_products: int = 100) -> List[AmazonProduct]:
        """
        Scrape products from a specific category.
        
        Args:
            category: Category name or keyword
            max_products: Maximum number of products to scrape
            
        Returns:
            List of AmazonProduct objects
        """
        logger.info(f"Starting to scrape category: {category}")
        
        # Search for products in category
        product_urls = await self.search_products(category, max_pages=10)
        product_urls = product_urls[:max_products]
        
        logger.info(f"Found {len(product_urls)} products to scrape")
        
        # Scrape individual product pages
        products = []
        semaphore = asyncio.Semaphore(3)  # Limit concurrent requests
        
        async def scrape_with_semaphore(url):
            async with semaphore:
                return await self.scrape_product_page(url)
        
        tasks = [scrape_with_semaphore(url) for url in product_urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, AmazonProduct):
                products.append(result)
            elif isinstance(result, Exception):
                logger.error(f"Error scraping product: {result}")
        
        logger.info(f"Successfully scraped {len(products)} products")
        return products
    
    async def save_products_to_json(self, products: List[AmazonProduct], filename: str):
        """
        Save products to JSON file.
        
        Args:
            products: List of AmazonProduct objects
            filename: Output filename
        """
        products_data = [asdict(product) for product in products]
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(products_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved {len(products)} products to {filename}")


async def main():
    """Example usage of the Amazon scraper."""
    
    # Categories to scrape
    categories = [
        "electronics",
        "home kitchen",
        "beauty personal care",
        "sports outdoors",
        "books"
    ]
    
    async with AmazonScraper() as scraper:
        for category in categories:
            logger.info(f"Scraping category: {category}")
            
            products = await scraper.scrape_category_products(category, max_products=50)
            
            if products:
                filename = f"data/amazon_products_{category.replace(' ', '_')}.json"
                await scraper.save_products_to_json(products, filename)
            else:
                logger.warning(f"No products found for category: {category}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())