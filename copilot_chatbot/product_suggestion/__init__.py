"""
SmartShelf AI - Product Suggestion Module

Provides intelligent product recommendations and data processing
for Amazon products using semantic search and machine learning.
"""

from .recommender import AmazonProductRecommender, ProductRecommendation
from .data_processor import AmazonDataProcessor, ProcessedProduct

__version__ = "1.0.0"
__author__ = "SmartShelf AI Team"

# Export main classes
__all__ = [
    "AmazonProductRecommender",
    "ProductRecommendation", 
    "AmazonDataProcessor",
    "ProcessedProduct"
]