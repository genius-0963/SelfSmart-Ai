"""
Intelligent AI Backend - Technology Product Knowledge Base
Production-grade OOP implementation for comprehensive product information and recommendations
"""

import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class ProductCategory(Enum):
    """Enumeration of product categories"""
    LAPTOP = "laptop"
    SMARTPHONE = "smartphone"
    TABLET = "tablet"
    DESKTOP = "desktop"
    WEARABLE = "wearable"
    ACCESSORIES = "accessories"


class PriceRange(Enum):
    """Enumeration of price ranges"""
    BUDGET = "budget"
    MID_RANGE = "mid_range"
    PREMIUM = "premium"
    LUXURY = "luxury"


class UseCase(Enum):
    """Enumeration of use cases"""
    GAMING = "gaming"
    BUSINESS = "business"
    STUDENT = "student"
    CREATIVE = "creative"
    GENERAL = "general"
    DEVELOPMENT = "development"


@dataclass
class Product:
    """Data class for product information"""
    id: str
    name: str
    category: ProductCategory
    brand: str
    price_range: PriceRange
    specifications: Dict[str, Any]
    use_cases: List[UseCase]
    pros: List[str]
    cons: List[str]
    rating: float
    description: str


@dataclass
class RecommendationRequest:
    """Data class for recommendation requests"""
    category: ProductCategory
    budget_range: Optional[Tuple[float, float]]
    use_cases: List[UseCase]
    preferred_brands: List[str]
    required_features: List[str]
    user_preferences: Dict[str, Any]


class ProductKnowledgeBase:
    """Comprehensive product knowledge base"""
    
    def __init__(self):
        self.products = self._initialize_products()
        self.specifications_guide = self._initialize_specifications_guide()
        self.comparison_matrix = self._initialize_comparison_matrix()
        self.recommendation_engine = ProductRecommendationEngine(self.products)
        logger.info("Product Knowledge Base initialized with comprehensive product data")
    
    def _initialize_products(self) -> Dict[str, Product]:
        """Initialize comprehensive product database"""
        products = {}
        
        # Laptops
        products['macbook_air_m2'] = Product(
            id='macbook_air_m2',
            name='MacBook Air M2',
            category=ProductCategory.LAPTOP,
            brand='Apple',
            price_range=PriceRange.PREMIUM,
            specifications={
                'processor': 'Apple M2',
                'ram': '8GB/16GB',
                'storage': '256GB-1TB SSD',
                'display': '13.6" Liquid Retina',
                'battery': '18 hours',
                'weight': '1.24 kg',
                'operating_system': 'macOS'
            },
            use_cases=[UseCase.STUDENT, UseCase.BUSINESS, UseCase.CREATIVE, UseCase.GENERAL],
            pros=['Excellent performance', 'Amazing battery life', 'Premium build quality', 'Silent operation'],
            cons=['Limited ports', 'Not upgradeable', 'Higher price'],
            rating=4.5,
            description='The MacBook Air M2 offers incredible performance in a thin and light design, perfect for students and professionals.'
        )
        
        products['dell_xps_15'] = Product(
            id='dell_xps_15',
            name='Dell XPS 15',
            category=ProductCategory.LAPTOP,
            brand='Dell',
            price_range=PriceRange.PREMIUM,
            specifications={
                'processor': 'Intel Core i7-13700H',
                'ram': '16GB/32GB DDR5',
                'storage': '512GB-2TB SSD',
                'display': '15.6" FHD+ to 4K OLED',
                'battery': '8 hours',
                'weight': '1.8 kg',
                'operating_system': 'Windows 11',
                'graphics': 'NVIDIA RTX 4050/4060/4070'
            },
            use_cases=[UseCase.CREATIVE, UseCase.BUSINESS, UseCase.DEVELOPMENT, UseCase.GAMING],
            pros=['Stunning 4K display option', 'Powerful performance', 'Premium build', 'Excellent keyboard'],
            cons=['Can get expensive', 'Battery life with dedicated GPU', 'Runs warm under load'],
            rating=4.4,
            description='The Dell XPS 15 is a powerhouse laptop with a stunning display, ideal for creative professionals and power users.'
        )
        
        products['macbook_pro_14'] = Product(
            id='macbook_pro_14',
            name='MacBook Pro 14"',
            category=ProductCategory.LAPTOP,
            brand='Apple',
            price_range=PriceRange.PREMIUM,
            specifications={
                'processor': 'Apple M3 Pro/M3 Max',
                'ram': '18GB-128GB',
                'storage': '512GB-8TB SSD',
                'display': '14.2" Liquid Retina XDR',
                'battery': '18 hours',
                'weight': '1.6 kg',
                'operating_system': 'macOS'
            },
            use_cases=[UseCase.CREATIVE, UseCase.DEVELOPMENT, UseCase.BUSINESS],
            pros=['Incredible performance', 'Amazing Mini-LED display', 'Great battery life', 'Professional features'],
            cons=['Very expensive', 'Heavier than Air', 'Overkill for basic tasks'],
            rating=4.7,
            description='The MacBook Pro 14" is a professional-grade laptop with exceptional performance and the best display in its class.'
        )
        
        # Smartphones
        products['iphone_15_pro'] = Product(
            id='iphone_15_pro',
            name='iPhone 15 Pro',
            category=ProductCategory.SMARTPHONE,
            brand='Apple',
            price_range=PriceRange.PREMIUM,
            specifications={
                'processor': 'A17 Pro',
                'ram': '8GB',
                'storage': '128GB-1TB',
                'display': '6.1" Super Retina XDR ProMotion',
                'camera': '48MP Main + 12MP Ultra Wide + 12MP Telephoto',
                'battery': 'All-day battery',
                'weight': '187 g',
                'operating_system': 'iOS 17'
            },
            use_cases=[UseCase.GENERAL, UseCase.BUSINESS, UseCase.CREATIVE],
            pros=['Powerful A17 Pro chip', 'Excellent camera system', 'Premium titanium design', 'Great ecosystem'],
            cons=['Expensive', 'Limited customization', 'Charging speed could be better'],
            rating=4.6,
            description='The iPhone 15 Pro features a powerful A17 Pro chip, professional-grade camera system, and premium titanium design.'
        )
        
        products['samsung_s24_ultra'] = Product(
            id='samsung_s24_ultra',
            name='Samsung Galaxy S24 Ultra',
            category=ProductCategory.SMARTPHONE,
            brand='Samsung',
            price_range=PriceRange.PREMIUM,
            specifications={
                'processor': 'Snapdragon 8 Gen 3',
                'ram': '12GB/16GB',
                'storage': '256GB-1TB',
                'display': '6.8" Dynamic AMOLED 2X 120Hz',
                'camera': '200MP Main + 50MP Periscope + 12MP Ultra Wide + 10MP Telephoto',
                'battery': '5000 mAh',
                'weight': '232 g',
                'operating_system': 'Android 14 with One UI'
            },
            use_cases=[UseCase.GENERAL, UseCase.CREATIVE, UseCase.BUSINESS],
            pros=['Incredible camera system', 'S Pen integration', 'Beautiful display', 'Expandable storage'],
            cons=['Large and heavy', 'Expensive', 'Curved edges may not appeal to everyone'],
            rating=4.5,
            description='The Galaxy S24 Ultra is Samsung\'s flagship with an incredible camera system, S Pen, and stunning display.'
        )
        
        products['google_pixel_8_pro'] = Product(
            id='google_pixel_8_pro',
            name='Google Pixel 8 Pro',
            category=ProductCategory.SMARTPHONE,
            brand='Google',
            price_range=PriceRange.PREMIUM,
            specifications={
                'processor': 'Google Tensor G3',
                'ram': '12GB',
                'storage': '128GB-1TB',
                'display': '6.7" LTPO OLED 120Hz',
                'camera': '50MP Main + 48MP Ultra Wide + 48MP Telephoto',
                'battery': '5050 mAh',
                'weight': '213 g',
                'operating_system': 'Android 14 with Pixel UI'
            },
            use_cases=[UseCase.GENERAL, UseCase.CREATIVE, UseCase.BUSINESS],
            pros=['Amazing AI features', 'Excellent camera processing', 'Clean Android experience', 'Great software support'],
            cons=['Tensor G3 performance lag', 'Battery life could be better', 'Limited availability'],
            rating=4.3,
            description='The Pixel 8 Pro focuses on AI features and camera excellence, offering a clean Android experience with Google\'s smart features.'
        )
        
        # Tablets
        products['ipad_pro_m2'] = Product(
            id='ipad_pro_m2',
            name='iPad Pro M2',
            category=ProductCategory.TABLET,
            brand='Apple',
            price_range=PriceRange.PREMIUM,
            specifications={
                'processor': 'Apple M2',
                'ram': '8GB/16GB',
                'storage': '128GB-2TB',
                'display': '11" or 12.9" Liquid Retina XDR with ProMotion',
                'camera': '12MP Wide + 10MP Ultra Wide',
                'battery': '10 hours',
                'weight': '466 g (11") / 682 g (12.9")',
                'operating_system': 'iPadOS 17'
            },
            use_cases=[UseCase.CREATIVE, UseCase.BUSINESS, UseCase.STUDENT],
            pros=['Incredibly powerful', 'Amazing display', 'Great for creative work', 'Excellent accessory support'],
            cons=['Expensive', 'iPadOS limitations', 'Need accessories for full potential'],
            rating=4.6,
            description='The iPad Pro M2 is incredibly powerful with an amazing display, perfect for creative professionals and productivity.'
        )
        
        products['samsung_tab_s9_ultra'] = Product(
            id='samsung_tab_s9_ultra',
            name='Samsung Galaxy Tab S9 Ultra',
            category=ProductCategory.TABLET,
            brand='Samsung',
            price_range=PriceRange.PREMIUM,
            specifications={
                'processor': 'Snapdragon 8 Gen 2 for Galaxy',
                'ram': '12GB/16GB',
                'storage': '256GB-1TB',
                'display': '14.6" Dynamic AMOLED 2X 120Hz',
                'camera': '13MP Main + 6MP Ultra Wide',
                'battery': '11200 mAh',
                'weight': '732 g',
                'operating_system': 'Android 13 with One UI'
            },
            use_cases=[UseCase.CREATIVE, UseCase.BUSINESS, UseCase.STUDENT],
            pros=['Massive beautiful display', 'S Pen included', 'Great multitasking', 'Expandable storage'],
            cons=['Very large', 'Expensive', 'Android tablet app optimization'],
            rating=4.4,
            description='The Tab S9 Ultra features a massive 14.6" display with included S Pen, perfect for productivity and entertainment.'
        )
        
        return products
    
    def _initialize_specifications_guide(self) -> Dict[str, Dict[str, Any]]:
        """Initialize specifications explanation guide"""
        return {
            'laptop': {
                'processor': {
                    'description': 'The brain of the laptop that determines performance',
                    'options': {
                        'entry_level': ['Intel Core i3', 'AMD Ryzen 3', 'Apple M1'],
                        'mid_range': ['Intel Core i5', 'AMD Ryzen 5', 'Apple M2'],
                        'high_end': ['Intel Core i7', 'AMD Ryzen 7', 'Apple M2 Pro'],
                        'professional': ['Intel Core i9', 'AMD Ryzen 9', 'Apple M3 Max']
                    },
                    'recommendations': {
                        'general': 'Intel Core i5 or AMD Ryzen 5 is sufficient',
                        'gaming': 'Intel Core i7 or AMD Ryzen 7 recommended',
                        'creative': 'Apple M series or Intel Core i7+ recommended'
                    }
                },
                'ram': {
                    'description': 'Memory for running applications and multitasking',
                    'options': {
                        '8GB': 'Basic use, web browsing, office applications',
                        '16GB': 'Most users, multitasking, light creative work',
                        '32GB': 'Heavy multitasking, creative work, development',
                        '64GB+': 'Professional creative work, virtual machines'
                    }
                },
                'storage': {
                    'description': 'Where your files and applications are stored',
                    'types': {
                        'SSD': 'Fast, reliable, more expensive',
                        'HDD': 'Slower, larger capacity, cheaper'
                    },
                    'recommendations': {
                        '256GB': 'Basic use with cloud storage',
                        '512GB': 'Most users, good balance',
                        '1TB': 'Heavy users, creative work',
                        '2TB+': 'Professional work, large file storage'
                    }
                },
                'display': {
                    'description': 'The screen quality and size',
                    'types': {
                        'FHD': '1920x1080, good for most users',
                        'QHD': '2560x1440, sharper images',
                        '4K': '3840x2160, extremely sharp, best for creative work'
                    },
                    'features': {
                        'IPS': 'Better colors and viewing angles',
                        'OLED': 'Perfect blacks, vibrant colors',
                        'ProMotion': '120Hz refresh rate, smoother scrolling'
                    }
                }
            },
            'smartphone': {
                'camera': {
                    'description': 'Camera quality for photos and videos',
                    'megapixels': {
                        '12MP': 'Good for social media',
                        '48MP+': 'Detailed photos, good for cropping',
                        '108MP+': 'Extremely detailed, professional use'
                    },
                    'features': {
                        'optical_zoom': 'True zoom without quality loss',
                        'night_mode': 'Better low-light photos',
                        'portrait_mode': 'Depth of field effect',
                        'video_recording': '4K, 8K, slow motion'
                    }
                },
                'battery': {
                    'description': 'Battery capacity and charging',
                    'capacity': {
                        '3000-4000 mAh': 'Average battery life',
                        '4000-5000 mAh': 'Good battery life',
                        '5000+ mAh': 'Excellent battery life'
                    },
                    'charging': {
                        'fast_charging': 'Quick top-ups',
                        'wireless_charging': 'Convenient charging',
                        'reverse_charging': 'Charge other devices'
                    }
                }
            }
        }
    
    def _initialize_comparison_matrix(self) -> Dict[str, Dict[str, Any]]:
        """Initialize product comparison matrix"""
        return {
            'laptop_comparison': {
                'performance': ['macbook_pro_14', 'dell_xps_15', 'macbook_air_m2'],
                'portability': ['macbook_air_m2', 'macbook_pro_14', 'dell_xps_15'],
                'battery_life': ['macbook_air_m2', 'macbook_pro_14', 'dell_xps_15'],
                'display_quality': ['macbook_pro_14', 'dell_xps_15', 'macbook_air_m2'],
                'value_for_money': ['macbook_air_m2', 'dell_xps_15', 'macbook_pro_14']
            },
            'smartphone_comparison': {
                'camera_quality': ['samsung_s24_ultra', 'iphone_15_pro', 'google_pixel_8_pro'],
                'performance': ['iphone_15_pro', 'samsung_s24_ultra', 'google_pixel_8_pro'],
                'battery_life': ['samsung_s24_ultra', 'google_pixel_8_pro', 'iphone_15_pro'],
                'display_quality': ['samsung_s24_ultra', 'iphone_15_pro', 'google_pixel_8_pro'],
                'ecosystem': ['iphone_15_pro', 'samsung_s24_ultra', 'google_pixel_8_pro']
            }
        }
    
    def get_product_by_id(self, product_id: str) -> Optional[Product]:
        """Get product by ID"""
        return self.products.get(product_id)
    
    def get_products_by_category(self, category: ProductCategory) -> List[Product]:
        """Get all products in a category"""
        return [product for product in self.products.values() if product.category == category]
    
    def get_products_by_brand(self, brand: str) -> List[Product]:
        """Get all products by brand"""
        return [product for product in self.products.values() if product.brand.lower() == brand.lower()]
    
    def get_specification_guide(self, category: str, spec: str) -> Optional[Dict[str, Any]]:
        """Get specification guide for a category"""
        return self.specifications_guide.get(category, {}).get(spec)


class ProductRecommendationEngine:
    """Engine for generating product recommendations"""
    
    def __init__(self, products: Dict[str, Product]):
        self.products = products
        self.scoring_weights = {
            'use_case_match': 0.3,
            'price_match': 0.25,
            'brand_preference': 0.2,
            'feature_match': 0.15,
            'rating': 0.1
        }
    
    def get_recommendations(self, request: RecommendationRequest) -> List[Tuple[Product, float]]:
        """Get product recommendations based on request"""
        recommendations = []
        
        for product in self.products.values():
            if product.category != request.category:
                continue
            
            score = self._calculate_score(product, request)
            recommendations.append((product, score))
        
        # Sort by score (descending)
        recommendations.sort(key=lambda x: x[1], reverse=True)
        return recommendations
    
    def _calculate_score(self, product: Product, request: RecommendationRequest) -> float:
        """Calculate recommendation score for a product"""
        score = 0.0
        
        # Use case matching
        use_case_score = self._calculate_use_case_score(product, request.use_cases)
        score += use_case_score * self.scoring_weights['use_case_match']
        
        # Price range matching
        price_score = self._calculate_price_score(product, request.budget_range)
        score += price_score * self.scoring_weights['price_match']
        
        # Brand preference
        brand_score = self._calculate_brand_score(product, request.preferred_brands)
        score += brand_score * self.scoring_weights['brand_preference']
        
        # Feature matching
        feature_score = self._calculate_feature_score(product, request.required_features)
        score += feature_score * self.scoring_weights['feature_match']
        
        # Rating
        rating_score = product.rating / 5.0
        score += rating_score * self.scoring_weights['rating']
        
        return score
    
    def _calculate_use_case_score(self, product: Product, use_cases: List[UseCase]) -> float:
        """Calculate use case matching score"""
        if not use_cases:
            return 0.5
        
        matching_use_cases = set(product.use_cases) & set(use_cases)
        return len(matching_use_cases) / len(use_cases)
    
    def _calculate_price_score(self, product: Product, budget_range: Optional[Tuple[float, float]]) -> float:
        """Calculate price range matching score"""
        if not budget_range:
            return 0.5
        
        # For simplicity, use price range enum matching
        price_mapping = {
            PriceRange.BUDGET: (0, 600),
            PriceRange.MID_RANGE: (600, 1200),
            PriceRange.PREMIUM: (1200, 2000),
            PriceRange.LUXURY: (2000, float('inf'))
        }
        
        product_range = price_mapping.get(product.price_range, (0, float('inf')))
        
        # Check if price ranges overlap
        if product_range[0] <= budget_range[1] and product_range[1] >= budget_range[0]:
            return 1.0
        else:
            return 0.2
    
    def _calculate_brand_score(self, product: Product, preferred_brands: List[str]) -> float:
        """Calculate brand preference score"""
        if not preferred_brands:
            return 0.5
        
        if product.brand.lower() in [brand.lower() for brand in preferred_brands]:
            return 1.0
        else:
            return 0.3
    
    def _calculate_feature_score(self, product: Product, required_features: List[str]) -> float:
        """Calculate feature matching score"""
        if not required_features:
            return 0.5
        
        matching_features = 0
        for feature in required_features:
            if self._product_has_feature(product, feature):
                matching_features += 1
        
        return matching_features / len(required_features)
    
    def _product_has_feature(self, product: Product, feature: str) -> bool:
        """Check if product has a specific feature"""
        feature_lower = feature.lower()
        
        # Check in specifications
        for spec_key, spec_value in product.specifications.items():
            if feature_lower in str(spec_value).lower():
                return True
        
        # Check in pros
        for pro in product.pros:
            if feature_lower in pro.lower():
                return True
        
        # Check in description
        if feature_lower in product.description.lower():
            return True
        
        return False


class ProductAdvisor:
    """Main product advisor interface"""
    
    def __init__(self):
        self.knowledge_base = ProductKnowledgeBase()
        logger.info("Product Advisor initialized")
    
    def get_product_advice(self, user_input: str, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Get product advice based on user input and entities"""
        try:
            # Determine category from entities
            category = self._determine_category(entities)
            
            if category:
                return self._generate_category_advice(category, entities)
            else:
                return self._generate_general_advice(entities)
                
        except Exception as e:
            logger.error(f"Error getting product advice: {str(e)}")
            return self._generate_fallback_advice()
    
    def _determine_category(self, entities: Dict[str, Any]) -> Optional[ProductCategory]:
        """Determine product category from entities"""
        product_type = entities.get('product_type', [''])[0].lower()
        
        category_mapping = {
            'laptop': ProductCategory.LAPTOP,
            'phone': ProductCategory.SMARTPHONE,
            'smartphone': ProductCategory.SMARTPHONE,
            'tablet': ProductCategory.TABLET,
            'computer': ProductCategory.LAPTOP
        }
        
        return category_mapping.get(product_type)
    
    def _generate_category_advice(self, category: ProductCategory, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Generate category-specific advice"""
        products = self.knowledge_base.get_products_by_category(category)
        
        if not products:
            return self._generate_fallback_advice()
        
        # Generate overview
        advice = self._generate_category_overview(category, products)
        
        # Add specific product recommendations if brand mentioned
        if 'brand' in entities:
            brand_products = self.knowledge_base.get_products_by_brand(entities['brand'][0])
            if brand_products:
                advice += self._generate_brand_recommendations(brand_products)
        
        # Add price range advice if mentioned
        if 'price_range' in entities:
            advice += self._generate_price_range_advice(category, entities['price_range'][0])
        
        return {
            'advice': advice,
            'category': category.value,
            'products': [p.name for p in products],
            'follow_up_questions': self._generate_follow_up_questions(category, entities)
        }
    
    def _generate_category_overview(self, category: ProductCategory, products: List[Product]) -> str:
        """Generate category overview"""
        category_info = {
            ProductCategory.LAPTOP: {
                'description': 'Laptops are perfect for productivity, creativity, and entertainment on the go.',
                'key_considerations': ['Processor performance', 'RAM capacity', 'Storage type and size', 'Display quality', 'Battery life']
            },
            ProductCategory.SMARTPHONE: {
                'description': 'Smartphones keep you connected with powerful cameras, fast performance, and beautiful displays.',
                'key_considerations': ['Camera quality', 'Battery life', 'Display quality', 'Performance', 'Ecosystem integration']
            },
            ProductCategory.TABLET: {
                'description': 'Tablets offer the perfect balance between portability and productivity for media and work.',
                'key_considerations': ['Display size and quality', 'Performance', 'Accessory support', 'Operating system', 'Battery life']
            }
        }
        
        info = category_info.get(category, category_info[ProductCategory.LAPTOP])
        
        advice = f"{info['description']}\n\n"
        advice += f"**Key Considerations for {category.title()}s:**\n"
        for consideration in info['key_considerations']:
            advice += f"• {consideration}\n"
        
        advice += f"\n**Popular Options:**\n"
        for product in products[:3]:
            advice += f"• {product.name} - {product.description}\n"
        
        return advice
    
    def _generate_brand_recommendations(self, brand_products: List[Product]) -> str:
        """Generate brand-specific recommendations"""
        advice = f"\n**{brand_products[0].brand} Products:**\n"
        
        for product in brand_products:
            advice += f"• {product.name}: {product.description}\n"
            advice += f"  Rating: {product.rating}/5, Price Range: {product.price_range.value}\n"
        
        return advice
    
    def _generate_price_range_advice(self, category: ProductCategory, price_range: str) -> str:
        """Generate price range specific advice"""
        price_mapping = {
            'budget': 'under $600',
            'mid_range': '$600-$1200',
            'premium': '$1200-$2000',
            'luxury': 'above $2000'
        }
        
        actual_range = price_mapping.get(price_range.lower(), price_range)
        
        return f"\n**For {actual_range} budget:**\nFocus on getting the best value by prioritizing features that matter most to your use case."
    
    def _generate_general_advice(self, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Generate general product advice"""
        advice = """I'd be happy to help you find the perfect technology product! To give you the best recommendations, tell me about:

• What type of product you're looking for (laptop, phone, tablet)
• Your budget range
• What you'll use it for
• Any preferred brands or features

Here are the main categories I can help with:
• **Laptops** - For work, study, gaming, or creative projects
• **Smartphones** - Stay connected with great cameras and performance
• **Tablets** - Perfect balance of portability and productivity

What type of product interests you most?"""
        
        return {
            'advice': advice,
            'category': 'general',
            'follow_up_questions': [
                "What type of product are you looking for?",
                "What's your budget range?",
                "What will you use it for?",
                "Do you have any brand preferences?"
            ]
        }
    
    def _generate_follow_up_questions(self, category: ProductCategory, entities: Dict[str, Any]) -> List[str]:
        """Generate relevant follow-up questions"""
        base_questions = [
            "What's your budget range?",
            "What will you primarily use it for?",
            "Do you have any brand preferences?",
            "Any specific features you need?"
        ]
        
        # Remove questions already answered
        if 'price_range' in entities:
            base_questions = [q for q in base_questions if 'budget' not in q.lower()]
        
        if 'brand' in entities:
            base_questions = [q for q in base_questions if 'brand' not in q.lower()]
        
        return base_questions[:3]
    
    def _generate_fallback_advice(self) -> Dict[str, Any]:
        """Generate fallback advice"""
        return {
            'advice': "I'm here to help you find the perfect technology product! Whether you need a laptop, phone, or tablet, I can provide detailed recommendations based on your needs and budget.",
            'category': 'fallback',
            'follow_up_questions': ["What type of product are you looking for?", "How can I help you choose?"]
        }


# Factory function for easy instantiation
def create_product_advisor() -> ProductAdvisor:
    """Factory function to create product advisor"""
    return ProductAdvisor()


if __name__ == "__main__":
    # Test the product advisor
    advisor = create_product_advisor()
    
    test_inputs = [
        ({"product_type": ["laptop"]}, "Tell me about laptops"),
        ({"product_type": ["phone"], "brand": ["Apple"]}, "I want an iPhone"),
        ({"product_type": ["tablet"], "price_range": ["$600-$1200"]}, "Recommend a tablet")
    ]
    
    print("=== Product Advisor Test ===")
    for entities, user_input in test_inputs:
        result = advisor.get_product_advice(user_input, entities)
        print(f"Input: '{user_input}'")
        print(f"Entities: {entities}")
        print(f"Advice: {result['advice'][:200]}...")
        print(f"Category: {result['category']}")
        print("-" * 50)
