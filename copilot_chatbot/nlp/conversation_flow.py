"""
Intelligent AI Backend - Conversation Flow Manager
Production-grade OOP implementation for managing conversation flow and follow-up questions
"""

import json
import logging
import uuid
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

from .intent_recognition import Intent, IntentType, ConversationContext
from .response_generation import Response
from .sports_handler import SportsContext, create_sports_handler
from .product_knowledge import create_product_advisor

logger = logging.getLogger(__name__)


class ConversationState(Enum):
    """Enumeration of conversation states"""
    INITIAL = "initial"
    GREETING = "greeting"
    INFORMATION_GATHERING = "information_gathering"
    DISCUSSION = "discussion"
    QUESTION_ANSWERING = "question_answering"
    FOLLOW_UP = "follow_up"
    CONCLUSION = "conclusion"


class DialogueTurn(Enum):
    """Enumeration of dialogue turns"""
    USER = "user"
    ASSISTANT = "assistant"


@dataclass
class DialogueMessage:
    """Data class for dialogue messages"""
    id: str
    turn: DialogueTurn
    content: str
    timestamp: datetime
    intent: Optional[Intent] = None
    response: Optional[Response] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConversationSession:
    """Data class for conversation sessions"""
    session_id: str
    user_id: str
    state: ConversationState
    messages: List[DialogueMessage]
    context: Dict[str, Any]
    entities_collected: Dict[str, Any]
    follow_up_queue: List[str]
    created_at: datetime
    last_activity: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


class ConversationFlowStrategy(ABC):
    """Abstract base class for conversation flow strategies"""
    
    @abstractmethod
    def determine_next_state(self, current_state: ConversationState, intent: Intent, 
                           context: Dict[str, Any]) -> ConversationState:
        """Determine the next conversation state"""
        pass
    
    @abstractmethod
    def generate_follow_up_questions(self, state: ConversationState, intent: Intent, 
                                   context: Dict[str, Any]) -> List[str]:
        """Generate follow-up questions for the current state"""
        pass


class DefaultConversationFlowStrategy(ConversationFlowStrategy):
    """Default conversation flow strategy"""
    
    def __init__(self):
        self.state_transitions = self._initialize_state_transitions()
        self.follow_up_templates = self._initialize_follow_up_templates()
    
    def _initialize_state_transitions(self) -> Dict[ConversationState, Dict[IntentType, ConversationState]]:
        """Initialize state transition rules"""
        return {
            ConversationState.INITIAL: {
                IntentType.GREETING: ConversationState.GREETING,
                IntentType.HELP_REQUEST: ConversationState.INFORMATION_GATHERING,
                IntentType.PRODUCT_INQUIRY: ConversationState.INFORMATION_GATHERING,
                IntentType.SPORTS_TOPIC: ConversationState.DISCUSSION,
                IntentType.GENERAL_QUESTION: ConversationState.QUESTION_ANSWERING,
                IntentType.CONVERSATION: ConversationState.DISCUSSION
            },
            ConversationState.GREETING: {
                IntentType.PRODUCT_INQUIRY: ConversationState.INFORMATION_GATHERING,
                IntentType.SPORTS_TOPIC: ConversationState.DISCUSSION,
                IntentType.GENERAL_QUESTION: ConversationState.QUESTION_ANSWERING,
                IntentType.CONVERSATION: ConversationState.DISCUSSION
            },
            ConversationState.INFORMATION_GATHERING: {
                IntentType.PRODUCT_INQUIRY: ConversationState.INFORMATION_GATHERING,
                IntentType.GENERAL_QUESTION: ConversationState.QUESTION_ANSWERING,
                IntentType.CONVERSATION: ConversationState.DISCUSSION
            },
            ConversationState.DISCUSSION: {
                IntentType.SPORTS_TOPIC: ConversationState.DISCUSSION,
                IntentType.PRODUCT_INQUIRY: ConversationState.INFORMATION_GATHERING,
                IntentType.GENERAL_QUESTION: ConversationState.QUESTION_ANSWERING,
                IntentType.CONVERSATION: ConversationState.DISCUSSION
            },
            ConversationState.QUESTION_ANSWERING: {
                IntentType.GENERAL_QUESTION: ConversationState.QUESTION_ANSWERING,
                IntentType.PRODUCT_INQUIRY: ConversationState.INFORMATION_GATHERING,
                IntentType.SPORTS_TOPIC: ConversationState.DISCUSSION,
                IntentType.CONVERSATION: ConversationState.DISCUSSION
            }
        }
    
    def _initialize_follow_up_templates(self) -> Dict[ConversationState, Dict[str, List[str]]]:
        """Initialize follow-up question templates"""
        return {
            ConversationState.INITIAL: {
                'default': [
                    "What would you like to know about?",
                    "How can I assist you today?",
                    "What topic interests you?"
                ]
            },
            ConversationState.GREETING: {
                'default': [
                    "What brings you here today?",
                    "What would you like to explore?",
                    "How can I help you?"
                ]
            },
            ConversationState.INFORMATION_GATHERING: {
                'product_inquiry': [
                    "What's your budget range?",
                    "What will you use it for?",
                    "Any preferred brands?",
                    "Specific features you need?"
                ],
                'default': [
                    "Could you provide more details?",
                    "What specifically are you looking for?",
                    "Any particular preferences?"
                ]
            },
            ConversationState.DISCUSSION: {
                'sports': [
                    "Which team do you support?",
                    "What's your favorite aspect of the game?",
                    "Any recent matches you want to discuss?",
                    "Players you admire?"
                ],
                'default': [
                    "What are your thoughts on this?",
                    "Would you like to explore another aspect?",
                    "What's your experience with this?"
                ]
            },
            ConversationState.QUESTION_ANSWERING: {
                'default': [
                    "Does that answer your question?",
                    "Would you like more details?",
                    "Any related questions?",
                    "What else would you like to know?"
                ]
            }
        }
    
    def determine_next_state(self, current_state: ConversationState, intent: Intent, 
                           context: Dict[str, Any]) -> ConversationState:
        """Determine the next conversation state"""
        
        # Get state transitions for current state
        state_transitions = self.state_transitions.get(current_state, {})
        
        # Get next state based on intent
        next_state = state_transitions.get(intent.intent_type, current_state)
        
        # Apply context-based modifications
        if context.get('is_follow_up'):
            if current_state == ConversationState.INFORMATION_GATHERING:
                next_state = ConversationState.INFORMATION_GATHERING
            elif current_state == ConversationState.DISCUSSION:
                next_state = ConversationState.DISCUSSION
        
        # Handle conversation depth
        message_count = context.get('message_count', 0)
        if message_count > 10:
            if next_state not in [ConversationState.CONCLUSION]:
                next_state = ConversationState.DISCUSSION
        
        return next_state
    
    def generate_follow_up_questions(self, state: ConversationState, intent: Intent, 
                                   context: Dict[str, Any]) -> List[str]:
        """Generate follow-up questions for the current state"""
        
        templates = self.follow_up_templates.get(state, {})
        
        # Select template based on intent
        if intent.intent_type == IntentType.PRODUCT_INQUIRY:
            questions = templates.get('product_inquiry', templates.get('default', []))
        elif intent.intent_type == IntentType.SPORTS_TOPIC:
            questions = templates.get('sports', templates.get('default', []))
        else:
            questions = templates.get('default', [])
        
        # Filter questions based on context
        filtered_questions = self._filter_questions_by_context(questions, context)
        
        # Return 2-3 questions
        return filtered_questions[:3]
    
    def _filter_questions_by_context(self, questions: List[str], context: Dict[str, Any]) -> List[str]:
        """Filter questions based on conversation context"""
        filtered = []
        
        entities = context.get('entities', {})
        
        for question in questions:
            # Skip budget question if price range already mentioned
            if 'budget' in question.lower() and 'price_range' in entities:
                continue
            
            # Skip brand question if brand already mentioned
            if 'brand' in question.lower() and 'brand' in entities:
                continue
            
            filtered.append(question)
        
        # If no questions left, return default questions
        if not filtered:
            return ["What else would you like to know?", "How can I help you further?"]
        
        return filtered


class ConversationFlowManager:
    """Main conversation flow manager"""
    
    def __init__(self):
        self.flow_strategy = DefaultConversationFlowStrategy()
        self.sessions: Dict[str, ConversationSession] = {}
        self.sports_handler = create_sports_handler()
        self.product_advisor = create_product_advisor()
        self.session_timeout = timedelta(hours=1)
        logger.info("Conversation Flow Manager initialized")
    
    def create_session(self, user_id: str) -> str:
        """Create a new conversation session"""
        session_id = str(uuid.uuid4())
        
        session = ConversationSession(
            session_id=session_id,
            user_id=user_id,
            state=ConversationState.INITIAL,
            messages=[],
            context={},
            entities_collected={},
            follow_up_queue=[],
            created_at=datetime.now(),
            last_activity=datetime.now(),
            metadata={'session_length': 0}
        )
        
        self.sessions[session_id] = session
        logger.info(f"Created new session {session_id} for user {user_id}")
        return session_id
    
    def get_session(self, session_id: str) -> Optional[ConversationSession]:
        """Get conversation session by ID"""
        session = self.sessions.get(session_id)
        
        if session:
            # Check if session has timed out
            if datetime.now() - session.last_activity > self.session_timeout:
                logger.info(f"Session {session_id} timed out")
                del self.sessions[session_id]
                return None
            
            session.last_activity = datetime.now()
        
        return session
    
    def process_message(self, session_id: str, user_message: str, intent: Intent, 
                       response: Response) -> Dict[str, Any]:
        """Process a user message and update conversation flow"""
        
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found or expired")
        
        try:
            # Create user message
            user_message_obj = DialogueMessage(
                id=str(uuid.uuid4()),
                turn=DialogueTurn.USER,
                content=user_message,
                timestamp=datetime.now(),
                intent=intent,
                metadata={'entities': intent.entities}
            )
            
            # Create assistant message
            assistant_message_obj = DialogueMessage(
                id=str(uuid.uuid4()),
                turn=DialogueTurn.ASSISTANT,
                content=response.text,
                timestamp=datetime.now(),
                response=response,
                metadata={'follow_up_questions': response.follow_up_questions}
            )
            
            # Add messages to session
            session.messages.append(user_message_obj)
            session.messages.append(assistant_message_obj)
            
            # Update entities collected
            self._update_entities_collected(session, intent.entities)
            
            # Update context
            self._update_context(session, intent, response)
            
            # Determine next state
            next_state = self.flow_strategy.determine_next_state(
                session.state, intent, session.context
            )
            session.state = next_state
            
            # Generate follow-up questions
            follow_up_questions = self.flow_strategy.generate_follow_up_questions(
                next_state, intent, session.context
            )
            session.follow_up_queue = follow_up_questions
            
            # Update metadata
            session.metadata['session_length'] = len(session.messages)
            session.last_activity = datetime.now()
            
            # Handle specialized conversations
            specialized_response = self._handle_specialized_conversations(
                session, user_message, intent
            )
            
            logger.info(f"Processed message in session {session_id}, new state: {next_state.value}")
            
            return {
                'session_id': session_id,
                'state': next_state.value,
                'response': response.text,
                'follow_up_questions': follow_up_questions,
                'specialized_response': specialized_response,
                'conversation_history': self._get_conversation_summary(session),
                'entities_collected': session.entities_collected
            }
            
        except Exception as e:
            logger.error(f"Error processing message in session {session_id}: {str(e)}")
            return self._generate_error_response(session_id)
    
    def _update_entities_collected(self, session: ConversationSession, new_entities: Dict[str, Any]):
        """Update collected entities in session"""
        for entity_type, entity_values in new_entities.items():
            if entity_type not in session.entities_collected:
                session.entities_collected[entity_type] = []
            
            # Add new entity values (avoid duplicates)
            for value in entity_values:
                if value not in session.entities_collected[entity_type]:
                    session.entities_collected[entity_type].append(value)
    
    def _update_context(self, session: ConversationSession, intent: Intent, response: Response):
        """Update conversation context"""
        session.context.update({
            'last_intent': intent.intent_type.value,
            'last_intent_confidence': intent.confidence,
            'message_count': len(session.messages),
            'is_follow_up': intent.context.get('is_follow_up', False),
            'has_question_mark': intent.context.get('has_question_mark', False),
            'conversation_depth': len([m for m in session.messages if m.turn == DialogueTurn.USER])
        })
        
        # Add response metadata
        session.context['last_response_strategy'] = response.metadata.get('strategy', 'unknown')
    
    def _handle_specialized_conversations(self, session: ConversationSession, 
                                        user_message: str, intent: Intent) -> Optional[Dict[str, Any]]:
        """Handle specialized conversation types"""
        
        if intent.intent_type == IntentType.SPORTS_TOPIC:
            sports_context = SportsContext(
                sport_type=None,  # Will be determined by handler
                topic=None,
                entities=intent.entities,
                user_preferences={},
                conversation_history=[{'user': msg.content, 'assistant': msg.content} 
                                     for msg in session.messages[-4:]]  # Last 4 messages
            )
            
            return self.sports_handler.handle_sports_conversation(user_message, sports_context)
        
        elif intent.intent_type == IntentType.PRODUCT_INQUIRY:
            return self.product_advisor.get_product_advice(user_message, intent.entities)
        
        return None
    
    def _get_conversation_summary(self, session: ConversationSession) -> Dict[str, Any]:
        """Get conversation summary"""
        user_messages = [m for m in session.messages if m.turn == DialogueTurn.USER]
        assistant_messages = [m for m in session.messages if m.turn == DialogueTurn.ASSISTANT]
        
        return {
            'total_messages': len(session.messages),
            'user_messages': len(user_messages),
            'assistant_messages': len(assistant_messages),
            'current_state': session.state.value,
            'entities_collected': session.entities_collected,
            'duration_minutes': (datetime.now() - session.created_at).total_seconds() / 60
        }
    
    def _generate_error_response(self, session_id: str) -> Dict[str, Any]:
        """Generate error response"""
        return {
            'session_id': session_id,
            'state': 'error',
            'response': "I'm having trouble processing that. Could you please rephrase your message?",
            'follow_up_questions': ["What would you like to discuss?", "How can I help you?"],
            'error': True
        }
    
    def get_conversation_history(self, session_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get conversation history for a session"""
        session = self.get_session(session_id)
        if not session:
            return []
        
        messages = session.messages[-limit:] if limit > 0 else session.messages
        
        return [
            {
                'id': msg.id,
                'turn': msg.turn.value,
                'content': msg.content,
                'timestamp': msg.timestamp.isoformat(),
                'intent': msg.intent.intent_type.value if msg.intent else None,
                'metadata': msg.metadata
            }
            for msg in messages
        ]
    
    def clear_session(self, session_id: str) -> bool:
        """Clear a conversation session"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"Cleared session {session_id}")
            return True
        return False
    
    def get_active_sessions_count(self) -> int:
        """Get count of active sessions"""
        return len(self.sessions)
    
    def cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        current_time = datetime.now()
        expired_sessions = [
            session_id for session_id, session in self.sessions.items()
            if current_time - session.last_activity > self.session_timeout
        ]
        
        for session_id in expired_sessions:
            del self.sessions[session_id]
            logger.info(f"Cleaned up expired session {session_id}")
        
        return len(expired_sessions)


class FollowUpQuestionManager:
    """Manager for follow-up questions and conversation continuity"""
    
    def __init__(self):
        self.question_templates = self._initialize_question_templates()
        self.context_analyzers = self._initialize_context_analyzers()
    
    def _initialize_question_templates(self) -> Dict[str, List[str]]:
        """Initialize follow-up question templates"""
        return {
            'engagement': [
                "What are your thoughts on that?",
                "How does that sound to you?",
                "What's your take on this?",
                "Does that resonate with you?"
            ],
            'clarification': [
                "Could you tell me more about that?",
                "What specifically do you mean?",
                "Can you elaborate on that?",
                "What aspect interests you most?"
            ],
            'continuation': [
                "What would you like to explore next?",
                "Is there anything else you'd like to know?",
                "What other questions do you have?",
                "How else can I assist you?"
            ],
            'personalization': [
                "Based on what you've told me, I think you might also be interested in...",
                "Given your preferences, have you considered...",
                "That reminds me, you might also want to know about...",
                "Since you mentioned that, you might find this helpful..."
            ]
        }
    
    def _initialize_context_analyzers(self) -> Dict[str, callable]:
        """Initialize context analyzers for question selection"""
        return {
            'entity_count': lambda ctx: len(ctx.get('entities', {})),
            'conversation_depth': lambda ctx: ctx.get('conversation_depth', 0),
            'has_questions': lambda ctx: ctx.get('has_question_mark', False),
            'is_follow_up': lambda ctx: ctx.get('is_follow_up', False)
        }
    
    def select_best_follow_up(self, available_questions: List[str], context: Dict[str, Any]) -> str:
        """Select the best follow-up question based on context"""
        
        if not available_questions:
            return "What else would you like to know?"
        
        # Analyze context
        entity_count = self.context_analyzers['entity_count'](context)
        conversation_depth = self.context_analyzers['conversation_depth'](context)
        has_questions = self.context_analyzers['has_questions'](context)
        is_follow_up = self.context_analyzers['is_follow_up'](context)
        
        # Select question based on context
        if is_follow_up and entity_count < 2:
            # Need more information
            clarification_questions = self.question_templates['clarification']
            return clarification_questions[0] if clarification_questions else available_questions[0]
        
        elif conversation_depth > 5:
            # Deep conversation, offer continuation
            continuation_questions = self.question_templates['continuation']
            return continuation_questions[0] if continuation_questions else available_questions[0]
        
        elif has_questions:
            # User asked questions, engage with their thoughts
            engagement_questions = self.question_templates['engagement']
            return engagement_questions[0] if engagement_questions else available_questions[0]
        
        else:
            # Default to first available question
            return available_questions[0]


# Factory function for easy instantiation
def create_conversation_manager() -> ConversationFlowManager:
    """Factory function to create conversation flow manager"""
    return ConversationFlowManager()


if __name__ == "__main__":
    # Test the conversation flow manager
    manager = create_conversation_manager()
    
    # Create a test session
    session_id = manager.create_session("test_user")
    print(f"Created session: {session_id}")
    
    # Simulate a conversation
    from .intent_recognition import create_intent_engine, IntentType
    from .response_generation import create_response_generator
    
    intent_engine = create_intent_engine()
    response_generator = create_response_generator()
    
    test_conversation = [
        "Hi there!",
        "I want to buy a laptop",
        "What's the best laptop for programming?",
        "Tell me about football"
    ]
    
    print("=== Conversation Flow Test ===")
    for message in test_conversation:
        intent = intent_engine.process_input(message)
        response = response_generator.generate_response(intent)
        
        result = manager.process_message(session_id, message, intent, response)
        
        print(f"User: {message}")
        print(f"Intent: {intent.intent_type.value}")
        print(f"State: {result['state']}")
        print(f"Response: {result['response'][:100]}...")
        print(f"Follow-up: {result['follow_up_questions']}")
        print("-" * 50)
