"""
SmartShelf AI - Enhanced Chat Service
Production-ready chat processing with caching and optimization
"""

import asyncio
import time
import logging
from typing import Dict, List, Optional, Any
from fastapi import HTTPException

from core.config import settings
from services.cache_service import cache_service
from services.metrics_service import metrics_service

logger = logging.getLogger(__name__)

class ChatService:
    """Enhanced chat service with performance optimizations"""
    
    def __init__(self):
        self.conversation_manager = None
        self.intent_engine = None
        self.response_generator = None
        
        # Initialize components safely
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize NLP components with error handling"""
        try:
            # Import and initialize components
            from nlp.conversation_flow import create_conversation_manager
            from nlp.intent_recognition import create_intent_engine
            from nlp.response_generation import create_response_generator
            
            self.conversation_manager = create_conversation_manager()
            self.intent_engine = create_intent_engine()
            self.response_generator = create_response_generator()
            
            logger.info("Chat service components initialized successfully")
            
        except ImportError as e:
            logger.warning(f"Could not import NLP components: {e}")
            # Set up mock components for fallback
            self._setup_mock_components()
    
    def _setup_mock_components(self):
        """Set up mock components for graceful degradation"""
        class MockConversationManager:
            def create_session(self, user_id):
                return f"mock_session_{int(time.time())}"
            
            def get_session(self, session_id):
                return None
            
            def process_message(self, session_id, message, intent, response):
                return {
                    'state': 'active',
                    'conversation_history': {'total_messages': 1}
                }
        
        class MockIntentEngine:
            def process_input(self, message, context=None):
                class MockIntent:
                    intent_type = type('IntentType', (), {'value': 'general'})()
                    confidence = 0.8
                    entities = {}
                
                return MockIntent()
        
        class MockResponseGenerator:
            def generate_response(self, intent):
                class MockResponse:
                    text = "I'm a fallback response. The advanced AI components are not available."
                    follow_up_questions = []
                    metadata = {'strategy': 'fallback'}
                
                return MockResponse()
        
        self.conversation_manager = MockConversationManager()
        self.intent_engine = MockIntentEngine()
        self.response_generator = MockResponseGenerator()
    
    async def process_message(
        self, 
        message: str, 
        session_id: Optional[str] = None,
        user_id: str = "anonymous",
        context: Dict[str, Any] = None,
        include_products: bool = False
    ) -> Dict[str, Any]:
        """Process chat message with comprehensive optimizations"""
        start_time = time.time()
        
        try:
            # Input validation
            if not message or not message.strip():
                raise HTTPException(status_code=400, detail="Message cannot be empty")
            
            message = message.strip()
            if len(message) > 10000:  # 10k character limit
                raise HTTPException(status_code=400, detail="Message too long")
            
            # Check cache for similar queries
            cache_key = f"chat:{hash(message)}:{session_id}:{include_products}"
            cached_response = await cache_service.get(cache_key)
            
            if cached_response:
                logger.info(f"Cache hit for query: {message[:50]}...")
                metrics_service.record_request("/chat", "POST", time.time() - start_time, 200, user_id)
                return cached_response
            
            # Get or create session
            if not session_id:
                session_id = self.conversation_manager.create_session(user_id)
            else:
                # Validate session exists
                session = self.conversation_manager.get_session(session_id)
                if not session:
                    session_id = self.conversation_manager.create_session(user_id)
            
            # Process intent with timeout
            try:
                intent = await asyncio.wait_for(
                    self._process_intent_async(message, context or {}),
                    timeout=settings.request_timeout
                )
            except asyncio.TimeoutError:
                logger.error(f"Intent processing timeout for: {message[:50]}...")
                raise HTTPException(status_code=408, detail="Intent processing timeout")
            
            # Generate response with timeout
            try:
                response = await asyncio.wait_for(
                    self._generate_response_async(intent),
                    timeout=settings.request_timeout
                )
            except asyncio.TimeoutError:
                logger.error(f"Response generation timeout for: {message[:50]}...")
                raise HTTPException(status_code=408, detail="Response generation timeout")
            
            # Process conversation
            conversation_result = await self._process_conversation_async(
                session_id, message, intent, response
            )
            
            # Handle product suggestions if requested
            product_suggestions = []
            if include_products:
                product_suggestions = await self._get_product_suggestions(message)
            
            # Build final response
            result = {
                "response": response.text,
                "session_id": session_id,
                "intent": intent.intent_type.value,
                "confidence": intent.confidence,
                "follow_up_questions": response.follow_up_questions,
                "entities": intent.entities,
                "conversation_state": conversation_result.get('state', 'active'),
                "timestamp": time.time(),
                "product_suggestions": product_suggestions,
                "metadata": {
                    "strategy": response.metadata.get('strategy', 'unknown'),
                    "response_time_ms": (time.time() - start_time) * 1000,
                    "cached": False,
                    "include_products": include_products
                }
            }
            
            # Cache the response (shorter TTL for chat responses)
            await cache_service.set(cache_key, result, ttl=300)  # 5 minutes cache
            
            # Record metrics
            response_time = time.time() - start_time
            metrics_service.record_request("/chat", "POST", response_time, 200, user_id, intent.intent_type.value)
            
            return result
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            metrics_service.record_request("/chat", "POST", time.time() - start_time, 500, user_id)
            raise HTTPException(status_code=500, detail="Internal server error")
    
    async def _process_intent_async(self, message: str, context: Dict[str, Any]):
        """Async wrapper for intent processing"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, 
            self.intent_engine.process_input, 
            message, 
            context
        )
    
    async def _generate_response_async(self, intent):
        """Async wrapper for response generation"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, 
            self.response_generator.generate_response, 
            intent
        )
    
    async def _process_conversation_async(self, session_id: str, message: str, intent, response):
        """Async wrapper for conversation processing"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, 
            self.conversation_manager.process_message, 
            session_id, 
            message, 
            intent, 
            response
        )
    
    async def _get_product_suggestions(self, message: str) -> List[Dict[str, Any]]:
        """Get product suggestions for the message"""
        try:
            # Import here to avoid circular dependencies
            from integrations.amazon_scraper import amazon_scraper
            
            # Search for products based on message
            products = await amazon_scraper.search_products(message, limit=5)
            
            suggestions = []
            for product in products[:3]:  # Top 3 suggestions
                suggestions.append({
                    "asin": product.asin,
                    "title": product.title,
                    "price": product.price,
                    "rating": product.rating,
                    "url": product.url,
                    "image_url": product.image_url
                })
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Error getting product suggestions: {e}")
            return []
    
    async def get_session_info(self, session_id: str) -> Dict[str, Any]:
        """Get session information"""
        try:
            session = self.conversation_manager.get_session(session_id)
            if not session:
                raise HTTPException(status_code=404, detail="Session not found")
            
            return {
                "session_id": session.session_id,
                "user_id": session.user_id,
                "created_at": session.created_at.isoformat() if hasattr(session, 'created_at') else None,
                "message_count": len(session.messages) if hasattr(session, 'messages') else 0,
                "state": session.state.value if hasattr(session, 'state') else 'active',
                "entities_collected": getattr(session, 'entities_collected', {})
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting session info: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error")
    
    async def get_conversation_history(self, session_id: str, limit: int = 10) -> Dict[str, Any]:
        """Get conversation history"""
        try:
            history = self.conversation_manager.get_conversation_history(session_id, limit)
            
            return {
                "session_id": session_id,
                "history": history,
                "total_messages": len(history)
            }
            
        except Exception as e:
            logger.error(f"Error getting conversation history: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error")
    
    async def clear_session(self, session_id: str) -> Dict[str, str]:
        """Clear conversation session"""
        try:
            success = self.conversation_manager.clear_session(session_id)
            if not success:
                raise HTTPException(status_code=404, detail="Session not found")
            
            # Clear cache for this session
            await cache_service.delete_pattern(f"chat:*:{session_id}:*")
            
            return {"message": "Session cleared successfully", "session_id": session_id}
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error clearing session: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error")
    
    async def get_active_sessions_count(self) -> int:
        """Get count of active sessions"""
        try:
            return self.conversation_manager.get_active_sessions_count()
        except Exception as e:
            logger.error(f"Error getting active sessions count: {str(e)}")
            return 0
    
    async def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions"""
        try:
            return self.conversation_manager.cleanup_expired_sessions()
        except Exception as e:
            logger.error(f"Error cleaning up sessions: {str(e)}")
            return 0
    
    def health_check(self) -> Dict[str, Any]:
        """Health check for chat service"""
        components = {
            "conversation_manager": "operational" if self.conversation_manager else "failed",
            "intent_engine": "operational" if self.intent_engine else "failed",
            "response_generator": "operational" if self.response_generator else "failed"
        }
        
        all_operational = all(status == "operational" for status in components.values())
        
        return {
            "status": "healthy" if all_operational else "degraded",
            "components": components,
            "cache_service": cache_service.health_check()
        }

# Global chat service instance
chat_service = ChatService()
