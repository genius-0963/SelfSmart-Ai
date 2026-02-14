"""
Intelligent AI Backend - Natural Language Processing Engine
Production-grade OOP implementation for understanding human language
"""

import re
import json
import logging
from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class IntentType(Enum):
    """Enumeration of different user intents"""
    GREETING = "greeting"
    HELP_REQUEST = "help_request"
    PRODUCT_INQUIRY = "product_inquiry"
    SPORTS_TOPIC = "sports_topic"
    GENERAL_QUESTION = "general_question"
    CONVERSATION = "conversation"
    UNKNOWN = "unknown"


@dataclass
class Intent:
    """Data class for intent recognition results"""
    intent_type: IntentType
    confidence: float
    entities: Dict[str, Any]
    context: Dict[str, Any]


@dataclass
class ConversationContext:
    """Data class for conversation context"""
    user_id: str
    session_id: str
    previous_intents: List[IntentType]
    entities_mentioned: Dict[str, Any]
    conversation_history: List[Dict[str, str]]
    timestamp: datetime


class IntentRecognizer(ABC):
    """Abstract base class for intent recognition"""
    
    @abstractmethod
    def recognize_intent(self, text: str, context: Optional[ConversationContext] = None) -> Intent:
        """Recognize user intent from text"""
        pass


class NLPEngine:
    """Core NLP Engine for text processing and analysis"""
    
    def __init__(self):
        self.stop_words = {
            'the', 'is', 'at', 'which', 'on', 'a', 'an', 'and', 'or', 'but',
            'in', 'with', 'to', 'for', 'of', 'as', 'by', 'that', 'this',
            'it', 'from', 'be', 'are', 'been', 'was', 'were', 'will', 'would',
            'can', 'could', 'should', 'may', 'might', 'must', 'shall', 'do',
            'does', 'did', 'have', 'has', 'had', 'having', 'i', 'you', 'he',
            'she', 'we', 'they', 'me', 'him', 'her', 'us', 'them', 'my', 'your',
            'his', 'its', 'our', 'their'
        }
        
    def preprocess_text(self, text: str) -> str:
        """Clean and preprocess text for analysis"""
        if not text:
            return ""
            
        # Convert to lowercase and remove special characters
        text = text.lower().strip()
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        
        return text
    
    def extract_keywords(self, text: str) -> List[str]:
        """Extract meaningful keywords from text"""
        processed_text = self.preprocess_text(text)
        words = processed_text.split()
        
        # Remove stop words and short words
        keywords = [
            word for word in words 
            if word not in self.stop_words and len(word) > 2
        ]
        
        return keywords
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts using keyword overlap"""
        keywords1 = set(self.extract_keywords(text1))
        keywords2 = set(self.extract_keywords(text2))
        
        if not keywords1 or not keywords2:
            return 0.0
            
        intersection = keywords1.intersection(keywords2)
        union = keywords1.union(keywords2)
        
        return len(intersection) / len(union) if union else 0.0


class RuleBasedIntentRecognizer(IntentRecognizer):
    """Rule-based intent recognition system"""
    
    def __init__(self):
        self.nlp_engine = NLPEngine()
        self.intent_patterns = self._initialize_intent_patterns()
        self.entity_extractors = self._initialize_entity_extractors()
        
    def _initialize_intent_patterns(self) -> Dict[IntentType, List[str]]:
        """Initialize patterns for different intents"""
        return {
            IntentType.GREETING: [
                r'\b(hi|hello|hey|good morning|good afternoon|good evening|greetings)\b',
                r'\b(how are you|how do you do|what\'s up)\b',
                r'\b(nice to meet you|pleased to meet you)\b'
            ],
            IntentType.HELP_REQUEST: [
                r'\b(help|assist|support|guide|how to|what can you do)\b',
                r'\b(need help|require assistance|looking for help)\b',
                r'\b(explain|show me|teach me|demonstrate)\b'
            ],
            IntentType.PRODUCT_INQUIRY: [
                r'\b(laptop|phone|tablet|computer|smartphone|iphone|android)\b',
                r'\b(buy|purchase|price|cost|recommend|suggest)\b',
                r'\b(features|specifications|review|comparison|best)\b',
                r'\b(choose|select|pick|which one|what is the best)\b'
            ],
            IntentType.SPORTS_TOPIC: [
                r'\b(football|soccer|basketball|tennis|cricket|baseball)\b',
                r'\b(game|match|team|player|score|goal|win|lose)\b',
                r'\b(championship|league|tournament|world cup|premier league)\b'
            ],
            IntentType.GENERAL_QUESTION: [
                r'\b(what|where|when|why|how|who|which)\b',
                r'\b(tell me about|explain|describe|define)\b',
                r'\?\s*$'  # Ends with question mark
            ]
        }
    
    def _initialize_entity_extractors(self) -> Dict[str, re.Pattern]:
        """Initialize entity extraction patterns"""
        return {
            'product_type': re.compile(r'\b(laptop|phone|tablet|computer|smartphone|iphone|android|pc|mac)\b', re.IGNORECASE),
            'price_range': re.compile(r'\b(\$?\d+\s*-\s*\$?\d+|\$?\d+\s*(to|and)\s*\$?\d+|under\s*\$?\d+|above\s*\$?\d+)\b', re.IGNORECASE),
            'brand': re.compile(r'\b(apple|samsung|dell|hp|lenovo|microsoft|sony|lg|google|oneplus)\b', re.IGNORECASE),
            'sport': re.compile(r'\b(football|soccer|basketball|tennis|cricket|baseball|golf|hockey)\b', re.IGNORECASE),
            'team': re.compile(r'\b(real madrid|barcelona|manchester united|liverpool|chelsea|arsenal|bayern munich)\b', re.IGNORECASE)
        }
    
    def recognize_intent(self, text: str, context: Optional[ConversationContext] = None) -> Intent:
        """Recognize intent from user input"""
        if not text:
            return Intent(IntentType.UNKNOWN, 0.0, {}, {})
        
        text = text.strip()
        best_intent = IntentType.UNKNOWN
        best_confidence = 0.0
        
        # Check each intent pattern
        for intent_type, patterns in self.intent_patterns.items():
            confidence = self._calculate_pattern_confidence(text, patterns)
            if confidence > best_confidence:
                best_confidence = confidence
                best_intent = intent_type
        
        # Extract entities
        entities = self._extract_entities(text)
        
        # Add context information
        context_info = self._analyze_context(text, context)
        
        return Intent(best_intent, best_confidence, entities, context_info)
    
    def _calculate_pattern_confidence(self, text: str, patterns: List[str]) -> float:
        """Calculate confidence score for intent patterns"""
        max_confidence = 0.0
        
        for pattern in patterns:
            try:
                if re.search(pattern, text, re.IGNORECASE):
                    # Simple confidence based on pattern match
                    confidence = 0.8
                    if pattern.endswith(r'\b'):
                        confidence += 0.1  # Boost for word boundary matches
                    max_confidence = max(max_confidence, confidence)
            except re.error:
                logger.debug(f"Skipping invalid pattern: {pattern[:50]}...")
                continue
        
        return max_confidence
    
    def _extract_entities(self, text: str) -> Dict[str, Any]:
        """Extract entities from user input"""
        entities = {}
        
        for entity_type, pattern in self.entity_extractors.items():
            matches = pattern.findall(text)
            if matches:
                entities[entity_type] = matches
        
        return entities
    
    def _analyze_context(self, text: str, context: Optional[ConversationContext]) -> Dict[str, Any]:
        """Analyze context for better understanding"""
        context_info = {}
        
        if context:
            # Check if this is a follow-up question
            context_info['is_follow_up'] = self._is_follow_up(text, context)
            context_info['previous_intent'] = context.previous_intents[-1] if context.previous_intents else None
            context_info['session_length'] = len(context.conversation_history)
        
        # Analyze text characteristics
        context_info['text_length'] = len(text)
        context_info['word_count'] = len(text.split())
        context_info['has_question_mark'] = '?' in text
        context_info['has_exclamation'] = '!' in text
        
        return context_info
    
    def _is_follow_up(self, text: str, context: ConversationContext) -> bool:
        """Determine if this is a follow-up question"""
        follow_up_indicators = [
            'what about', 'how about', 'and', 'also', 'what if',
            'tell me more', 'can you explain', 'why', 'when'
        ]
        
        text_lower = text.lower()
        return any(indicator in text_lower for indicator in follow_up_indicators)


class IntentRecognitionEngine:
    """Main engine for intent recognition with multiple strategies"""
    
    def __init__(self):
        self.rule_based_recognizer = RuleBasedIntentRecognizer()
        self.nlp_engine = NLPEngine()
        logger.info("Intent Recognition Engine initialized")
    
    def process_input(self, text: str, context: Optional[ConversationContext] = None) -> Intent:
        """Process user input and return recognized intent"""
        try:
            # Use rule-based recognition for now
            intent = self.rule_based_recognizer.recognize_intent(text, context)
            
            logger.info(f"Intent recognized: {intent.intent_type.value} (confidence: {intent.confidence})")
            return intent
            
        except Exception as e:
            logger.error(f"Error processing input: {str(e)}")
            return Intent(IntentType.UNKNOWN, 0.0, {}, {})
    
    def get_confidence_threshold(self) -> float:
        """Get minimum confidence threshold for intent recognition"""
        return 0.3
    
    def is_confident(self, intent: Intent) -> bool:
        """Check if intent recognition is confident enough"""
        return intent.confidence >= self.get_confidence_threshold()


# Factory function for easy instantiation
def create_intent_engine() -> IntentRecognitionEngine:
    """Factory function to create intent recognition engine"""
    return IntentRecognitionEngine()


if __name__ == "__main__":
    # Test the intent recognition system
    engine = create_intent_engine()
    
    test_inputs = [
        "Hi there!",
        "What can you help me with?",
        "Tell me about laptops",
        "Football is amazing",
        "How are you today?",
        "Help me choose a phone",
        "What is the best laptop for programming?"
    ]
    
    print("=== Intent Recognition Test ===")
    for test_input in test_inputs:
        intent = engine.process_input(test_input)
        print(f"Input: '{test_input}'")
        print(f"Intent: {intent.intent_type.value} (confidence: {intent.confidence:.2f})")
        print(f"Entities: {intent.entities}")
        print("-" * 50)
