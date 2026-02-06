"""
SmartShelf AI - AI Copilot API v1

Endpoints for AI-powered conversational assistance and decision support.
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import uuid
import logging

from ...database import get_db
from ...database import ChatSession, ChatMessage
from ...models.copilot import (
    ChatRequest, ChatResponse, ChatSessionResponse, ChatMessageResponse,
    ContextSearchRequest, ContextSearchResponse, CopilotAnalytics
)
from ...core.exceptions import ValidationError, CopilotError

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat_with_copilot(
    request: ChatRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Send a message to the AI Copilot and get a response."""
    try:
        # Get or create session
        if request.session_id:
            session = db.query(ChatSession).filter(
                ChatSession.session_id == request.session_id,
                ChatSession.is_active == True
            ).first()
            if not session:
                raise ValidationError("Invalid or expired session")
        else:
            # Create new session
            session_id = str(uuid.uuid4())
            session = ChatSession(
                session_id=session_id,
                user_id="demo_user",  # In production, get from auth
                session_metadata={"source": "api"}
            )
            db.add(session)
            db.commit()
            db.refresh(session)
        
        # Save user message
        user_message = ChatMessage(
            session_id=session.session_id,
            message_type="user",
            message_content=request.message,
            model_used="user_input"
        )
        db.add(user_message)
        db.commit()
        db.refresh(user_message)
        
        # Generate AI response (simplified implementation)
        ai_response = await generate_ai_response(request.message, session.session_id, db)
        
        # Save AI response
        assistant_message = ChatMessage(
            session_id=session.session_id,
            message_type="assistant",
            message_content=ai_response["response"],
            message_data=ai_response.get("data"),
            context_used=ai_response.get("context_sources", []),
            model_used="demo_model",
            tokens_used=len(ai_response["response"].split()),
            response_time_ms=150  # Mock response time
        )
        db.add(assistant_message)
        db.commit()
        db.refresh(assistant_message)
        
        # Update session activity
        session.last_activity = datetime.utcnow()
        db.commit()
        
        return ChatResponse(
            session_id=session.session_id,
            message_id=assistant_message.id,
            response=ai_response["response"],
            message_data=ai_response.get("data"),
            context_used=[{"source": src, "relevance": 0.9} for src in ai_response.get("context_sources", [])],
            sources_cited=ai_response.get("sources_cited", []),
            model_used="demo_model",
            tokens_used=assistant_message.tokens_used,
            response_time_ms=assistant_message.response_time_ms,
            confidence_score=0.85,
            suggested_questions=ai_response.get("suggested_questions", []),
            related_topics=ai_response.get("related_topics", [])
        )
        
    except Exception as e:
        logger.error(f"Copilot chat failed: {e}")
        raise CopilotError(f"Failed to process chat request: {str(e)}")


async def generate_ai_response(message: str, session_id: str, db: Session) -> Dict[str, Any]:
    """Generate AI response (simplified implementation)."""
    message_lower = message.lower()
    
    # Simple keyword-based responses for demo
    if any(keyword in message_lower for keyword in ["stock", "inventory", "reorder"]):
        response = "Based on current inventory levels, I recommend focusing on products with less than 7 days of supply. Would you like me to show you the specific products that need immediate attention?"
        suggested_questions = [
            "Which products are at risk of stockout?",
            "What should I reorder this week?",
            "Show me inventory levels by category"
        ]
        related_topics = ["inventory_management", "reorder_points", "stockout_prevention"]
        
    elif any(keyword in message_lower for keyword in ["revenue", "sales", "performance"]):
        response = "Your total revenue for the last 30 days is $609,523.18, representing a 12% increase from the previous period. Electronics and Clothing categories are driving this growth. Would you like me to break down the performance by product?"
        suggested_questions = [
            "What are my top selling products?",
            "How is revenue trending this month?",
            "Which categories are performing best?"
        ]
        related_topics = ["revenue_analytics", "sales_performance", "category_analysis"]
        
    elif any(keyword in message_lower for keyword in ["forecast", "prediction", "demand"]):
        response = "My demand forecasting models predict steady growth over the next 30 days with a 95% confidence interval. Seasonal patterns suggest a 15% increase in demand for Electronics products. Would you like to see the detailed forecast?"
        suggested_questions = [
            "Show me the 30-day demand forecast",
            "Which products have highest forecast accuracy?",
            "What factors are driving demand changes?"
        ]
        related_topics = ["demand_forecasting", "seasonal_patterns", "prediction_accuracy"]
        
    elif any(keyword in message_lower for keyword in ["price", "pricing", "cost"]):
        response = "I've identified 8 products with pricing optimization opportunities. The average potential revenue impact is $217.38 per product. Most recommendations involve small price adjustments (5-10%) based on competitor analysis and price elasticity."
        suggested_questions = [
            "Which products need price adjustments?",
            "How do my prices compare to competitors?",
            "What's the revenue impact of pricing changes?"
        ]
        related_topics = ["pricing_optimization", "competitor_analysis", "price_elasticity"]
        
    else:
        response = "I'm here to help you make data-driven decisions for your retail business. I can assist with inventory management, demand forecasting, pricing optimization, and sales analytics. What specific area would you like to explore?"
        suggested_questions = [
            "Show me inventory alerts",
            "What's my revenue trend?",
            "Which products should I reorder?"
        ]
        related_topics = ["inventory", "forecasting", "pricing", "analytics"]
    
    return {
        "response": response,
        "data": None,
        "context_sources": ["sales_data", "inventory_data", "product_catalog"],
        "sources_cited": ["Database Analytics", "ML Models", "Business Rules"],
        "suggested_questions": suggested_questions,
        "related_topics": related_topics
    }


@router.get("/sessions", response_model=List[ChatSessionResponse])
async def get_chat_sessions(
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Get recent chat sessions."""
    sessions = db.query(ChatSession).filter(
        ChatSession.is_active == True
    ).order_by(ChatSession.last_activity.desc()).limit(limit).all()
    
    # Get message counts for each session
    session_responses = []
    for session in sessions:
        message_count = db.query(ChatMessage).filter(
            ChatMessage.session_id == session.session_id
        ).count()
        
        # Get average rating if available
        avg_rating = db.query(func.avg(ChatMessage.user_feedback)).filter(
            ChatMessage.session_id == session.session_id,
            ChatMessage.user_feedback.isnot(None)
        ).scalar()
        
        session_responses.append(ChatSessionResponse(
            id=session.id,
            session_id=session.session_id,
            user_id=session.user_id,
            created_date=session.created_date,
            last_activity=session.last_activity,
            is_active=session.is_active,
            message_count=message_count,
            average_response_time_ms=150,  # Mock data
            user_satisfaction_score=avg_rating,
            session_metadata=session.session_metadata
        ))
    
    return session_responses


@router.get("/sessions/{session_id}/messages", response_model=List[ChatMessageResponse])
async def get_chat_messages(
    session_id: str,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get messages for a specific chat session."""
    messages = db.query(ChatMessage).filter(
        ChatMessage.session_id == session_id
    ).order_by(ChatMessage.created_date).limit(limit).all()
    
    return [
        ChatMessageResponse(
            id=msg.id,
            session_id=msg.session_id,
            message_type=msg.message_type,
            message_content=msg.message_content,
            message_data=msg.message_data,
            context_used=msg.context_used,
            model_used=msg.model_used,
            tokens_used=msg.tokens_used,
            response_time_ms=msg.response_time_ms,
            user_feedback=msg.user_feedback,
            created_date=msg.created_date
        )
        for msg in messages
    ]


@router.post("/context/search", response_model=ContextSearchResponse)
async def search_context(
    request: ContextSearchRequest,
    db: Session = Depends(get_db)
):
    """Search for relevant context documents."""
    # Simplified context search (in production, use vector search)
    mock_results = [
        {
            "document_id": "sales_summary_2024",
            "content": "Total sales for 2024: $609,523.18 across 50 products",
            "source": "sales_data",
            "source_type": "analytics",
            "relevance_score": 0.95,
            "metadata": {"date": "2024-02-06", "type": "summary"},
            "retrieved_at": datetime.utcnow().isoformat()
        },
        {
            "document_id": "inventory_alerts",
            "content": "5 products currently at risk of stockout",
            "source": "inventory_data",
            "source_type": "alert",
            "relevance_score": 0.87,
            "metadata": {"alert_count": 5, "severity": "high"},
            "retrieved_at": datetime.utcnow().isoformat()
        }
    ]
    
    # Filter by source types if specified
    if request.source_types:
        mock_results = [r for r in mock_results if r["source_type"] in request.source_types]
    
    return ContextSearchResponse(
        query=request.query,
        results=mock_results[:request.max_results],
        total_found=len(mock_results),
        search_time_ms=45,
        search_metadata={"index_version": "v1.0", "search_method": "hybrid"}
    )


@router.get("/analytics", response_model=CopilotAnalytics)
async def get_copilot_analytics(
    period_days: int = 30,
    db: Session = Depends(get_db)
):
    """Get AI Copilot usage analytics."""
    start_date = datetime.utcnow() - timedelta(days=period_days)
    
    # Session metrics
    total_sessions = db.query(ChatSession).filter(
        ChatSession.created_date >= start_date
    ).count()
    
    active_sessions = db.query(ChatSession).filter(
        ChatSession.created_date >= start_date,
        ChatSession.is_active == True
    ).count()
    
    # Message metrics
    total_messages = db.query(ChatMessage).filter(
        ChatMessage.created_date >= start_date
    ).count()
    
    user_messages = db.query(ChatMessage).filter(
        ChatMessage.created_date >= start_date,
        ChatMessage.message_type == "user"
    ).count()
    
    # Performance metrics
    avg_response_time = db.query(func.avg(ChatMessage.response_time_ms)).filter(
        ChatMessage.created_date >= start_date,
        ChatMessage.message_type == "assistant"
    ).scalar()
    
    avg_tokens = db.query(func.avg(ChatMessage.tokens_used)).filter(
        ChatMessage.created_date >= start_date,
        ChatMessage.message_type == "assistant"
    ).scalar()
    
    # Satisfaction metrics
    avg_rating = db.query(func.avg(ChatMessage.user_feedback)).filter(
        ChatMessage.created_date >= start_date,
        ChatMessage.user_feedback.isnot(None)
    ).scalar()
    
    # Mock additional analytics
    most_asked_topics = [
        {"topic": "inventory_management", "count": 45, "percentage": 35.2},
        {"topic": "revenue_analytics", "count": 32, "percentage": 25.0},
        {"topic": "demand_forecasting", "count": 28, "percentage": 21.9},
        {"topic": "pricing_optimization", "count": 23, "percentage": 18.0}
    ]
    
    return CopilotAnalytics(
        period_start=start_date,
        period_end=datetime.utcnow(),
        total_sessions=total_sessions,
        total_messages=total_messages,
        unique_users=1,  # Mock data
        average_session_length_minutes=15.5,  # Mock data
        average_response_time_ms=float(avg_response_time or 150),
        average_tokens_per_response=float(avg_tokens or 100),
        user_satisfaction_score=float(avg_rating or 4.2),
        most_asked_topics=most_asked_topics,
        context_hit_rate=0.87,  # Mock data
        visualization_usage_rate=0.65,  # Mock data
        total_tokens_consumed=int(total_messages * (avg_tokens or 100)),
        estimated_cost_usd=2.45,  # Mock data
        generated_at=datetime.utcnow().isoformat()
    )


@router.post("/feedback/{message_id}")
async def submit_feedback(
    message_id: int,
    rating: int,
    feedback_text: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Submit feedback for a copilot response."""
    if rating < 1 or rating > 5:
        raise ValidationError("Rating must be between 1 and 5")
    
    message = db.query(ChatMessage).filter(ChatMessage.id == message_id).first()
    if not message:
        raise ValidationError("Message not found")
    
    message.user_feedback = rating
    db.commit()
    
    return {"message": "Feedback submitted successfully", "rating": rating}


@router.delete("/sessions/{session_id}")
async def end_chat_session(session_id: str, db: Session = Depends(get_db)):
    """End a chat session."""
    session = db.query(ChatSession).filter(
        ChatSession.session_id == session_id
    ).first()
    if not session:
        raise ValidationError("Session not found")
    
    session.is_active = False
    db.commit()
    
    return {"message": f"Session {session_id} ended successfully"}


# Import func for database queries
from sqlalchemy import func
