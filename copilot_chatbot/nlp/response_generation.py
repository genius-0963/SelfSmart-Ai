"""
Intelligent AI Backend - Context Analysis and Response Generation
Production-grade OOP implementation for intelligent responses
"""

import json
import random
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

from .intent_recognition import Intent, IntentType, ConversationContext

logger = logging.getLogger(__name__)


@dataclass
class Response:
    """Data class for generated responses"""
    text: str
    confidence: float
    intent_type: IntentType
    follow_up_questions: List[str]
    metadata: Dict[str, Any]


class ResponseStrategy(ABC):
    """Abstract base class for response generation strategies"""
    
    @abstractmethod
    def generate_response(self, intent: Intent, context: Optional[ConversationContext] = None) -> Response:
        """Generate response based on intent and context"""
        pass


class GreetingResponseStrategy(ResponseStrategy):
    """Strategy for generating greeting responses"""
    
    def __init__(self):
        self.greetings = [
            "Hello! I'm your intelligent assistant. How can I help you today?",
            "Hi there! I'm excited to assist you. What would you like to know?",
            "Good day! I'm here to help with any questions you have.",
            "Greetings! I'm your AI assistant. What can I do for you?",
            "Hey! I'm ready to help. What's on your mind?"
        ]
        
        self.follow_up_questions = [
            "What would you like to know about?",
            "How can I assist you today?",
            "What topic interests you?",
            "Do you have any specific questions?"
        ]
    
    def generate_response(self, intent: Intent, context: Optional[ConversationContext] = None) -> Response:
        """Generate friendly greeting response"""
        base_greeting = random.choice(self.greetings)
        
        # Add context-aware variation
        if context and context.session_length > 1:
            base_greeting = "Welcome back! " + base_greeting.lower()
        
        follow_up = random.sample(self.follow_up_questions, min(2, len(self.follow_up_questions)))
        
        return Response(
            text=base_greeting,
            confidence=0.9,
            intent_type=IntentType.GREETING,
            follow_up_questions=follow_up,
            metadata={"strategy": "greeting", "personalized": context is not None}
        )


class HelpResponseStrategy(ResponseStrategy):
    """Strategy for generating help responses"""
    
    def __init__(self):
        self.capabilities = [
            "I can help you with product recommendations and comparisons",
            "I can discuss sports topics, especially football",
            "I can answer general questions and provide information",
            "I can engage in natural conversation on various topics",
            "I can help you choose the right technology products"
        ]
        
        self.examples = [
            "Try asking: 'Tell me about laptops'",
            "Try asking: 'What's the best phone under $500?'",
            "Try asking: 'Let's discuss football'",
            "Try asking: 'Help me choose a tablet'"
        ]
    
    def generate_response(self, intent: Intent, context: Optional[ConversationContext] = None) -> Response:
        """Generate helpful response explaining capabilities"""
        capabilities_text = "\n".join(f"• {cap}" for cap in self.capabilities)
        example_text = "\n".join(f"• {ex}" for ex in random.sample(self.examples, 2))
        
        response_text = f"""I'm your intelligent AI assistant! Here's what I can do:

{capabilities_text}

Here are some examples to get you started:
{example_text}

What would you like to explore?"""
        
        follow_up = [
            "What topic interests you most?",
            "Do you need help with something specific?",
            "Would you like product recommendations?"
        ]
        
        return Response(
            text=response_text,
            confidence=0.95,
            intent_type=IntentType.HELP_REQUEST,
            follow_up_questions=follow_up,
            metadata={"strategy": "help", "capabilities_count": len(self.capabilities)}
        )


class ProductInquiryResponseStrategy(ResponseStrategy):
    """Strategy for handling product inquiries"""
    
    def __init__(self):
        self.product_knowledge = self._initialize_product_knowledge()
        self.recommendation_questions = [
            "What's your budget range?",
            "What will you use it for primarily?",
            "Do you have any brand preferences?",
            "Any specific features you need?"
        ]
    
    def _initialize_product_knowledge(self) -> Dict[str, Any]:
        """Initialize product knowledge base"""
        return {
            'laptop': {
                'types': ['ultrabook', 'gaming', 'business', 'student', 'creative'],
                'key_features': ['processor', 'ram', 'storage', 'display', 'battery'],
                'brands': ['Apple', 'Dell', 'HP', 'Lenovo', 'Microsoft', 'ASUS'],
                'price_ranges': {
                    'budget': 'under $600',
                    'mid_range': '$600-$1200',
                    'premium': '$1200-$2000',
                    'luxury': 'above $2000'
                }
            },
            'phone': {
                'types': ['flagship', 'mid_range', 'budget', 'gaming', 'camera_focused'],
                'key_features': ['camera', 'battery', 'display', 'processor', 'storage'],
                'brands': ['Apple', 'Samsung', 'Google', 'OnePlus', 'Xiaomi'],
                'price_ranges': {
                    'budget': 'under $300',
                    'mid_range': '$300-$700',
                    'premium': '$700-$1000',
                    'luxury': 'above $1000'
                }
            },
            'tablet': {
                'types': ['productivity', 'entertainment', 'creative', 'budget'],
                'key_features': ['display', 'processor', 'storage', 'stylus_support', 'battery'],
                'brands': ['Apple', 'Samsung', 'Microsoft', 'Amazon', 'Lenovo'],
                'price_ranges': {
                    'budget': 'under $250',
                    'mid_range': '$250-$600',
                    'premium': '$600-$1000',
                    'luxury': 'above $1000'
                }
            }
        }
    
    def generate_response(self, intent: Intent, context: Optional[ConversationContext] = None) -> Response:
        """Generate product inquiry response"""
        entities = intent.entities
        product_type = entities.get('product_type', ['product'])[0]
        
        # Get product information
        product_info = self.product_knowledge.get(product_type.lower(), {})
        
        if product_info:
            response_text = self._generate_product_info_response(product_type, product_info, entities)
        else:
            response_text = self._generate_general_product_response(entities)
        
        # Select relevant follow-up questions
        follow_up = self._select_relevant_follow_up(entities)
        
        return Response(
            text=response_text,
            confidence=0.85,
            intent_type=IntentType.PRODUCT_INQUIRY,
            follow_up_questions=follow_up,
            metadata={"strategy": "product_inquiry", "product_type": product_type}
        )
    
    def _generate_product_info_response(self, product_type: str, product_info: Dict, entities: Dict) -> str:
        """Generate detailed product information response"""
        types = product_info.get('types', [])
        features = product_info.get('key_features', [])
        brands = product_info.get('brands', [])
        
        response = f"Great choice looking at {product_type}s! Let me help you understand the options:\n\n"
        
        # Types overview
        if types:
            response += f"**Types of {product_type}s:**\n"
            for ptype in types[:4]:
                response += f"• {ptype.replace('_', ' ').title()}\n"
            response += "\n"
        
        # Key features to consider
        if features:
            response += f"**Key Features to Consider:**\n"
            for feature in features[:5]:
                response += f"• {feature.replace('_', ' ').title()}\n"
            response += "\n"
        
        # Popular brands
        if brands:
            response += f"**Popular Brands:**\n"
            response += f"• {', '.join(brands[:5])}\n\n"
        
        response += "To give you the best recommendation, I'd love to know more about your needs!"
        
        return response
    
    def _generate_general_product_response(self, entities: Dict) -> str:
        """Generate general product recommendation response"""
        return """I'd be happy to help you find the perfect product! Whether you're looking for a laptop, phone, tablet, or any other technology device, I can guide you through the options.

To give you the best recommendations, tell me about:
• Your budget range
• What you'll use it for
• Any preferred features
• Brand preferences if you have them

What specific type of product are you interested in?"""
    
    def _select_relevant_follow_up(self, entities: Dict) -> List[str]:
        """Select relevant follow-up questions based on entities"""
        questions = self.recommendation_questions.copy()
        
        # If price range already mentioned, remove that question
        if 'price_range' in entities:
            questions = [q for q in questions if 'budget' not in q.lower()]
        
        # If brand mentioned, remove brand question
        if 'brand' in entities:
            questions = [q for q in questions if 'brand' not in q.lower()]
        
        return random.sample(questions, min(3, len(questions)))


class SportsResponseStrategy(ResponseStrategy):
    """Strategy for handling sports conversations"""
    
    def __init__(self):
        self.sports_knowledge = self._initialize_sports_knowledge()
        self.football_topics = [
            "premier league standings",
            "champions league",
            "world cup",
            "player transfers",
            "match predictions",
            "team performance"
        ]
    
    def _initialize_sports_knowledge(self) -> Dict[str, Any]:
        """Initialize sports knowledge base"""
        return {
            'football': {
                'popular_leagues': ['Premier League', 'La Liga', 'Serie A', 'Bundesliga', 'Ligue 1'],
                'top_teams': ['Real Madrid', 'Barcelona', 'Manchester City', 'Liverpool', 'Bayern Munich'],
                'key_players': ['Messi', 'Ronaldo', 'Mbappé', 'Haaland', 'De Bruyne'],
                'tournaments': ['World Cup', 'Champions League', 'Euro Championship', 'Copa América'],
                'topics': ['transfers', 'injuries', 'formations', 'tactics', 'youth development']
            },
            'basketball': {
                'popular_leagues': ['NBA', 'EuroLeague', 'CBA'],
                'top_teams': ['Lakers', 'Warriors', 'Celtics', 'Heat', 'Nets'],
                'key_players': ['LeBron', 'Curry', 'Durant', 'Giannis', 'Jokić']
            }
        }
    
    def generate_response(self, intent: Intent, context: Optional[ConversationContext] = None) -> Response:
        """Generate sports conversation response"""
        entities = intent.entities
        sport = entities.get('sport', ['football'])[0].lower()
        
        if sport == 'football' or sport == 'soccer':
            response_text = self._generate_football_response(entities)
        else:
            response_text = self._generate_general_sports_response(sport, entities)
        
        follow_up = [
            "Which team do you support?",
            "What's your favorite tournament?",
            "Do you follow any specific players?",
            "What aspect of the game interests you most?"
        ]
        
        return Response(
            text=response_text,
            confidence=0.8,
            intent_type=IntentType.SPORTS_TOPIC,
            follow_up_questions=follow_up,
            metadata={"strategy": "sports", "sport": sport}
        )
    
    def _generate_football_response(self, entities: Dict) -> str:
        """Generate football-specific response"""
        team = entities.get('team', [None])[0]
        
        if team:
            return f"Great choice supporting {team}! Football is such an amazing sport. The tactical depth, skill level, and passion make it the world's most popular game.\n\nI can discuss:\n• Match analysis and predictions\n• Player performances and transfers\n• Tactical formations and strategies\n• League standings and tournaments\n• Historical moments and records\n\nWhat aspect of football would you like to explore?"
        else:
            return """Football is absolutely incredible! The beautiful game combines athleticism, strategy, and pure passion like nothing else.\n\nI love talking about:\n• Premier League, La Liga, Champions League\n• Top players like Messi, Ronaldo, Mbappé\n• Tactical innovations and formations\n• Transfer rumors and market analysis\n• International tournaments\n\nWho's your favorite team, or what aspect of football interests you most?"""
    
    def _generate_general_sports_response(self, sport: str, entities: Dict) -> str:
        """Generate general sports response"""
        return f"{sport.title()} is a fantastic sport! The combination of skill, strategy, and athleticism makes it so exciting to follow and discuss.\n\nI'd love to hear your thoughts on recent games, players, or tournaments. What aspects of {sport} do you enjoy most?"


class ConversationResponseStrategy(ResponseStrategy):
    """Strategy for general conversation"""
    
    def __init__(self):
        self.conversation_responses = [
            "That's interesting! Tell me more about what you're thinking.",
            "I'd love to hear your perspective on that.",
            "That's a great point. What else is on your mind?",
            "Thanks for sharing! How does that make you feel?",
            "I'm here to listen. What would you like to discuss next?"
        ]
    
    def generate_response(self, intent: Intent, context: Optional[ConversationContext] = None) -> Response:
        """Generate conversational response"""
        base_response = random.choice(self.conversation_responses)
        
        # Add context awareness
        if context and context.session_length > 3:
            base_response = "I'm really enjoying our conversation! " + base_response.lower()
        
        follow_up = [
            "What's on your mind?",
            "How are you feeling today?",
            "Anything exciting happening?",
            "Want to explore a new topic?"
        ]
        
        return Response(
            text=base_response,
            confidence=0.7,
            intent_type=IntentType.CONVERSATION,
            follow_up_questions=follow_up,
            metadata={"strategy": "conversation", "contextual": context is not None}
        )


class ResponseGenerator:
    """Main response generation engine"""
    
    def __init__(self):
        self.strategies = {
            IntentType.GREETING: GreetingResponseStrategy(),
            IntentType.HELP_REQUEST: HelpResponseStrategy(),
            IntentType.PRODUCT_INQUIRY: ProductInquiryResponseStrategy(),
            IntentType.SPORTS_TOPIC: SportsResponseStrategy(),
            IntentType.CONVERSATION: ConversationResponseStrategy()
        }
        self.fallback_strategy = ConversationResponseStrategy()
        logger.info("Response Generator initialized with all strategies")
    
    def generate_response(self, intent: Intent, context: Optional[ConversationContext] = None) -> Response:
        """Generate appropriate response based on intent"""
        try:
            strategy = self.strategies.get(intent.intent_type, self.fallback_strategy)
            response = strategy.generate_response(intent, context)
            
            logger.info(f"Generated response for {intent.intent_type.value} (confidence: {response.confidence})")
            return response
            
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return self._generate_fallback_response()
    
    def _generate_fallback_response(self) -> Response:
        """Generate fallback response for errors"""
        return Response(
            text="I'm here to help! Could you please rephrase that or let me know what you'd like to discuss?",
            confidence=0.5,
            intent_type=IntentType.UNKNOWN,
            follow_up_questions=["What would you like to know?", "How can I assist you?"],
            metadata={"strategy": "fallback", "error": True}
        )


# Factory function for easy instantiation
def create_response_generator() -> ResponseGenerator:
    """Factory function to create response generator"""
    return ResponseGenerator()


if __name__ == "__main__":
    # Test the response generation system
    from .intent_recognition import create_intent_engine
    
    intent_engine = create_intent_engine()
    response_generator = create_response_generator()
    
    test_inputs = [
        "Hi there!",
        "What can you help me with?",
        "Tell me about laptops",
        "Football is amazing",
        "How are you today?"
    ]
    
    print("=== Response Generation Test ===")
    for test_input in test_inputs:
        intent = intent_engine.process_input(test_input)
        response = response_generator.generate_response(intent)
        
        print(f"Input: '{test_input}'")
        print(f"Intent: {intent.intent_type.value}")
        print(f"Response: {response.text}")
        print(f"Follow-up: {response.follow_up_questions}")
        print("-" * 50)
