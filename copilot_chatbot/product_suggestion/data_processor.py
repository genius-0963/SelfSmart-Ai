"""
Amazon Product Data Processor

Processes and cleans Amazon product data for training the suggestion system.
"""

import json
import logging
import re
import pandas as pd
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
import numpy as np
from collections import Counter

logger = logging.getLogger(__name__)


@dataclass
class ProcessedProduct:
    """Processed product data structure."""
    
    product_id: str
    title: str
    brand: str
    price: float
    original_price: Optional[float]
    discount_percentage: Optional[float]
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
    price_tier: str
    rating_tier: str
    popularity_score: float
    quality_score: float
    value_score: float
    url: str
    processed_at: str


class AmazonDataProcessor:
    """Processes Amazon product data for training."""
    
    def __init__(self):
        """Initialize the data processor."""
        self.price_tiers = {
            'budget': (0, 25),
            'mid_range': (25, 100),
            'premium': (100, 500),
            'luxury': (500, float('inf'))
        }
        
        self.rating_tiers = {
            'poor': (0, 2.5),
            'fair': (2.5, 3.5),
            'good': (3.5, 4.0),
            'very_good': (4.0, 4.5),
            'excellent': (4.5, 5.0)
        }
    
    def load_raw_data(self, file_path: str) -> List[Dict]:
        """
        Load raw Amazon product data from JSON file.
        
        Args:
            file_path: Path to the raw JSON data file
            
        Returns:
            List of raw product dictionaries
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            logger.info(f"Loaded {len(data)} raw products from {file_path}")
            return data
            
        except Exception as e:
            logger.error(f"Failed to load raw data from {file_path}: {e}")
            raise
    
    def clean_text(self, text: str) -> str:
        """
        Clean and normalize text data.
        
        Args:
            text: Raw text string
            
        Returns:
            Cleaned text string
        """
        if not text:
            return ""
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s\.\,\!\?\-\%\$\&\(\)]', '', text)
        
        # Strip and return
        return text.strip()
    
    def clean_price(self, price: Any) -> Optional[float]:
        """
        Clean and validate price data.
        
        Args:
            price: Raw price value
            
        Returns:
            Cleaned price or None if invalid
        """
        if price is None:
            return None
        
        try:
            if isinstance(price, str):
                # Extract numeric value from string
                price_match = re.search(r'[\d,]+\.?\d*', str(price).replace(',', ''))
                if price_match:
                    return float(price_match.group())
            elif isinstance(price, (int, float)):
                return float(price)
            
            return None
            
        except (ValueError, TypeError):
            return None
    
    def clean_rating(self, rating: Any) -> float:
        """
        Clean and validate rating data.
        
        Args:
            rating: Raw rating value
            
        Returns:
            Cleaned rating (0-5 scale)
        """
        if rating is None:
            return 0.0
        
        try:
            clean_rating = float(rating)
            # Clamp to 0-5 range
            return max(0.0, min(5.0, clean_rating))
            
        except (ValueError, TypeError):
            return 0.0
    
    def clean_review_count(self, count: Any) -> int:
        """
        Clean and validate review count.
        
        Args:
            count: Raw review count
            
        Returns:
            Cleaned review count
        """
        if count is None:
            return 0
        
        try:
            if isinstance(count, str):
                # Extract numeric value
                count_match = re.search(r'[\d,]+', str(count).replace(',', ''))
                if count_match:
                    return int(count_match.group())
            elif isinstance(count, (int, float)):
                return int(count)
            
            return 0
            
        except (ValueError, TypeError):
            return 0
    
    def categorize_price(self, price: float) -> str:
        """
        Categorize price into tiers.
        
        Args:
            price: Product price
            
        Returns:
            Price tier category
        """
        for tier, (min_price, max_price) in self.price_tiers.items():
            if min_price <= price < max_price:
                return tier
        return 'unknown'
    
    def categorize_rating(self, rating: float) -> str:
        """
        Categorize rating into tiers.
        
        Args:
            rating: Product rating
            
        Returns:
            Rating tier category
        """
        for tier, (min_rating, max_rating) in self.rating_tiers.items():
            if min_rating <= rating < max_rating:
                return tier
        return 'unknown'
    
    def calculate_popularity_score(self, rating: float, review_count: int, 
                                 best_seller_rank: Optional[int]) -> float:
        """
        Calculate popularity score based on rating, reviews, and rank.
        
        Args:
            rating: Product rating
            review_count: Number of reviews
            best_seller_rank: Best seller rank (lower is better)
            
        Returns:
            Popularity score (0-1 scale)
        """
        # Rating component (40% weight)
        rating_score = rating / 5.0
        
        # Review count component (40% weight) - log scale
        review_score = min(1.0, np.log10(max(1, review_count)) / 4.0)
        
        # Best seller rank component (20% weight)
        rank_score = 1.0
        if best_seller_rank:
            # Lower rank = higher score
            rank_score = max(0.1, 1.0 - (np.log10(best_seller_rank) / 6.0))
        
        popularity = (rating_score * 0.4) + (review_score * 0.4) + (rank_score * 0.2)
        return min(1.0, popularity)
    
    def calculate_quality_score(self, rating: float, review_count: int, 
                               prime_eligible: bool, brand: str) -> float:
        """
        Calculate quality score based on various factors.
        
        Args:
            rating: Product rating
            review_count: Number of reviews
            prime_eligible: Whether product is Prime eligible
            brand: Product brand
            
        Returns:
            Quality score (0-1 scale)
        """
        # Base rating score (50% weight)
        rating_score = rating / 5.0
        
        # Review confidence (20% weight) - more reviews = more confidence
        review_confidence = min(1.0, review_count / 100.0)
        
        # Prime eligibility bonus (15% weight)
        prime_bonus = 1.0 if prime_eligible else 0.7
        
        # Brand recognition (15% weight) - simple heuristic
        known_brands = {
            'apple', 'samsung', 'sony', 'lg', 'microsoft', 'dell', 'hp', 'canon',
            'nikon', 'bose', 'jbl', 'logitech', 'amazon', 'google', 'nintendo'
        }
        brand_bonus = 1.0 if brand.lower() in known_brands else 0.8
        
        quality = (rating_score * 0.5) + (review_confidence * 0.2) + \
                 (prime_bonus * 0.15) + (brand_bonus * 0.15)
        
        return min(1.0, quality)
    
    def calculate_value_score(self, price: float, rating: float, 
                            original_price: Optional[float]) -> float:
        """
        Calculate value score based on price and quality.
        
        Args:
            price: Current price
            rating: Product rating
            original_price: Original price (for discount calculation)
            
        Returns:
            Value score (0-1 scale)
        """
        # Quality per dollar
        quality_per_price = rating / max(1.0, price / 10.0)
        
        # Discount bonus
        discount_bonus = 1.0
        if original_price and original_price > price:
            discount_pct = (original_price - price) / original_price
            discount_bonus = 1.0 + (discount_pct * 0.5)
        
        # Normalize and combine
        value_score = min(1.0, quality_per_price * 0.7 * discount_bonus)
        return value_score
    
    def process_product(self, raw_product: Dict) -> Optional[ProcessedProduct]:
        """
        Process a single raw product.
        
        Args:
            raw_product: Raw product dictionary
            
        Returns:
            ProcessedProduct object or None if invalid
        """
        try:
            # Clean and validate basic fields
            product_id = raw_product.get('product_id', '').strip()
            if not product_id:
                return None
            
            title = self.clean_text(raw_product.get('title', ''))
            if not title or len(title) < 10:
                return None
            
            brand = self.clean_text(raw_product.get('brand', 'Unknown'))
            
            # Clean price
            price = self.clean_price(raw_product.get('price'))
            if price is None or price <= 0:
                return None
            
            original_price = self.clean_price(raw_product.get('original_price'))
            
            # Calculate discount percentage
            discount_percentage = None
            if original_price and original_price > price:
                discount_percentage = ((original_price - price) / original_price) * 100
            
            # Clean rating and review count
            rating = self.clean_rating(raw_product.get('rating'))
            review_count = self.clean_review_count(raw_product.get('review_count'))
            
            # Clean category information
            category = self.clean_text(raw_product.get('category', 'Unknown'))
            subcategory = self.clean_text(raw_product.get('subcategory', ''))
            
            # Clean description and features
            description = self.clean_text(raw_product.get('description', ''))
            
            raw_features = raw_product.get('features', [])
            features = [self.clean_text(feature) for feature in raw_features if feature]
            features = [f for f in features if len(f) > 5]  # Filter very short features
            
            # Clean images
            images = raw_product.get('images', [])
            images = [img for img in images if img and img.startswith('http')]
            
            # Other fields
            availability = self.clean_text(raw_product.get('availability', 'Unknown'))
            prime_eligible = bool(raw_product.get('prime_eligible', False))
            best_seller_rank = raw_product.get('best_seller_rank')
            url = raw_product.get('url', '')
            
            # Calculate derived metrics
            price_tier = self.categorize_price(price)
            rating_tier = self.categorize_rating(rating)
            popularity_score = self.calculate_popularity_score(rating, review_count, best_seller_rank)
            quality_score = self.calculate_quality_score(rating, review_count, prime_eligible, brand)
            value_score = self.calculate_value_score(price, rating, original_price)
            
            processed = ProcessedProduct(
                product_id=product_id,
                title=title,
                brand=brand,
                price=price,
                original_price=original_price,
                discount_percentage=discount_percentage,
                rating=rating,
                review_count=review_count,
                category=category,
                subcategory=subcategory,
                description=description,
                features=features,
                images=images,
                availability=availability,
                prime_eligible=prime_eligible,
                best_seller_rank=best_seller_rank,
                price_tier=price_tier,
                rating_tier=rating_tier,
                popularity_score=popularity_score,
                quality_score=quality_score,
                value_score=value_score,
                url=url,
                processed_at=pd.Timestamp.now().isoformat()
            )
            
            return processed
            
        except Exception as e:
            logger.warning(f"Failed to process product {raw_product.get('product_id', 'unknown')}: {e}")
            return None
    
    def process_products(self, raw_products: List[Dict]) -> List[ProcessedProduct]:
        """
        Process a list of raw products.
        
        Args:
            raw_products: List of raw product dictionaries
            
        Returns:
            List of ProcessedProduct objects
        """
        processed_products = []
        
        logger.info(f"Processing {len(raw_products)} raw products...")
        
        for i, raw_product in enumerate(raw_products, 1):
            processed = self.process_product(raw_product)
            if processed:
                processed_products.append(processed)
            
            if i % 100 == 0:
                logger.info(f"Processed {i}/{len(raw_products)} products...")
        
        logger.info(f"Successfully processed {len(processed_products)} products")
        return processed_products
    
    def save_processed_data(self, processed_products: List[ProcessedProduct], output_path: str):
        """
        Save processed products to JSON file.
        
        Args:
            processed_products: List of ProcessedProduct objects
            output_path: Output file path
        """
        try:
            products_data = [asdict(product) for product in processed_products]
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(products_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved {len(processed_products)} processed products to {output_path}")
            
        except Exception as e:
            logger.error(f"Failed to save processed data: {e}")
            raise
    
    def generate_data_report(self, processed_products: List[ProcessedProduct]) -> Dict[str, Any]:
        """
        Generate a comprehensive data quality report.
        
        Args:
            processed_products: List of ProcessedProduct objects
            
        Returns:
            Data quality report dictionary
        """
        if not processed_products:
            return {"error": "No processed products to analyze"}
        
        # Convert to DataFrame for analysis
        df_data = [asdict(p) for p in processed_products]
        df = pd.DataFrame(df_data)
        
        report = {
            "total_products": len(processed_products),
            "processing_date": pd.Timestamp.now().isoformat(),
            
            # Price analysis
            "price_analysis": {
                "min_price": float(df['price'].min()),
                "max_price": float(df['price'].max()),
                "avg_price": float(df['price'].mean()),
                "median_price": float(df['price'].median()),
                "price_tiers": df['price_tier'].value_counts().to_dict()
            },
            
            # Rating analysis
            "rating_analysis": {
                "min_rating": float(df['rating'].min()),
                "max_rating": float(df['rating'].max()),
                "avg_rating": float(df['rating'].mean()),
                "median_rating": float(df['rating'].median()),
                "rating_tiers": df['rating_tier'].value_counts().to_dict()
            },
            
            # Category analysis
            "category_analysis": {
                "total_categories": df['category'].nunique(),
                "top_categories": df['category'].value_counts().head(10).to_dict(),
                "top_brands": df['brand'].value_counts().head(10).to_dict()
            },
            
            # Quality metrics
            "quality_metrics": {
                "avg_popularity_score": float(df['popularity_score'].mean()),
                "avg_quality_score": float(df['quality_score'].mean()),
                "avg_value_score": float(df['value_score'].mean()),
                "prime_eligible_pct": float(df['prime_eligible'].mean() * 100),
                "with_discount_pct": float(df['discount_percentage'].notna().mean() * 100)
            },
            
            # Data completeness
            "data_completeness": {
                "with_description_pct": float((df['description'] != '').mean() * 100),
                "with_features_pct": float((df['features'].str.len() > 0).mean() * 100),
                "with_images_pct": float((df['images'].str.len() > 0).mean() * 100),
                "with_reviews_pct": float((df['review_count'] > 0).mean() * 100)
            }
        }
        
        return report
    
    def save_data_report(self, report: Dict[str, Any], output_path: str):
        """
        Save data quality report to JSON file.
        
        Args:
            report: Data quality report
            output_path: Output file path
        """
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved data report to {output_path}")
            
        except Exception as e:
            logger.error(f"Failed to save data report: {e}")
            raise


def main():
    """Example usage of the Amazon data processor."""
    
    # Initialize processor
    processor = AmazonDataProcessor()
    
    # Process each category file
    categories = ['electronics', 'home_kitchen', 'beauty_personal_care', 'sports_outdoors', 'books']
    
    for category in categories:
        input_file = f"data/amazon_products_{category}.json"
        output_file = f"data/processed_amazon_products_{category}.json"
        report_file = f"data/data_report_{category}.json"
        
        try:
            # Load raw data
            raw_products = processor.load_raw_data(input_file)
            
            # Process products
            processed_products = processor.process_products(raw_products)
            
            # Save processed data
            processor.save_processed_data(processed_products, output_file)
            
            # Generate and save report
            report = processor.generate_data_report(processed_products)
            processor.save_data_report(report, report_file)
            
            print(f"✅ Processed {category}: {len(processed_products)} products")
            
        except FileNotFoundError:
            print(f"⚠️  File not found: {input_file}")
        except Exception as e:
            print(f"❌ Error processing {category}: {e}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()