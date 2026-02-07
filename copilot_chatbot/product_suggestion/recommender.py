"""
Amazon Product Suggestion System

Provides intelligent product recommendations based on Amazon data training.
"""

import json
import logging
import numpy as np
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
import pickle
import os

logger = logging.getLogger(__name__)


@dataclass
class ProductRecommendation:
    """Product recommendation data structure."""
    
    product_id: str
    title: str
    brand: str
    price: float
    rating: float
    review_count: int
    category: str
    similarity_score: float
    recommendation_reason: str
    url: str


class AmazonProductRecommender:
    """Amazon product recommendation engine."""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize the recommender system.
        
        Args:
            model_name: Name of the sentence transformer model
        """
        self.model_name = model_name
        self.embedding_model = None
        self.product_embeddings = None
        self.products = []
        self.tfidf_vectorizer = None
        self.tfidf_matrix = None
        
        # Load the embedding model
        self._load_embedding_model()
    
    def _load_embedding_model(self):
        """Load the sentence transformer model."""
        try:
            self.embedding_model = SentenceTransformer(self.model_name)
            logger.info(f"Loaded embedding model: {self.model_name}")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise
    
    def load_amazon_products(self, json_file_path: str):
        """
        Load Amazon products from JSON file.
        
        Args:
            json_file_path: Path to the JSON file containing Amazon products
        """
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                products_data = json.load(f)
            
            self.products = products_data
            logger.info(f"Loaded {len(self.products)} products from {json_file_path}")
            
        except Exception as e:
            logger.error(f"Failed to load products from {json_file_path}: {e}")
            raise
    
    def load_processed_products(self, json_file_path: str):
        """
        Load processed Amazon products from JSON file.
        
        Args:
            json_file_path: Path to the processed JSON file
        """
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                products_data = json.load(f)
            
            self.products = products_data
            logger.info(f"Loaded {len(self.products)} processed products from {json_file_path}")
            
        except Exception as e:
            logger.error(f"Failed to load processed products from {json_file_path}: {e}")
            raise
    
    def _create_product_text(self, product: Dict) -> str:
        """
        Create searchable text from product data.
        
        Args:
            product: Product dictionary
            
        Returns:
            Combined text for embedding
        """
        text_parts = []
        
        # Add title (most important)
        if product.get('title'):
            text_parts.append(product['title'])
        
        # Add brand
        if product.get('brand'):
            text_parts.append(product['brand'])
        
        # Add category and subcategory
        if product.get('category'):
            text_parts.append(product['category'])
        if product.get('subcategory'):
            text_parts.append(product['subcategory'])
        
        # Add features
        if product.get('features'):
            text_parts.extend(product['features'])
        
        # Add description (truncated)
        if product.get('description'):
            description = product['description'][:500]  # Limit description length
            text_parts.append(description)
        
        return ' '.join(text_parts)
    
    def build_embeddings(self):
        """Build embeddings for all loaded products."""
        if not self.products:
            raise ValueError("No products loaded. Call load_amazon_products first.")
        
        logger.info("Building product embeddings...")
        
        # Create text representations
        product_texts = [self._create_product_text(product) for product in self.products]
        
        # Generate embeddings
        self.product_embeddings = self.embedding_model.encode(
            product_texts,
            show_progress_bar=True,
            batch_size=32,
            normalize_embeddings=True
        )
        
        # Also build TF-IDF for keyword-based search
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=5000,
            stop_words='english',
            ngram_range=(1, 2)
        )
        self.tfidf_matrix = self.tfidf_vectorizer.fit_transform(product_texts)
        
        logger.info(f"Built embeddings for {len(self.products)} products")
        logger.info(f"Embedding shape: {self.product_embeddings.shape}")
    
    def save_embeddings(self, save_path: str):
        """
        Save embeddings and vectorizer to disk.
        
        Args:
            save_path: Base path for saving (without extension)
        """
        if self.product_embeddings is None:
            raise ValueError("No embeddings to save. Call build_embeddings first.")
        
        try:
            # Save embeddings
            embeddings_path = f"{save_path}_embeddings.pkl"
            with open(embeddings_path, 'wb') as f:
                pickle.dump(self.product_embeddings, f)
            
            # Save TF-IDF components
            tfidf_path = f"{save_path}_tfidf.pkl"
            with open(tfidf_path, 'wb') as f:
                pickle.dump({
                    'vectorizer': self.tfidf_vectorizer,
                    'matrix': self.tfidf_matrix
                }, f)
            
            # Save products metadata
            products_path = f"{save_path}_products.json"
            with open(products_path, 'w', encoding='utf-8') as f:
                json.dump(self.products, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved embeddings to {embeddings_path}")
            logger.info(f"Saved TF-IDF to {tfidf_path}")
            logger.info(f"Saved products to {products_path}")
            
        except Exception as e:
            logger.error(f"Failed to save embeddings: {e}")
            raise
    
    def load_embeddings(self, load_path: str):
        """
        Load embeddings and vectorizer from disk.
        
        Args:
            load_path: Base path for loading (without extension)
        """
        try:
            # Load embeddings
            embeddings_path = f"{load_path}_embeddings.pkl"
            with open(embeddings_path, 'rb') as f:
                self.product_embeddings = pickle.load(f)
            
            # Load TF-IDF components
            tfidf_path = f"{load_path}_tfidf.pkl"
            with open(tfidf_path, 'rb') as f:
                tfidf_data = pickle.load(f)
                self.tfidf_vectorizer = tfidf_data['vectorizer']
                self.tfidf_matrix = tfidf_data['matrix']
            
            # Load products metadata
            products_path = f"{load_path}_products.json"
            with open(products_path, 'r', encoding='utf-8') as f:
                self.products = json.load(f)
            
            logger.info(f"Loaded embeddings for {len(self.products)} products")
            
        except Exception as e:
            logger.error(f"Failed to load embeddings: {e}")
            raise
    
    def find_similar_products(self, query: str, max_results: int = 10) -> List[ProductRecommendation]:
        """
        Find products similar to the query.
        
        Args:
            query: Search query
            max_results: Maximum number of results to return
            
        Returns:
            List of product recommendations
        """
        if self.product_embeddings is None:
            raise ValueError("No embeddings available. Call build_embeddings or load_embeddings first.")
        
        # Generate query embedding
        query_embedding = self.embedding_model.encode([query], normalize_embeddings=True)
        
        # Calculate cosine similarity
        similarities = cosine_similarity(query_embedding, self.product_embeddings)[0]
        
        # Get top similar products
        top_indices = np.argsort(similarities)[::-1][:max_results]
        
        recommendations = []
        for idx in top_indices:
            if similarities[idx] > 0.3:  # Minimum similarity threshold
                product = self.products[idx]
                
                recommendation = ProductRecommendation(
                    product_id=product['product_id'],
                    title=product['title'],
                    brand=product['brand'],
                    price=product['price'],
                    rating=product['rating'],
                    review_count=product['review_count'],
                    category=product['category'],
                    similarity_score=float(similarities[idx]),
                    recommendation_reason=self._generate_recommendation_reason(product, similarities[idx]),
                    url=product['url']
                )
                recommendations.append(recommendation)
        
        return recommendations
    
    def find_similar_by_product_id(self, product_id: str, max_results: int = 10) -> List[ProductRecommendation]:
        """
        Find products similar to a given product ID.
        
        Args:
            product_id: Amazon product ID
            max_results: Maximum number of results to return
            
        Returns:
            List of similar product recommendations
        """
        if self.product_embeddings is None:
            raise ValueError("No embeddings available. Call build_embeddings or load_embeddings first.")
        
        # Find the product index
        target_idx = None
        for i, product in enumerate(self.products):
            if product['product_id'] == product_id:
                target_idx = i
                break
        
        if target_idx is None:
            raise ValueError(f"Product with ID {product_id} not found")
        
        # Get embedding for the target product
        target_embedding = self.product_embeddings[target_idx:target_idx+1]
        
        # Calculate similarities
        similarities = cosine_similarity(target_embedding, self.product_embeddings)[0]
        
        # Get top similar products (excluding the target itself)
        top_indices = np.argsort(similarities)[::-1][:max_results+1]
        top_indices = [idx for idx in top_indices if idx != target_idx][:max_results]
        
        recommendations = []
        for idx in top_indices:
            if similarities[idx] > 0.3:
                product = self.products[idx]
                
                recommendation = ProductRecommendation(
                    product_id=product['product_id'],
                    title=product['title'],
                    brand=product['brand'],
                    price=product['price'],
                    rating=product['rating'],
                    review_count=product['review_count'],
                    category=product['category'],
                    similarity_score=float(similarities[idx]),
                    recommendation_reason=self._generate_recommendation_reason(product, similarities[idx]),
                    url=product['url']
                )
                recommendations.append(recommendation)
        
        return recommendations
    
    def get_category_recommendations(self, category: str, max_results: int = 10, 
                                   min_rating: float = 4.0) -> List[ProductRecommendation]:
        """
        Get top products from a specific category.
        
        Args:
            category: Product category
            max_results: Maximum number of results
            min_rating: Minimum rating threshold
            
        Returns:
            List of category product recommendations
        """
        category_products = []
        
        for product in self.products:
            if (category.lower() in product.get('category', '').lower() or 
                category.lower() in product.get('subcategory', '').lower()):
                
                if product.get('rating', 0) >= min_rating:
                    # Create a recommendation based on rating and review count
                    score = (product.get('rating', 0) * 0.7 + 
                            min(product.get('review_count', 0) / 1000, 1) * 0.3)
                    
                    recommendation = ProductRecommendation(
                        product_id=product['product_id'],
                        title=product['title'],
                        brand=product['brand'],
                        price=product['price'],
                        rating=product['rating'],
                        review_count=product['review_count'],
                        category=product['category'],
                        similarity_score=float(score),
                        recommendation_reason=f"Top-rated product in {category} with {product['rating']}★ rating",
                        url=product['url']
                    )
                    category_products.append(recommendation)
        
        # Sort by score and return top results
        category_products.sort(key=lambda x: x.similarity_score, reverse=True)
        return category_products[:max_results]
    
    def get_price_based_recommendations(self, max_price: float, category: str = None, 
                                      max_results: int = 10) -> List[ProductRecommendation]:
        """
        Get product recommendations based on price range.
        
        Args:
            max_price: Maximum price filter
            category: Optional category filter
            max_results: Maximum number of results
            
        Returns:
            List of price-filtered recommendations
        """
        filtered_products = []
        
        for product in self.products:
            if product.get('price', float('inf')) <= max_price:
                if category is None or (category.lower() in product.get('category', '').lower()):
                    # Score based on rating and value for money
                    rating_score = product.get('rating', 0) / 5.0
                    value_score = (max_price - product.get('price', 0)) / max_price
                    combined_score = rating_score * 0.6 + value_score * 0.4
                    
                    recommendation = ProductRecommendation(
                        product_id=product['product_id'],
                        title=product['title'],
                        brand=product['brand'],
                        price=product['price'],
                        rating=product['rating'],
                        review_count=product['review_count'],
                        category=product['category'],
                        similarity_score=float(combined_score),
                        recommendation_reason=f"Best value under ${max_price:.2f}",
                        url=product['url']
                    )
                    filtered_products.append(recommendation)
        
        # Sort by combined score and return top results
        filtered_products.sort(key=lambda x: x.similarity_score, reverse=True)
        return filtered_products[:max_results]
    
    def _generate_recommendation_reason(self, product: Dict, similarity_score: float) -> str:
        """Generate a human-readable recommendation reason."""
        reasons = []
        
        if similarity_score > 0.8:
            reasons.append("Excellent match")
        elif similarity_score > 0.6:
            reasons.append("Good match")
        else:
            reasons.append("Similar product")
        
        if product.get('rating', 0) >= 4.5:
            reasons.append(f"highly rated ({product['rating']}★)")
        elif product.get('rating', 0) >= 4.0:
            reasons.append(f"well-rated ({product['rating']}★)")
        
        if product.get('review_count', 0) > 1000:
            reasons.append("popular choice")
        
        if product.get('prime_eligible', False):
            reasons.append("Prime eligible")
        
        if product.get('best_seller_rank'):
            reasons.append("best seller")
        
        return " - ".join(reasons) if reasons else "Recommended product"
    
    def get_stats(self) -> Dict[str, Any]:
        """Get recommender system statistics."""
        return {
            "total_products": len(self.products),
            "embedding_model": self.model_name,
            "embedding_shape": self.product_embeddings.shape if self.product_embeddings is not None else None,
            "categories": list(set(p.get('category', '') for p in self.products if p.get('category'))),
            "avg_rating": np.mean([p.get('rating', 0) for p in self.products if p.get('rating')]),
            "price_range": {
                "min": min([p.get('price', float('inf')) for p in self.products if p.get('price')]),
                "max": max([p.get('price', 0) for p in self.products if p.get('price')]),
                "avg": np.mean([p.get('price', 0) for p in self.products if p.get('price')])
            }
        }


def main():
    """Example usage of the Amazon product recommender."""
    
    # Initialize recommender
    recommender = AmazonProductRecommender()
    
    # Load Amazon products (assuming you have scraped data)
    try:
        recommender.load_amazon_products("data/amazon_products_electronics.json")
    except FileNotFoundError:
        print("No Amazon product data found. Please run the scraper first.")
        return
    
    # Build embeddings
    recommender.build_embeddings()
    
    # Save embeddings for future use
    recommender.save_embeddings("data/amazon_product_embeddings")
    
    # Example queries
    queries = [
        "wireless headphones with noise cancellation",
        "laptop for programming",
        "smart watch for fitness tracking"
    ]
    
    for query in queries:
        print(f"\nQuery: {query}")
        recommendations = recommender.find_similar_products(query, max_results=5)
        
        for i, rec in enumerate(recommendations, 1):
            print(f"{i}. {rec.title}")
            print(f"   Price: ${rec.price:.2f} | Rating: {rec.rating}★ | {rec.recommendation_reason}")
            print(f"   Similarity: {rec.similarity_score:.3f}")
    
    # Print statistics
    print("\nRecommender Statistics:")
    stats = recommender.get_stats()
    for key, value in stats.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()