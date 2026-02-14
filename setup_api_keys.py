#!/usr/bin/env python3
"""
API Keys Setup Script for SmartShelf AI
Sets up environment variables for live data scraping
"""

import os
from pathlib import Path

def setup_api_keys():
    """Setup API keys for live scraping."""
    
    print("🔑 SmartShelf AI - API Keys Setup")
    print("=" * 50)
    
    # Create .env file
    env_file = Path(".env")
    
    print("\n📋 Required API Keys:")
    print("1. RapidAPI Key (for Amazon/eBay access)")
    print("2. Amazon Product API Key (optional)")
    print("3. eBay API Key (optional)")
    
    print("\n📖 How to get RapidAPI Key:")
    print("1. Go to https://rapidapi.com/hub")
    print("2. Create free account")
    print("3. Subscribe to Amazon Product API (free tier available)")
    print("4. Subscribe to eBay Product API (free tier available)")
    print("5. Copy your RapidAPI key from dashboard")
    
    # Get API key from user
    rapidapi_key = input("\nEnter your RapidAPI Key (or press Enter to skip): ").strip()
    
    if rapidapi_key:
        # Write to .env file
        env_content = f"""# SmartShelf AI API Keys
RAPIDAPI_KEY={rapidapi_key}
AMAZON_API_KEY=demo_key
EBAY_API_KEY=demo_key

# Additional configuration
API_BASE_URL=https://localhost:8001
DEBUG=true
"""
        
        env_file.write_text(env_content)
        print(f"✅ API keys saved to {env_file}")
        
        # Also set for current session
        os.environ["RAPIDAPI_KEY"] = rapidapi_key
        
        print("\n🎉 Setup Complete!")
        print("Now you can run: python3 simple_chat_server.py")
        print("Live scraping will be enabled with your API key")
        
    else:
        print("\n⚠️  No API key provided. Running in demo mode with static data.")
        print("To enable live scraping later:")
        print("1. Get a RapidAPI key from https://rapidapi.com")
        print("2. Run this script again with your key")
    
    print("\n📚 API Documentation:")
    print("- Amazon API: https://rapidapi.com/apigeek/api/amazon23")
    print("- eBay API: https://rapidapi.com/apigeek/api/ebay23")
    
    print("\n🚀 Ready to start SmartShelf AI!")

if __name__ == "__main__":
    setup_api_keys()
