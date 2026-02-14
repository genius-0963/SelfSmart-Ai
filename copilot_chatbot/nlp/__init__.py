"""
Intelligent AI Backend - NLP Package

Natural Language Processing components for advanced human-like conversation understanding.
"""

from .intent_recognition import (
    IntentType,
    Intent,
    ConversationContext,
    create_intent_engine
)

from .response_generation import (
    Response,
    create_response_generator
)

from .conversation_flow import (
    ConversationState,
    DialogueTurn,
    create_conversation_manager
)

from .sports_handler import (
    SportType,
    ConversationTopic,
    create_sports_handler
)

from .product_knowledge import (
    ProductCategory,
    PriceRange,
    UseCase,
    create_product_advisor
)

__all__ = [
    # Intent Recognition
    'IntentType',
    'Intent', 
    'ConversationContext',
    'create_intent_engine',
    
    # Response Generation
    'Response',
    'create_response_generator',
    
    # Conversation Flow
    'ConversationState',
    'DialogueTurn',
    'create_conversation_manager',
    
    # Sports Handler
    'SportType',
    'ConversationTopic',
    'create_sports_handler',
    
    # Product Knowledge
    'ProductCategory',
    'PriceRange',
    'UseCase',
    'create_product_advisor'
]
