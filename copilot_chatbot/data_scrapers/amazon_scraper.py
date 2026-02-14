"""
Enhanced Amazon Scraper with Anti-Bot Bypass
Includes rotating user agents, rate limiting, and retry logic
"""

import asyncio
import aiohttp
from bs4 import BeautifulSoup
from typing import List, Optional, Dict
import random
import logging
from dataclasses import dataclass
from urllib.parse import quote_plus
import time
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class AmazonProduct:
    """Enhanced Amazon product data structure"""
    title: str
    price: float
    rating: Optional[float]
    reviews_count: Optional[int]
    url: str
    image_url: Optional[str]
    availability: str
    brand: Optional[str] = None
    original_price: Optional[float] = None
    category: Optional[str] = None
    features: List[str] = None
    scraped_at: str = ""
    
    def __post_init__(self):
        if self.features is None:
            self.features = []
        if not self.scraped_at:
            self.scraped_at = time.strftime('%Y-%m-%d %H:%M:%S')


class AmazonScraper:
    """Enhanced Amazon scraper with anti-bot measures"""
    
    # Pool of realistic user agents
    USER_AGENTS = [
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 OPR/106.0.0.0',
        'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0',
    ]
    
    # Accept-Language variations
    ACCEPT_LANGUAGES = [
        'en-US,en;q=0.9',
        'en-GB,en;q=0.9,en-US;q=0.8',
        'en-US,en;q=0.8',
        'en-CA,en;q=0.9,en-US;q=0.8',
        'en-AU,en;q=0.9,en-US;q=0.8',
    ]
    
    def __init__(self, 
                 min_delay: float = 4.0, 
                 max_delay: float = 9.0,
                 max_retries: int = 3,
                 base_url: str = "https://www.amazon.com",
                 proxy_list: Optional[List[str]] = None,
                 rotate_proxies: bool = True):
        """
        Initialize the enhanced scraper with proxy support
        
        Args:
            min_delay: Minimum seconds between requests
            max_delay: Maximum seconds between requests
            max_retries: Maximum retry attempts per request
            base_url: Amazon base URL
            proxy_list: List of proxy URLs (e.g., ["http://proxy1:8080", "http://user:pass@proxy2:8080"])
            rotate_proxies: Whether to rotate proxies for each request
        """
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.max_retries = max_retries
        self.base_url = base_url
        self.session: Optional[aiohttp.ClientSession] = None
        self.last_request_time = 0
        self.rotate_proxies = rotate_proxies
        self.current_proxy_index = 0
        
        # Load proxy list
        self.proxy_list = self._load_proxy_list(proxy_list)
        logger.info(f"Initialized with {len(self.proxy_list)} proxies")
    
    def _load_proxy_list(self, proxy_list: Optional[List[str]]) -> List[str]:
        """Load proxy list from multiple sources"""
        proxies = []
        
        # Add provided proxies
        if proxy_list:
            proxies.extend(proxy_list)
        
        # Load from environment variables
        env_proxies = [
            os.getenv('HTTP_PROXY'),
            os.getenv('HTTPS_PROXY'),
            os.getenv('http_proxy'),
            os.getenv('https_proxy')
        ]
        for proxy in env_proxies:
            if proxy and proxy not in proxies:
                proxies.append(proxy)
        
        # Load from file if exists
        proxy_file = 'proxies.txt'
        if os.path.exists(proxy_file):
            try:
                with open(proxy_file, 'r') as f:
                    file_proxies = [line.strip() for line in f if line.strip() and not line.startswith('#')]
                    proxies.extend(file_proxies)
                logger.info(f"Loaded {len(file_proxies)} proxies from {proxy_file}")
            except Exception as e:
                logger.warning(f"Failed to load proxies from {proxy_file}: {e}")
        
        # Default free proxies for testing (use with caution)
        if not proxies:
            logger.warning("No proxies provided. Using direct connection (may be blocked).")
        
        return proxies
    
    def _get_next_proxy(self) -> Optional[str]:
        """Get next proxy from list with rotation"""
        if not self.proxy_list:
            return None
        
        if not self.rotate_proxies:
            return random.choice(self.proxy_list)
        
        # Round-robin rotation
        proxy = self.proxy_list[self.current_proxy_index]
        self.current_proxy_index = (self.current_proxy_index + 1) % len(self.proxy_list)
        return proxy
        
    def _get_random_headers(self) -> Dict[str, str]:
        """Generate randomized headers to appear more human-like"""
        return {
            'User-Agent': random.choice(self.USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': random.choice(self.ACCEPT_LANGUAGES),
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
            'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': random.choice(['"Windows"', '"macOS"', '"Linux"']),
        }
    
    async def _rate_limit(self):
        """Implement smart rate limiting with random delays"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        # Random delay between min_delay and max_delay
        delay = random.uniform(self.min_delay, self.max_delay)
        
        # If we made a request recently, wait the remaining time
        if time_since_last < delay:
            wait_time = delay - time_since_last
            logger.info(f"Rate limiting: waiting {wait_time:.2f}s")
            await asyncio.sleep(wait_time)
        
        self.last_request_time = time.time()
    
    async def _fetch_with_retry(self, url: str, retry_count: int = 0) -> Optional[str]:
        """
        Fetch URL with exponential backoff retry logic and proxy support
        
        Args:
            url: URL to fetch
            retry_count: Current retry attempt
            
        Returns:
            HTML content or None if failed
        """
        if retry_count >= self.max_retries:
            logger.error(f"Max retries ({self.max_retries}) reached for {url}")
            return None
        
        try:
            # Apply rate limiting
            await self._rate_limit()
            
            # Get proxy for this request
            proxy = self._get_next_proxy()
            
            # Generate fresh headers for each request
            headers = self._get_random_headers()
            
            logger.info(f"Fetching {url} (attempt {retry_count + 1}/{self.max_retries})")
            
            # Configure request with proxy
            request_kwargs = {
                'headers': headers,
                'timeout': 30
            }
            
            if proxy:
                request_kwargs['proxy'] = proxy
            
            async with self.session.get(url, **request_kwargs) as response:
                # Check for successful response
                if response.status == 200:
                    content = await response.text()
                    logger.info(f"✓ Successfully fetched {url}")
                    return content
                
                # Handle specific error codes
                elif response.status == 503:
                    logger.warning(f"Amazon returned 503 (Service Unavailable). Retrying with longer delay...")
                    await asyncio.sleep(random.uniform(10, 15))
                    return await self._fetch_with_retry(url, retry_count + 1)
                
                elif response.status in [429, 403]:
                    logger.warning(f"Rate limited (status {response.status}). Backing off and rotating proxy...")
                    # Exponential backoff: 2^retry_count * base_delay
                    backoff = (2 ** retry_count) * random.uniform(5, 10)
                    await asyncio.sleep(backoff)
                    return await self._fetch_with_retry(url, retry_count + 1)
                
                elif response.status == 407:
                    logger.error(f"Proxy authentication failed")
                    # Try next proxy
                    if self.proxy_list and len(self.proxy_list) > 1:
                        return await self._fetch_with_retry(url, retry_count + 1)
                    return None
                
                elif response.status == 404:
                    logger.error(f"Page not found: {url}")
                    return None
                
                else:
                    logger.warning(f"Unexpected status {response.status} for {url}")
                    # Retry with exponential backoff
                    await asyncio.sleep((2 ** retry_count) * random.uniform(3, 6))
                    return await self._fetch_with_retry(url, retry_count + 1)
                    
        except aiohttp.ClientProxyConnectionError as e:
            logger.error(f"Proxy connection error: {e}")
            if retry_count < self.max_retries - 1:
                await asyncio.sleep(random.uniform(3, 6))
                return await self._fetch_with_retry(url, retry_count + 1)
            return None
            
        except asyncio.TimeoutError:
            logger.warning(f"Timeout fetching {url}. Retrying...")
            await asyncio.sleep(random.uniform(5, 8))
            return await self._fetch_with_retry(url, retry_count + 1)
            
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            if retry_count < self.max_retries - 1:
                await asyncio.sleep(random.uniform(3, 6))
                return await self._fetch_with_retry(url, retry_count + 1)
            return None
    
    async def __aenter__(self):
        """Async context manager entry"""
        # Create session with cookie jar for session persistence
        cookie_jar = aiohttp.CookieJar()
        self.session = aiohttp.ClientSession(cookie_jar=cookie_jar)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def search_products(self, query: str, max_pages: int = 3) -> List[str]:
        """
        Search for products and return product URLs
        
        Args:
            query: Search query
            max_pages: Maximum number of search result pages to scrape
            
        Returns:
            List of product URLs
        """
        product_urls = []
        
        for page in range(1, max_pages + 1):
            search_url = f"{self.base_url}/s?k={quote_plus(query)}&page={page}"
            
            html = await self._fetch_with_retry(search_url)
            if not html:
                logger.warning(f"Failed to fetch search page {page}")
                continue
            
            soup = BeautifulSoup(html, 'html.parser')
            
            # Find product links - multiple selectors for robustness
            product_links = soup.select('h2.s-line-clamp-2 a, div.s-title-instructions-style a, h2 a.a-link-normal')
            
            for link in product_links:
                href = link.get('href')
                if href and '/dp/' in href:
                    # Construct full URL
                    if href.startswith('/'):
                        full_url = f"{self.base_url}{href}"
                    else:
                        full_url = href
                    
                    # Clean URL (remove tracking parameters)
                    clean_url = full_url.split('?')[0] if '?' in full_url else full_url
                    
                    if clean_url not in product_urls:
                        product_urls.append(clean_url)
            
            logger.info(f"Found {len(product_links)} products on page {page}")
        
        logger.info(f"Total unique products found: {len(product_urls)}")
        return product_urls
    
    async def scrape_product_page(self, url: str) -> Optional[AmazonProduct]:
        """
        Scrape product details from a product page
        
        Args:
            url: Product page URL
            
        Returns:
            AmazonProduct object or None if scraping failed
        """
        html = await self._fetch_with_retry(url)
        if not html:
            return None
        
        soup = BeautifulSoup(html, 'html.parser')
        
        try:
            # Extract title - multiple selectors for robustness
            title_elem = soup.select_one('#productTitle, #title')
            title = title_elem.get_text(strip=True) if title_elem else "Unknown Product"
            
            # Extract price - try multiple price selectors
            price = 0.0
            price_selectors = [
                '.a-price .a-offscreen',
                '#priceblock_ourprice',
                '#priceblock_dealprice',
                '.a-price-whole',
                'span.priceToPay .a-offscreen'
            ]
            
            for selector in price_selectors:
                price_elem = soup.select_one(selector)
                if price_elem:
                    price_text = price_elem.get_text(strip=True)
                    # Extract numeric value
                    price_text = price_text.replace('$', '').replace(',', '')
                    try:
                        price = float(price_text)
                        break
                    except ValueError:
                        continue
            
            # Extract rating
            rating = None
            rating_elem = soup.select_one('span.a-icon-alt')
            if rating_elem:
                rating_text = rating_elem.get_text(strip=True)
                try:
                    rating = float(rating_text.split()[0])
                except (ValueError, IndexError):
                    pass
            
            # Extract review count
            reviews_count = None
            reviews_elem = soup.select_one('#acrCustomerReviewText')
            if reviews_elem:
                reviews_text = reviews_elem.get_text(strip=True)
                try:
                    reviews_count = int(reviews_text.replace(',', '').split()[0])
                except (ValueError, IndexError):
                    pass
            
            # Extract image URL
            image_url = None
            image_elem = soup.select_one('#landingImage, #imgBlkFront')
            if image_elem:
                image_url = image_elem.get('src') or image_elem.get('data-old-hires')
            
            # Extract availability
            availability = "Unknown"
            avail_elem = soup.select_one('#availability span')
            if avail_elem:
                availability = avail_elem.get_text(strip=True)
            
            # Extract brand
            brand = None
            brand_elem = soup.select_one('#bylineInfo')
            if brand_elem:
                brand_text = brand_elem.get_text(strip=True)
                brand = brand_text.replace('Brand: ', '').replace('Visit the ', '').replace(' Store', '')
            
            # Extract features
            features = []
            feature_list = soup.select_one('#feature-bullets ul')
            if feature_list:
                for li in feature_list.find_all('li'):
                    feature_text = li.get_text(strip=True)
                    if feature_text and not feature_text.startswith('›'):
                        features.append(feature_text)
            
            product = AmazonProduct(
                title=title,
                price=price,
                rating=rating,
                reviews_count=reviews_count,
                url=url,
                image_url=image_url,
                availability=availability,
                brand=brand,
                features=features
            )
            
            logger.info(f"✓ Scraped product: {title[:50]}... (${price})")
            return product
            
        except Exception as e:
            logger.error(f"Error parsing product page {url}: {e}")
            return None
    
    # Legacy methods for compatibility
    async def scrape_category_products(self, category: str, max_products: int = 100) -> List[AmazonProduct]:
        """
        Scrape products from a specific category (legacy method).
        
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
        import json
        products_data = []
        for product in products:
            product_dict = {
                'title': product.title,
                'price': product.price,
                'rating': product.rating,
                'reviews_count': product.reviews_count,
                'url': product.url,
                'image_url': product.image_url,
                'availability': product.availability,
                'brand': product.brand,
                'features': product.features,
                'scraped_at': product.scraped_at
            }
            products_data.append(product_dict)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(products_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved {len(products)} products to {filename}")


# Example usage and testing
async def test_enhanced_scraper():
    """Test the enhanced scraper with proxy support"""
    print("Testing Enhanced Amazon Scraper with Proxy Support...")
    print("=" * 60)
    
    # Example proxy configurations
    proxy_options = [
        # Option 1: Use environment variables
        # Set HTTP_PROXY=http://your-proxy:port or HTTPS_PROXY=http://your-proxy:port
        
        # Option 2: Use proxy list
        # ["http://proxy1:8080", "http://proxy2:8080", "socks5://proxy3:1080"]
        
        # Option 3: Load from proxies.txt file (automatically loaded)
        None  # Will load from proxies.txt if it exists
    ]
    
    async with AmazonScraper(
        min_delay=5, 
        max_delay=8, 
        max_retries=3,
        proxy_list=proxy_options[0],
        rotate_proxies=True
    ) as scraper:
        
        # Show proxy status
        if scraper.proxy_list:
            print(f"✓ Using {len(scraper.proxy_list)} proxies with rotation")
        else:
            print("⚠ No proxies configured - using direct connection")
        
        # Test search
        print("\n1. Testing product search...")
        query = "wireless mouse"
        urls = await scraper.search_products(query, max_pages=1)
        
        if urls:
            print(f"✓ Found {len(urls)} product URLs")
            print(f"Sample URLs:")
            for url in urls[:3]:
                print(f"  - {url}")
            
            # Test product scraping
            print(f"\n2. Testing product detail scraping...")
            product = await scraper.scrape_product_page(urls[0])
            
            if product:
                print(f"\n✓ Successfully scraped product:")
                print(f"  Title: {product.title}")
                print(f"  Price: ${product.price}")
                print(f"  Rating: {product.rating} stars")
                print(f"  Reviews: {product.reviews_count}")
                print(f"  Availability: {product.availability}")
                print(f"\n✅ SCRAPER IS WORKING!")
                return True
            else:
                print("✗ Failed to scrape product details")
                return False
        else:
            print("✗ No product URLs found")
            return False


async def test_proxy_only():
    """Test proxy connectivity only"""
    print("Testing Proxy Connectivity...")
    print("=" * 40)
    
    # Test with a simple HTTP request to verify proxy works
    test_proxies = [
        # Add your proxies here or set environment variables
        # "http://your-proxy:8080"
    ]
    
    async with AmazonScraper(proxy_list=test_proxies) as scraper:
        if not scraper.proxy_list:
            print("⚠ No proxies configured")
            return False
        
        print(f"Testing {len(scraper.proxy_list)} proxies...")
        
        for i, proxy in enumerate(scraper.proxy_list):
            print(f"\nTesting proxy {i+1}: {proxy}")
            try:
                # Simple test request
                headers = scraper._get_random_headers()
                timeout = aiohttp.ClientTimeout(total=10)
                
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.get('https://httpbin.org/ip', proxy=proxy, headers=headers) as response:
                        if response.status == 200:
                            data = await response.json()
                            print(f"✓ Proxy works! IP: {data.get('origin', 'Unknown')}")
                        else:
                            print(f"✗ Proxy failed with status {response.status}")
            except Exception as e:
                print(f"✗ Proxy error: {e}")
        
        return True


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
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--test-proxy":
        # Test proxy connectivity only
        result = asyncio.run(test_proxy_only())
    else:
        # Run the full scraper test
        result = asyncio.run(test_enhanced_scraper())
    
    print(f"\n{'='*60}")
    print(f"Final Result: {'✅ SUCCESS' if result else '❌ FAILED'}")
