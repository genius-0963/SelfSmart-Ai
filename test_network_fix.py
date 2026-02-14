#!/usr/bin/env python3
"""
Test script to verify network/proxy fixes in product suggestion module
"""

import os
import sys
import asyncio
import logging

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_amazon_scraper():
    """Test Amazon scraper with proxy support."""
    try:
        print("🧪 Testing Amazon scraper network configuration...")
        
        from copilot_chatbot.data_scrapers.amazon_scraper import AmazonScraper
        
        # Test with proxy environment variables (if set)
        if os.getenv('HTTP_PROXY') or os.getenv('HTTPS_PROXY'):
            print(f"📡 Proxy detected: {os.getenv('HTTPS_PROXY') or os.getenv('HTTP_PROXY')}")
        else:
            print("🌐 No proxy detected - using direct connection")
        
        # Create scraper instance
        scraper = AmazonScraper(delay_range=(0.1, 0.5))
        
        # Test network connection (simple test)
        async with scraper:
            # Try to fetch a simple page
            test_url = "https://httpbin.org/get"  # Simple test endpoint
            print(f"🔗 Testing connection to: {test_url}")
            
            content = await scraper._get_page(test_url)
            if content:
                print("✅ Network connection successful!")
                return True
            else:
                print("❌ Network connection failed")
                return False
                
    except Exception as e:
        print(f"❌ Error testing scraper: {e}")
        return False

def test_product_suggestion_import():
    """Test that product suggestion module imports work."""
    try:
        print("🧪 Testing product suggestion module imports...")
        
        from copilot_chatbot.product_suggestion import (
            AmazonProductRecommender, 
            ProductRecommendation,
            AmazonDataProcessor,
            ProcessedProduct
        )
        
        print("✅ All imports successful!")
        
        # Test basic instantiation
        recommender = AmazonProductRecommender()
        processor = AmazonDataProcessor()
        
        print("✅ Classes instantiated successfully!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

async def main():
    """Run all tests."""
    print("🚀 Starting network/proxy tests...\n")
    
    # Test imports
    import_success = test_product_suggestion_import()
    print()
    
    # Test network connection
    network_success = await test_amazon_scraper()
    print()
    
    # Summary
    print("📊 Test Results:")
    print(f"   Imports: {'✅ PASS' if import_success else '❌ FAIL'}")
    print(f"   Network: {'✅ PASS' if network_success else '❌ FAIL'}")
    
    overall_success = import_success and network_success
    print(f"\n🎯 Overall: {'✅ ALL TESTS PASSED' if overall_success else '❌ SOME TESTS FAILED'}")
    
    return overall_success

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
