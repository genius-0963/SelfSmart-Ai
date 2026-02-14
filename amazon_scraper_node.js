// Real-time Amazon Data Scraper - Node.js Version
// Using your provided API key for live Amazon data

const https = require('https');
const http = require('http');
const querystring = require('querystring');

// Configuration
const API_KEY = 'd4cf23a971msh75af80bfc558d43p1403eejsn6eafeb67936b';
const API_HOST = 'real-time-amazon-data.p.rapidapi.com';

class AmazonScraper {
    constructor() {
        this.apiKey = API_KEY;
        this.host = API_HOST;
    }

    // Search for products
    async searchProducts(query, country = 'US', page = 1) {
        return new Promise((resolve, reject) => {
            const options = {
                method: 'GET',
                hostname: this.host,
                port: null,
                path: `/search?${querystring.stringify({ query, country, page })}`,
                headers: {
                    'x-rapidapi-key': this.apiKey,
                    'x-rapidapi-host': this.host,
                    'useQueryString': true
                }
            };

            const req = https.request(options, (res) => {
                const chunks = [];
                
                res.on('data', (chunk) => {
                    chunks.push(chunk);
                });
                
                res.on('end', () => {
                    try {
                        const body = Buffer.concat(chunks);
                        const data = JSON.parse(body.toString());
                        resolve(data);
                    } catch (error) {
                        reject(error);
                    }
                });
            });

            req.on('error', (error) => {
                reject(error);
            });

            req.end();
        });
    }

    // Get product reviews
    async getProductReviews(asin, country = 'US') {
        return new Promise((resolve, reject) => {
            const options = {
                method: 'GET',
                hostname: this.host,
                port: null,
                path: `/top-product-reviews?${querystring.stringify({ asin, country })}`,
                headers: {
                    'x-rapidapi-key': this.apiKey,
                    'x-rapidapi-host': this.host,
                    'useQueryString': true
                }
            };

            const req = https.request(options, (res) => {
                const chunks = [];
                
                res.on('data', (chunk) => {
                    chunks.push(chunk);
                });
                
                res.on('end', () => {
                    try {
                        const body = Buffer.concat(chunks);
                        const data = JSON.parse(body.toString());
                        resolve(data);
                    } catch (error) {
                        reject(error);
                    }
                });
            });

            req.on('error', (error) => {
                reject(error);
            });

            req.end();
        });
    }

    // Get product details
    async getProductDetails(asin, country = 'US') {
        return new Promise((resolve, reject) => {
            const options = {
                method: 'GET',
                hostname: this.host,
                port: null,
                path: `/product-details?${querystring.stringify({ asin, country })}`,
                headers: {
                    'x-rapidapi-key': this.apiKey,
                    'x-rapidapi-host': this.host,
                    'useQueryString': true
                }
            };

            const req = https.request(options, (res) => {
                const chunks = [];
                
                res.on('data', (chunk) => {
                    chunks.push(chunk);
                });
                
                res.on('end', () => {
                    try {
                        const body = Buffer.concat(chunks);
                        const data = JSON.parse(body.toString());
                        resolve(data);
                    } catch (error) {
                        reject(error);
                    }
                });
            });

            req.on('error', (error) => {
                reject(error);
            });

            req.end();
        });
    }

    // Complete product search with reviews
    async searchWithReviews(query, limit = 5) {
        try {
            console.log(`🔍 Searching for: ${query}`);
            
            // Search products
            const searchResults = await this.searchProducts(query);
            
            if (!searchResults.data || !searchResults.data.products) {
                return [];
            }

            const products = searchResults.data.products.slice(0, limit);
            const detailedProducts = [];

            // Get reviews for each product
            for (const product of products) {
                try {
                    if (product.asin) {
                        const reviews = await this.getProductReviews(product.asin);
                        const details = await this.getProductDetails(product.asin);
                        
                        detailedProducts.push({
                            ...product,
                            reviews: reviews.data || {},
                            details: details.data || {},
                            source: 'Amazon (Real-Time)'
                        });
                    } else {
                        detailedProducts.push({
                            ...product,
                            source: 'Amazon (Basic)'
                        });
                    }
                } catch (error) {
                    console.error(`Error getting details for ${product.asin}:`, error.message);
                    detailedProducts.push({
                        ...product,
                        source: 'Amazon (Partial)'
                    });
                }
            }

            return detailedProducts;
        } catch (error) {
            console.error('Search error:', error);
            throw error;
        }
    }
}

// Express server for the scraper
const express = require('express');
const cors = require('cors');
const app = express();

// Middleware
app.use(cors());
app.use(express.json());

// Initialize scraper
const scraper = new AmazonScraper();

// Routes
app.get('/', (req, res) => {
    res.json({
        service: 'Amazon Real-Time Data Scraper',
        version: '1.0.0',
        status: 'operational',
        endpoints: [
            '/search?q=laptop',
            '/reviews/:asin',
            '/details/:asin',
            '/search-with-reviews?q=gaming%20laptop'
        ]
    });
});

app.get('/search', async (req, res) => {
    try {
        const { q, country = 'US', page = 1 } = req.query;
        
        if (!q) {
            return res.status(400).json({ error: 'Query parameter "q" is required' });
        }

        const results = await scraper.searchProducts(q, country, page);
        res.json(results);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

app.get('/reviews/:asin', async (req, res) => {
    try {
        const { asin } = req.params;
        const { country = 'US' } = req.query;
        
        const reviews = await scraper.getProductReviews(asin, country);
        res.json(reviews);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

app.get('/details/:asin', async (req, res) => {
    try {
        const { asin } = req.params;
        const { country = 'US' } = req.query;
        
        const details = await scraper.getProductDetails(asin, country);
        res.json(details);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

app.get('/search-with-reviews', async (req, res) => {
    try {
        const { q, limit = 5, country = 'US' } = req.query;
        
        if (!q) {
            return res.status(400).json({ error: 'Query parameter "q" is required' });
        }

        const results = await scraper.searchWithReviews(q, parseInt(limit));
        res.json(results);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Health check
app.get('/health', (req, res) => {
    res.json({ 
        status: 'healthy', 
        timestamp: new Date().toISOString(),
        api_key_configured: scraper.apiKey !== 'demo_key'
    });
});

// Start server
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log('🚀 Amazon Real-Time Scraper Server');
    console.log(`📱 Server running on http://localhost:${PORT}`);
    console.log('🔍 Endpoints:');
    console.log(`   GET /search?q=laptop`);
    console.log(`   GET /reviews/:asin`);
    console.log(`   GET /details/:asin`);
    console.log(`   GET /search-with-reviews?q=gaming%20laptop`);
    console.log(`   GET /health`);
    console.log('🔑 Using real Amazon API key');
});

// Export for use as module
module.exports = AmazonScraper;

// Example usage
if (require.main === module) {
    // Test the scraper
    async function testScraper() {
        const scraper = new AmazonScraper();
        
        try {
            console.log('🧪 Testing Amazon scraper...');
            
            // Test search
            const results = await scraper.searchWithReviews('gaming laptop', 2);
            console.log('✅ Search results:', results.length, 'products found');
            
            if (results.length > 0) {
                const product = results[0];
                console.log('📦 Sample product:', {
                    title: product.product_title,
                    price: product.product_price,
                    rating: product.product_star_rating,
                    reviews: product.reviews.total_reviews || 'N/A'
                });
            }
            
        } catch (error) {
            console.error('❌ Test failed:', error.message);
        }
    }
    
    // Run test after server starts
    setTimeout(testScraper, 2000);
}
