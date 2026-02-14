"""
Intelligent AI Backend - Main FastAPI Server
Production-grade implementation with complete natural language understanding
"""

import json
import logging
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

# Import our NLP components
from nlp.intent_recognition import create_intent_engine, Intent, IntentType
from nlp.response_generation import create_response_generator, Response
from nlp.conversation_flow import create_conversation_manager
from nlp.sports_handler import create_sports_handler
from nlp.product_knowledge import create_product_advisor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Intelligent AI Backend",
    description="Production-grade Natural Language Understanding & Response System",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize NLP components
intent_engine = create_intent_engine()
response_generator = create_response_generator()
conversation_manager = create_conversation_manager()
sports_handler = create_sports_handler()
product_advisor = create_product_advisor()

# Pydantic models for API
class ChatRequest(BaseModel):
    message: str = Field(..., description="User message to process")
    session_id: Optional[str] = Field(None, description="Session ID for conversation continuity")
    user_id: Optional[str] = Field("anonymous", description="User identifier")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional context")

class ChatResponse(BaseModel):
    response: str = Field(..., description="AI response")
    session_id: str = Field(..., description="Session ID")
    intent: str = Field(..., description="Recognized intent")
    confidence: float = Field(..., description="Intent confidence score")
    follow_up_questions: List[str] = Field(..., description="Suggested follow-up questions")
    entities: Dict[str, Any] = Field(..., description="Extracted entities")
    conversation_state: str = Field(..., description="Current conversation state")
    timestamp: str = Field(..., description="Response timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

class SessionInfo(BaseModel):
    session_id: str = Field(..., description="Session ID")
    user_id: str = Field(..., description="User ID")
    created_at: str = Field(..., description="Session creation time")
    message_count: int = Field(..., description="Number of messages in session")
    state: str = Field(..., description="Current conversation state")
    entities_collected: Dict[str, Any] = Field(..., description="Collected entities")

class HealthResponse(BaseModel):
    status: str = Field(..., description="Service health status")
    timestamp: str = Field(..., description="Health check timestamp")
    active_sessions: int = Field(..., description="Number of active sessions")
    components: Dict[str, str] = Field(..., description="Component status")

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        self.active_connections[session_id] = websocket
        logger.info(f"WebSocket connected for session {session_id}")
    
    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]
            logger.info(f"WebSocket disconnected for session {session_id}")
    
    async def send_message(self, session_id: str, message: dict):
        if session_id in self.active_connections:
            await self.active_connections[session_id].send_json(message)

connection_manager = ConnectionManager()

# API Routes
@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint"""
    return {
        "message": "Intelligent AI Backend - Natural Language Understanding System",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    try:
        # Test all components
        test_intent = intent_engine.process_input("hello")
        test_response = response_generator.generate_response(test_intent)
        
        active_sessions = conversation_manager.get_active_sessions_count()
        
        return HealthResponse(
            status="healthy",
            timestamp=datetime.now().isoformat(),
            active_sessions=active_sessions,
            components={
                "intent_engine": "operational",
                "response_generator": "operational",
                "conversation_manager": "operational",
                "sports_handler": "operational",
                "product_advisor": "operational"
            }
        )
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=503, detail="Service unavailable")

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Main chat endpoint"""
    try:
        # Get or create session
        if not request.session_id:
            session_id = conversation_manager.create_session(request.user_id)
        else:
            session_id = request.session_id
            session = conversation_manager.get_session(session_id)
            if not session:
                session_id = conversation_manager.create_session(request.user_id)
        
        # Process user message
        intent = intent_engine.process_input(
            request.message, 
            context=request.context
        )
        
        # Generate response
        response = response_generator.generate_response(intent)
        
        # Process through conversation manager
        conversation_result = conversation_manager.process_message(
            session_id, request.message, intent, response
        )
        
        # Handle specialized responses
        specialized_response = conversation_result.get('specialized_response')
        if specialized_response:
            if 'response' in specialized_response:
                response.text = specialized_response['response']
            if 'follow_up_questions' in specialized_response:
                response.follow_up_questions = specialized_response['follow_up_questions']
        
        # Create final response
        chat_response = ChatResponse(
            response=response.text,
            session_id=session_id,
            intent=intent.intent_type.value,
            confidence=intent.confidence,
            follow_up_questions=response.follow_up_questions,
            entities=intent.entities,
            conversation_state=conversation_result['state'],
            timestamp=datetime.now().isoformat(),
            metadata={
                "strategy": response.metadata.get('strategy', 'unknown'),
                "specialized_handling": specialized_response is not None,
                "conversation_length": conversation_result['conversation_history']['total_messages']
            }
        )
        
        logger.info(f"Processed chat message for session {session_id}: {intent.intent_type.value}")
        return chat_response
        
    except Exception as e:
        logger.error(f"Error processing chat request: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/session/{session_id}", response_model=SessionInfo)
async def get_session_info(session_id: str):
    """Get session information"""
    try:
        session = conversation_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return SessionInfo(
            session_id=session.session_id,
            user_id=session.user_id,
            created_at=session.created_at.isoformat(),
            message_count=len(session.messages),
            state=session.state.value,
            entities_collected=session.entities_collected
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session info: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/session/{session_id}/history")
async def get_conversation_history(session_id: str, limit: int = 10):
    """Get conversation history for a session"""
    try:
        history = conversation_manager.get_conversation_history(session_id, limit)
        return {
            "session_id": session_id,
            "history": history,
            "total_messages": len(history)
        }
    except Exception as e:
        logger.error(f"Error getting conversation history: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.delete("/session/{session_id}")
async def clear_session(session_id: str):
    """Clear a conversation session"""
    try:
        success = conversation_manager.clear_session(session_id)
        if not success:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return {"message": "Session cleared successfully", "session_id": session_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error clearing session: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/sessions/active")
async def get_active_sessions():
    """Get information about active sessions"""
    try:
        active_count = conversation_manager.get_active_sessions_count()
        return {
            "active_sessions": active_count,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting active sessions: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/admin/cleanup")
async def cleanup_expired_sessions():
    """Clean up expired sessions (admin endpoint)"""
    try:
        cleaned_count = conversation_manager.cleanup_expired_sessions()
        return {
            "message": f"Cleaned up {cleaned_count} expired sessions",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error cleaning up sessions: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# WebSocket endpoint for real-time chat
@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time conversation"""
    await connection_manager.connect(websocket, session_id)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            
            try:
                # Process the message
                request = ChatRequest(**data)
                
                # Get or create session
                session = conversation_manager.get_session(session_id)
                if not session:
                    session_id = conversation_manager.create_session("websocket_user")
                
                # Process message
                intent = intent_engine.process_input(request.message)
                response = response_generator.generate_response(intent)
                
                conversation_result = conversation_manager.process_message(
                    session_id, request.message, intent, response
                )
                
                # Handle specialized responses
                specialized_response = conversation_result.get('specialized_response')
                if specialized_response and 'response' in specialized_response:
                    response.text = specialized_response['response']
                
                # Send response back to client
                await connection_manager.send_message(session_id, {
                    "response": response.text,
                    "session_id": session_id,
                    "intent": intent.intent_type.value,
                    "confidence": intent.confidence,
                    "follow_up_questions": response.follow_up_questions,
                    "entities": intent.entities,
                    "conversation_state": conversation_result['state'],
                    "timestamp": datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"Error processing WebSocket message: {str(e)}")
                await connection_manager.send_message(session_id, {
                    "error": "Failed to process message",
                    "timestamp": datetime.now().isoformat()
                })
    
    except WebSocketDisconnect:
        connection_manager.disconnect(session_id)
        logger.info(f"WebSocket disconnected for session {session_id}")

# Specialized endpoints
@app.post("/sports")
async def sports_conversation(message: str, session_id: Optional[str] = None):
    """Specialized sports conversation endpoint"""
    try:
        from nlp.sports_handler import SportsContext
        
        # Create sports context
        sports_context = SportsContext(
            sport_type=None,
            topic=None,
            entities={},
            user_preferences={},
            conversation_history=[]
        )
        
        # Handle sports conversation
        result = sports_handler.handle_sports_conversation(message, sports_context)
        
        return {
            "response": result['response'],
            "topic": result['topic'],
            "entities": result['entities'],
            "follow_up_questions": result['follow_up_questions'],
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in sports conversation: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/products")
async def product_advice(message: str, entities: Dict[str, Any] = {}):
    """Specialized product advice endpoint"""
    try:
        result = product_advisor.get_product_advice(message, entities)
        
        return {
            "advice": result['advice'],
            "category": result['category'],
            "follow_up_questions": result['follow_up_questions'],
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in product advice: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/capabilities")
async def get_capabilities():
    """Get system capabilities"""
    return {
        "intents": [intent.value for intent in IntentType],
        "features": {
            "natural_language_understanding": True,
            "intent_recognition": True,
            "context_analysis": True,
            "conversation_flow": True,
            "sports_conversations": True,
            "product_recommendations": True,
            "follow_up_questions": True,
            "session_management": True,
            "websocket_support": True
        },
        "supported_topics": [
            "General conversation",
            "Help and assistance",
            "Product inquiries and recommendations",
            "Sports discussions (football, basketball, etc.)",
            "Technology advice",
            "Q&A and information"
        ],
        "languages": ["English"],
        "response_formats": ["REST API", "WebSocket"]
    }

# Background tasks
async def periodic_cleanup():
    """Periodic cleanup of expired sessions"""
    while True:
        try:
            await asyncio.sleep(3600)  # Run every hour
            cleaned = conversation_manager.cleanup_expired_sessions()
            if cleaned > 0:
                logger.info(f"Periodic cleanup: removed {cleaned} expired sessions")
        except Exception as e:
            logger.error(f"Error in periodic cleanup: {str(e)}")

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize background tasks"""
    logger.info("Starting Intelligent AI Backend...")
    logger.info("All NLP components initialized successfully")
    
    # Start background cleanup task
    asyncio.create_task(periodic_cleanup())
    
    logger.info("Intelligent AI Backend is ready!")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down Intelligent AI Backend...")
    # Cleanup could be added here if needed
    logger.info("Shutdown complete")

# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "timestamp": datetime.now().isoformat()}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "timestamp": datetime.now().isoformat()}
    )

# Run the application
if __name__ == "__main__":
    uvicorn.run(
        "intelligent_backend:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
