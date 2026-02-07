# Amazon Product Data Setup Script

This script helps you set up the Amazon product data for training your copilot suggestion system.

## Prerequisites

Install the required packages:
```bash
pip install aiohttp beautifulsoup4 sentence-transformers scikit-learn pandas numpy
```

## Usage

### 1. Scrape Amazon Product Data

Run the scraper to collect product data from Amazon:

```python
import asyncio
from copilot_chatbot.data_scrapers.amazon_scraper import AmazonScraper

async def scrape_data():
    categories = [
        "electronics",
        "home kitchen", 
        "beauty personal care",
        "sports outdoors",
        "books"
    ]
    
    async with AmazonScraper() as scraper:
        for category in categories:
            print(f"Scraping {category}...")
            products = await scraper.scrape_category_products(category, max_products=100)
            
            if products:
                filename = f"data/amazon_products_{category.replace(' ', '_')}.json"
                await scraper.save_products_to_json(products, filename)
                print(f"Saved {len(products)} products to {filename}")

if __name__ == "__main__":
    asyncio.run(scrape_data())
```

### 2. Process the Raw Data

Clean and process the scraped data:

```python
from copilot_chatbot.product_suggestion.data_processor import AmazonDataProcessor

def process_data():
    processor = AmazonDataProcessor()
    
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
    process_data()
```

### 3. Build Product Embeddings

Create embeddings for semantic search:

```python
from copilot_chatbot.product_suggestion.recommender import AmazonProductRecommender

def build_embeddings():
    recommender = AmazonProductRecommender()
    
    # Load processed data (using electronics as example)
    recommender.load_processed_products("data/processed_amazon_products_electronics.json")
    
    # Build embeddings
    recommender.build_embeddings()
    
    # Save embeddings for future use
    recommender.save_embeddings("data/amazon_product_embeddings")
    
    print("✅ Embeddings built and saved successfully!")

if __name__ == "__main__":
    build_embeddings()
```

### 4. Test the System

Test your product suggestion system:

```python
from copilot_chatbot.product_suggestion.recommender import AmazonProductRecommender

def test_suggestions():
    recommender = AmazonProductRecommender()
    
    # Load pre-built embeddings
    recommender.load_embeddings("data/amazon_product_embeddings")
    
    # Test queries
    queries = [
        "wireless headphones with noise cancellation",
        "laptop for programming", 
        "smart watch for fitness"
    ]
    
    for query in queries:
        print(f"\nQuery: {query}")
        recommendations = recommender.find_similar_products(query, max_results=5)
        
        for i, rec in enumerate(recommendations, 1):
            print(f"{i}. {rec.title}")
            print(f"   Price: ${rec.price:.2f} | Rating: {rec.rating}★")
            print(f"   {rec.recommendation_reason}")
            print(f"   Similarity: {rec.similarity_score:.3f}")

if __name__ == "__main__":
    test_suggestions()
```

## API Endpoints

Once your copilot is running, you can use these endpoints:

### Product Suggestions
```bash
curl -X POST "http://localhost:8001/products/suggest" \
  -H "Content-Type: application/json" \
  -d '{"query": "wireless headphones", "max_results": 5}'
```

### Similar Products
```bash
curl -X POST "http://localhost:8001/products/similar/B08HD5KD2F" \
  -H "Content-Type: application/json" \
  -d '{"max_results": 5}'
```

### Category Products
```bash
curl -X POST "http://localhost:8001/products/category/electronics" \
  -H "Content-Type: application/json" \
  -d '{"max_results": 10, "min_rating": 4.0}'
```

### Price-based Recommendations
```bash
curl -X POST "http://localhost:8001/products/price-based" \
  -H "Content-Type: application/json" \
  -d '{"max_price": 100, "category": "electronics", "max_results": 5}'
```

### Enhanced Chat with Product Suggestions
```bash
curl -X POST "http://localhost:8001/products/chat" \
  -H "Content-Type: application/json" \
  -d '{"query": "What are the best wireless headphones for running?", "session_id": "user123"}'
```

## Configuration

Update your `copilot_chatbot/config.py` to customize the system:

```python
class ProductSuggestionConfig(BaseSettings):
    embeddings_path: str = "data/amazon_product_embeddings"
    model_name: str = "all-MiniLM-L6-v2"
    similarity_threshold: float = 0.3
    max_recommendations: int = 10
    enable_cache: bool = True
    cache_ttl: int = 3600  # 1 hour
```

## Important Notes

1. **Legal Compliance**: Always respect Amazon's Terms of Service and robots.txt when scraping
2. **Rate Limiting**: The scraper includes built-in delays to avoid being blocked
3. **Data Quality**: Process the data to remove duplicates and invalid entries
4. **Storage**: Embeddings can be large, ensure you have adequate disk space
5. **Performance**: Consider using a GPU for faster embedding generation with large datasets

## Troubleshooting

- **Scraping Issues**: If you get blocked, try increasing delays or using rotating proxies
- **Memory Issues**: For large datasets, process in smaller batches
- **Embedding Errors**: Ensure you have enough RAM for the embedding model and data
- **API Errors**: Check that all dependencies are installed and the copilot service is running
