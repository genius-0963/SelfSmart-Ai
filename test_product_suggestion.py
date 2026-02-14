#!/usr/bin/env python3
"""
Test script for product_suggestion module
"""

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all imports work correctly."""
    try:
        print("🧪 Testing product_suggestion module imports...")
        
        # Test direct imports
        from copilot_chatbot.product_suggestion.recommender import AmazonProductRecommender, ProductRecommendation
        print("✅ Successfully imported AmazonProductRecommender and ProductRecommendation")
        
        from copilot_chatbot.product_suggestion.data_processor import AmazonDataProcessor, ProcessedProduct
        print("✅ Successfully imported AmazonDataProcessor and ProcessedProduct")
        
        # Test module-level imports
        from copilot_chatbot.product_suggestion import (
            AmazonProductRecommender as Recommender,
            ProductRecommendation as Recommendation,
            AmazonDataProcessor as Processor,
            ProcessedProduct as Product
        )
        print("✅ Successfully imported from module level")
        
        # Test that classes are properly defined
        assert hasattr(Recommender, '__init__'), "AmazonProductRecommender should have __init__ method"
        assert hasattr(Recommendation, '__dataclass_fields__'), "ProductRecommendation should be a dataclass"
        assert hasattr(Processor, '__init__'), "AmazonDataProcessor should have __init__ method"
        assert hasattr(Product, '__dataclass_fields__'), "ProcessedProduct should be a dataclass"
        
        print("🎉 All tests passed! The product_suggestion module is working correctly.")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)
