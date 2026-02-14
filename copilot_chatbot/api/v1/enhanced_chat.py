"""
SmartShelf AI - Enhanced Chat API
Production-ready chat endpoints with comprehensive features
"""

import asyncio
import time
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import logging

from services.chat_service import chat_service
from services.analytics_service import analytics_service
from services.metrics_service import metrics_service
from services.cache_service import cache_service
from core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])

# Pydantic models for enhanced API
class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=10000, description="User message to process")
    session_id: Optional[str] = Field(None, description="Session ID for conversation continuity")
    user_id: Optional[str] = Field("anonymous", description="User identifier")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional context")
    include_products: bool = Field(False, description="Include product suggestions")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")

class ChatResponse(BaseModel):
    response: str = Field(..., description="AI response")
    session_id: str = Field(..., description="Session ID")
    intent: str = Field(..., description="Recognized intent")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Intent confidence score")
    follow_up_questions: List[str] = Field(..., description="Suggested follow-up questions")
    entities: Dict[str, Any] = Field(..., description="Extracted entities")
    conversation_state: str = Field(..., description="Current conversation state")
    timestamp: float = Field(..., description="Response timestamp")
    product_suggestions: List[Dict[str, Any]] = Field(default=[], description="Product suggestions")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

class SessionCreateRequest(BaseModel):
    title: Optional[str] = Field("New Chat", description="Session title")
    user_id: Optional[str] = Field("anonymous", description="User identifier")

class FeedbackRequest(BaseModel):
    session_id: str = Field(..., description="Session ID")
    rating: int = Field(..., ge=1, le=5, description="User rating (1-5)")
    feedback: Optional[str] = Field("", description="Optional feedback text")

# Enhanced chat endpoint
@router.post("/", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """Enhanced chat endpoint with comprehensive features"""
    start_time = time.time()
    
    try:
        # Process message through enhanced chat service
        result = await chat_service.process_message(
            message=request.message,
            session_id=request.session_id,
            user_id=request.user_id,
            context=request.context,
            include_products=request.include_products
        )
        
        # Track analytics
        await analytics_service.track_conversation(
            session_id=result['session_id'],
            user_message=request.message,
            ai_response=result['response'],
            intent=result['intent'],
            confidence=result['confidence'],
            response_time=result['metadata']['response_time_ms'] / 1000,
            user_id=request.user_id,
            metadata={
                **request.metadata,
                'include_products': request.include_products,
                'product_count': len(result.get('product_suggestions', []))
            }
        )
        
        # Record metrics
        response_time = time.time() - start_time
        metrics_service.record_request("/api/v1/chat", "POST", response_time, 200, request.user_id, result['intent'])
        
        return ChatResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        metrics_service.record_request("/api/v1/chat", "POST", time.time() - start_time, 500, request.user_id)
        raise HTTPException(status_code=500, detail="Internal server error")

# Session management endpoints
@router.post("/sessions", response_model=Dict[str, Any])
async def create_session(request: SessionCreateRequest):
    """Create a new chat session"""
    try:
        session_id = chat_service.conversation_manager.create_session(request.user_id)
        
        return {
            "session_id": session_id,
            "user_id": request.user_id,
            "title": request.title,
            "created_at": time.time(),
            "message": "Session created successfully"
        }
        
    except Exception as e:
        logger.error(f"Error creating session: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create session")

@router.get("/sessions")
async def list_sessions():
    """List all active sessions"""
    try:
        active_count = await chat_service.get_active_sessions_count()
        
        return {
            "active_sessions": active_count,
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"Error listing sessions: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to list sessions")

@router.get("/sessions/{session_id}")
async def get_session_info(session_id: str):
    """Get detailed session information"""
    try:
        session_info = await chat_service.get_session_info(session_id)
        return session_info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session info: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get session info")

@router.get("/sessions/{session_id}/history")
async def get_conversation_history(session_id: str, limit: int = 50):
    """Get conversation history for a session"""
    try:
        if limit > 100:
            limit = 100  # Enforce maximum limit
        
        history = await chat_service.get_conversation_history(session_id, limit)
        return history
        
    except Exception as e:
        logger.error(f"Error getting conversation history: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get conversation history")

@router.delete("/sessions/{session_id}")
async def clear_session(session_id: str):
    """Clear a conversation session"""
    try:
        result = await chat_service.clear_session(session_id)
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error clearing session: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to clear session")

# Feedback endpoints
@router.post("/feedback")
async def submit_feedback(request: FeedbackRequest):
    """Submit user feedback for a session"""
    try:
        await analytics_service.track_user_feedback(
            session_id=request.session_id,
            rating=request.rating,
            feedback=request.feedback
        )
        
        return {
            "message": "Feedback submitted successfully",
            "session_id": request.session_id,
            "rating": request.rating
        }
        
    except Exception as e:
        logger.error(f"Error submitting feedback: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to submit feedback")

# Analytics endpoints
@router.get("/analytics/conversations")
async def get_conversation_analytics(days: int = 7):
    """Get conversation analytics"""
    try:
        if days > 90:
            days = 90  # Enforce maximum limit
        
        analytics = await analytics_service.get_conversation_analytics(days)
        return analytics
        
    except Exception as e:
        logger.error(f"Error getting conversation analytics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get analytics")

@router.get("/analytics/users/{user_id}")
async def get_user_analytics(user_id: str):
    """Get analytics for a specific user"""
    try:
        analytics = await analytics_service.get_user_analytics(user_id)
        return analytics
        
    except Exception as e:
        logger.error(f"Error getting user analytics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get user analytics")

@router.get("/analytics/sessions/{session_id}")
async def get_session_analytics(session_id: str):
    """Get analytics for a specific session"""
    try:
        analytics = await analytics_service.get_session_analytics(session_id)
        return analytics
        
    except Exception as e:
        logger.error(f"Error getting session analytics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get session analytics")

@router.get("/analytics/products")
async def get_product_analytics(days: int = 7):
    """Get product-related analytics"""
    try:
        if days > 90:
            days = 90
        
        analytics = await analytics_service.get_product_analytics(days)
        return analytics
        
    except Exception as e:
        logger.error(f"Error getting product analytics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get product analytics")

# System endpoints
@router.get("/health")
async def health_check():
    """Enhanced health check endpoint"""
    try:
        chat_health = chat_service.health_check()
        cache_health = cache_service.health_check()
        system_metrics = metrics_service.get_metrics()
        
        return {
            "status": "healthy" if chat_health["status"] == "healthy" else "degraded",
            "timestamp": time.time(),
            "version": settings.app_version,
            "components": {
                "chat_service": chat_health,
                "cache_service": cache_health,
                "analytics_service": {"status": "operational"}
            },
            "system_metrics": {
                "uptime_seconds": system_metrics["uptime_seconds"],
                "total_requests": system_metrics["total_requests"],
                "error_rate": system_metrics["error_rate"],
                "active_connections": system_metrics["active_connections"]
            }
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "timestamp": time.time(),
                "error": str(e)
            }
        )

@router.get("/metrics")
async def get_system_metrics():
    """Get comprehensive system metrics"""
    try:
        return metrics_service.get_metrics()
        
    except Exception as e:
        logger.error(f"Error getting metrics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get metrics")

@router.post("/admin/cleanup")
async def cleanup_expired_sessions():
    """Clean up expired sessions (admin endpoint)"""
    try:
        cleaned_count = await chat_service.cleanup_expired_sessions()
        
        return {
            "message": f"Cleaned up {cleaned_count} expired sessions",
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"Error during cleanup: {str(e)}")
        raise HTTPException(status_code=500, detail="Cleanup failed")

# WebSocket endpoint for real-time chat
@router.websocket("/ws/{session_id}")
async def websocket_chat_endpoint(websocket: WebSocket, session_id: str):
    """Enhanced WebSocket endpoint for real-time conversation"""
    await websocket.accept()
    
    # Record connection
    metrics_service.record_websocket_connection("connect", session_id)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            
            try:
                # Validate incoming data
                if 'message' not in data:
                    await websocket.send_json({
                        "error": "Message field is required",
                        "timestamp": time.time()
                    })
                    continue
                
                # Process the message
                request = ChatRequest(**data)
                
                # Get or create session
                session = chat_service.conversation_manager.get_session(session_id)
                if not session:
                    session_id = chat_service.conversation_manager.create_session("websocket_user")
                
                # Process message through chat service
                result = await chat_service.process_message(
                    message=request.message,
                    session_id=session_id,
                    user_id=request.user_id or "websocket_user",
                    context=request.context,
                    include_products=request.include_products
                )
                
                # Send response back to client
                await websocket.send_json({
                    **result,
                    "timestamp": time.time()
                })
                
            except Exception as e:
                logger.error(f"Error processing WebSocket message: {str(e)}")
                await websocket.send_json({
                    "error": "Failed to process message",
                    "details": str(e),
                    "timestamp": time.time()
                })
    
    except WebSocketDisconnect:
        metrics_service.record_websocket_connection("disconnect", session_id)
        logger.info(f"WebSocket disconnected for session {session_id}")
    
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        metrics_service.record_websocket_connection("disconnect", session_id)
