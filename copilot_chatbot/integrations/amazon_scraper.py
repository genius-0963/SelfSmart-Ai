"""
SmartShelf AI - Enhanced Amazon Scraper Service
Production-ready Amazon data integration with caching and rate limiting
"""

import asyncio
import aiohttp
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from urllib.parse import urlencode

from core.config import settings
from services.cache_service import cache_service
from services.metrics_service import metrics_service

logger = logging.getLogger(__name__)

@dataclass
class ProductData:
    """Product data structure with comprehensive fields"""
    asin: str
    title: str
    price: float
    rating: float
    review_count: int
    availability: str
    prime_eligible: bool
    category: str
    url: str
    image_url: str
    features: List[str]
    description: str = ""
    brand: str = ""
    last_updated: datetime = None
    
    def __post_init__(self):
        if self.last_updated is None:
            self.last_updated = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with JSON serialization"""
        data = asdict(self)
        data['last_updated'] = self.last_updated.isoformat()
        return data

class AmazonScraperService:
    """Enhanced Amazon scraper with production features"""
    
    def __init__(self):
        self.api_key = settings.amazon_api_key
        self.api_host = settings.amazon_api_host
        self.session = None
        self.rate_limiter = asyncio.Semaphore(settings.amazon_rate_limit)
        self.cache_ttl = 3600  # 1 hour cache for product data
        self.search_cache_ttl = 1800  # 30 minutes cache for searches
        
        # Statistics
        self.request_count = 0
        self.cache_hits = 0
        self.errors = 0
        
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session with proper configuration"""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=30, connect=10)
            headers = {
                'x-rapidapi-key': self.api_key,
                'x-rapidapi-host': self.api_host,
                'Content-Type': 'application/json',
                'User-Agent': 'SmartShelf-AI/1.0'
            }
            
            self.session = aiohttp.ClientSession(
                timeout=timeout,
                headers=headers,
                connector=aiohttp.TCPConnector(
                    limit=20,
                    limit_per_host=10,
                    ttl_dns_cache=300,
                    use_dns_cache=True,
                )
            )
        
        return self.session
    
    async def search_products(
        self, 
        query: str, 
        country: str = "US",
        page: int = 1,
        category: Optional[str] = None,
        max_results: int = 10
    ) -> List[ProductData]:
        """Search for products with comprehensive caching and error handling"""
        if not self.api_key:
            logger.warning("Amazon API key not configured")
            return []
        
        # Generate cache key
        cache_params = {
            'query': query,
            'country': country,
            'page': page,
            'category': category,
            'max_results': max_results
        }
        cache_key = f"amazon_search:{hash(json.dumps(cache_params, sort_keys=True))}"
        
        # Check cache first
        cached_result = await cache_service.get(cache_key)
        if cached_result:
            self.cache_hits += 1
            logger.info(f"Cache hit for Amazon search: {query}")
            metrics_service.record_product_search(query, len(cached_result))
            return cached_result
        
        # Rate limiting
        async with self.rate_limiter:
            try:
                session = await self._get_session()
                self.request_count += 1
                
                # Build request parameters
                params = {
                    'query': query,
                    'country': country,
                    'page': page
                }
                if category:
                    params['category'] = category
                
                url = f"https://{self.api_host}/search"
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        products = self._parse_search_results(data, max_results)
                        
                        # Cache the results
                        await cache_service.set(cache_key, products, self.search_cache_ttl)
                        
                        # Record metrics
                        metrics_service.record_product_search(query, len(products))
                        
                        logger.info(f"Found {len(products)} products for query: {query}")
                        return products
                        
                    elif response.status == 429:
                        logger.warning("Amazon API rate limit exceeded")
                        await asyncio.sleep(2)  # Backoff
                        return []
                    else:
                        logger.error(f"Amazon API error: {response.status} - {await response.text()}")
                        self.errors += 1
                        return []
                        
            except asyncio.TimeoutError:
                logger.error(f"Timeout searching Amazon products: {query}")
                self.errors += 1
                return []
            except Exception as e:
                logger.error(f"Error searching Amazon products: {e}")
                self.errors += 1
                return []
    
    def _parse_search_results(self, data: Dict, max_results: int) -> List[ProductData]:
        """Parse Amazon API response into ProductData objects"""
        products = []
        
        try:
            for item in data.get('data', {}).get('products', [])[:max_results]:
                try:
                    # Parse price safely
                    price_text = item.get('product_price', '0')
                    price = self._parse_price(price_text)
                    
                    # Parse rating safely
                    rating_text = item.get('product_star_rating', '0')
                    rating = self._parse_rating(rating_text)
                    
                    # Parse review count safely
                    review_count_text = item.get('product_num_reviews', '0')
                    review_count = self._parse_review_count(review_count_text)
                    
                    product = ProductData(
                        asin=item.get('asin', ''),
                        title=item.get('product_title', ''),
                        price=price,
                        rating=rating,
                        review_count=review_count,
                        availability=item.get('product_availability', ''),
                        prime_eligible=item.get('is_prime', False),
                        category=item.get('product_category', ''),
                        url=item.get('product_url', ''),
                        image_url=item.get('product_photo', ''),
                        features=item.get('product_features', []),
                        description=item.get('product_description', ''),
                        brand=item.get('product_brand', '')
                    )
                    
                    products.append(product)
                    
                except (ValueError, KeyError) as e:
                    logger.warning(f"Error parsing product data: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error parsing search results: {e}")
        
        return products
    
    def _parse_price(self, price_text: str) -> float:
        """Parse price from various formats"""
        if not price_text:
            return 0.0
        
        # Remove currency symbols and convert to float
        import re
        price_clean = re.sub(r'[^\d.]', '', price_text)
        try:
            return float(price_clean)
        except ValueError:
            return 0.0
    
    def _parse_rating(self, rating_text: str) -> float:
        """Parse rating from various formats"""
        if not rating_text:
            return 0.0
        
        import re
        rating_match = re.search(r'(\d+\.?\d*)', rating_text)
        if rating_match:
            try:
                return float(rating_match.group(1))
            except ValueError:
                return 0.0
        return 0.0
    
    def _parse_review_count(self, count_text: str) -> int:
        """Parse review count from various formats"""
        if not count_text:
            return 0
        
        import re
        count_match = re.search(r'(\d+)', count_text.replace(',', ''))
        if count_match:
            try:
                return int(count_match.group(1))
            except ValueError:
                return 0
        return 0
    
    async def get_product_details(self, asin: str, country: str = "US") -> Optional[ProductData]:
        """Get detailed product information"""
        if not self.api_key:
            return None
        
        cache_key = f"amazon_product:{asin}:{country}"
        
        # Check cache
        cached_result = await cache_service.get(cache_key)
        if cached_result:
            return cached_result
        
        async with self.rate_limiter:
            try:
                session = await self._get_session()
                self.request_count += 1
                
                params = {'asin': asin, 'country': country}
                url = f"https://{self.api_host}/product-details"
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        product = self._parse_product_details(data)
                        
                        if product:
                            await cache_service.set(cache_key, product, self.cache_ttl)
                        
                        return product
                    else:
                        logger.error(f"Product details API error: {response.status}")
                        self.errors += 1
                        return None
                        
            except Exception as e:
                logger.error(f"Error getting product details: {e}")
                self.errors += 1
                return None
    
    def _parse_product_details(self, data: Dict) -> Optional[ProductData]:
        """Parse product details response"""
        try:
            product_data = data.get('data', {})
            
            return ProductData(
                asin=product_data.get('asin', ''),
                title=product_data.get('product_title', ''),
                price=self._parse_price(product_data.get('product_price', '')),
                rating=self._parse_rating(product_data.get('product_star_rating', '')),
                review_count=self._parse_review_count(product_data.get('product_num_reviews', '')),
                availability=product_data.get('product_availability', ''),
                prime_eligible=product_data.get('is_prime', False),
                category=product_data.get('product_category', ''),
                url=product_data.get('product_url', ''),
                image_url=product_data.get('product_photo', ''),
                features=product_data.get('product_features', []),
                description=product_data.get('product_description', ''),
                brand=product_data.get('product_brand', '')
            )
            
        except Exception as e:
            logger.warning(f"Error parsing product details: {e}")
            return None
    
    async def get_product_reviews(self, asin: str, country: str = "US", limit: int = 10) -> List[Dict]:
        """Get product reviews for sentiment analysis"""
        if not self.api_key:
            return []
        
        cache_key = f"amazon_reviews:{asin}:{country}:{limit}"
        
        cached_result = await cache_service.get(cache_key)
        if cached_result:
            return cached_result
        
        async with self.rate_limiter:
            try:
                session = await self._get_session()
                self.request_count += 1
                
                params = {'asin': asin, 'country': country}
                url = f"https://{self.api_host}/reviews"
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        reviews = data.get('data', {}).get('reviews', [])[:limit]
                        
                        await cache_service.set(cache_key, reviews, self.cache_ttl)
                        
                        return reviews
                    else:
                        logger.error(f"Reviews API error: {response.status}")
                        self.errors += 1
                        return []
                        
            except Exception as e:
                logger.error(f"Error getting product reviews: {e}")
                self.errors += 1
                return []
    
    async def get_categories(self) -> List[str]:
        """Get available product categories"""
        cache_key = "amazon_categories"
        
        cached_result = await cache_service.get(cache_key)
        if cached_result:
            return cached_result
        
        # Common Amazon categories
        categories = [
            "Electronics",
            "Books",
            "Clothing",
            "Home & Kitchen",
            "Sports & Outdoors",
            "Beauty & Personal Care",
            "Toys & Games",
            "Health & Household",
            "Automotive",
            "Industrial & Scientific",
            "Office Products",
            "Pet Supplies",
            "Grocery & Gourmet Food",
            "Baby Products",
            "Tools & Home Improvement"
        ]
        
        await cache_service.set(cache_key, categories, 86400)  # 24 hours cache
        return categories
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get scraper statistics"""
        return {
            "total_requests": self.request_count,
            "cache_hits": self.cache_hits,
            "errors": self.errors,
            "cache_hit_rate": self.cache_hits / max(self.request_count, 1),
            "error_rate": self.errors / max(self.request_count, 1),
            "rate_limit": settings.amazon_rate_limit
        }
    
    async def close(self):
        """Close HTTP session and cleanup"""
        if self.session and not self.session.closed:
            await self.session.close()

# Global Amazon scraper service instance
amazon_scraper = AmazonScraperService()
