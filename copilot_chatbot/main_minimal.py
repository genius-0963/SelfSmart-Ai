"""
SmartShelf AI - Minimal Chat Service (Works without Docker/Redis)
"""

import asyncio
import logging
from contextlib import asynccontextmanager
import time
from typing import Optional, List
from datetime import datetime

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

# Core components
from .rag.pipeline import RAGPipeline
from .llm.openai_client import OpenAIClient
from .vector_store.chromadb_client import ChromaDBClient
from .product_suggestion.recommender import AmazonProductRecommender
from .config import CopilotConfig
from .core.exceptions import CopilotException

# Database and authentication
from .database.connection import init_db, close_db, get_db
from .database.crud import UserCRUD, ChatSessionCRUD, MessageCRUD, ProductCRUD, AnalyticsCRUD
from .database.models import User, ChatSession, Message, Product, AnalyticsEvent, MessageRole, AnalyticsEventType
from .auth.jwt_handler import jwt_handler
from .auth.password_utils import PasswordUtils
from .auth.dependencies import get_current_user, get_current_active_user
from .auth.models import (
    UserCreate, UserLogin, UserResponse, Token, 
    MessageCreate, MessageResponse, SessionResponse,
    AnalyticsEventCreate, ProductResponse
)

# Monitoring
from .monitoring.logger import setup_logging, get_logger, LogPerformance

# Setup logging
setup_logging(
    level="INFO",
    log_file="logs/smartshelf.log",
    enable_json=False  # Use plain text for local development
)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("🤖 Starting SmartShelf AI Minimal Chat Service...")
    
    try:
        # Initialize database (SQLite for local)
        await init_db()
        logger.info("✅ Database initialized")
        
        # Initialize components
        config = CopilotConfig()
        app.state.config = config
        
        # Initialize vector store
        vector_store = ChromaDBClient(config.vector_store)
        app.state.vector_store = vector_store
        logger.info("✅ Vector store initialized")
        
        # Initialize LLM client
        try:
            llm_client = OpenAIClient(config.llm)
            app.state.llm_client = llm_client
            logger.info("✅ LLM client initialized")
        except Exception as e:
            logger.warning(f"⚠️  LLM client initialization failed: {e}")
            app.state.llm_client = None
        
        # Initialize RAG pipeline
        if app.state.llm_client:
            rag_pipeline = RAGPipeline(vector_store, llm_client, config.rag)
            app.state.rag_pipeline = rag_pipeline
            logger.info("✅ RAG pipeline initialized")
        else:
            app.state.rag_pipeline = None
            logger.warning("⚠️  RAG pipeline disabled (no LLM client)")
        
        # Initialize Product Suggestion System
        try:
            product_recommender = AmazonProductRecommender(config.product_suggestion.model_name)
            product_recommender.load_embeddings(config.product_suggestion.embeddings_path)
            logger.info("✅ Loaded existing product embeddings")
        except FileNotFoundError:
            logger.warning("⚠️  No pre-built embeddings found, product suggestions will be limited")
            product_recommender = AmazonProductRecommender(config.product_suggestion.model_name)
        
        app.state.product_recommender = product_recommender
        logger.info("✅ Product suggestion system initialized")
        
        # Build initial index if needed
        if vector_store and not vector_store.has_documents():
            logger.info("📚 Building initial document index...")
            if app.state.rag_pipeline:
                await app.state.rag_pipeline.build_index()
                logger.info("✅ Document index built")
            else:
                logger.warning("⚠️  Cannot build index (no RAG pipeline)")
        
        logger.info("🎉 SmartShelf AI Minimal Chat Service started successfully!")
        
    except Exception as e:
        logger.error(f"❌ Failed to start Chat service: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down SmartShelf AI Chat Service...")
    await close_db()
    logger.info("✅ Database connections closed")


# Create FastAPI application
app = FastAPI(
    title="SmartShelf AI Chat Service",
    description="AI-powered conversational assistant",
    version="2.0.0-minimal",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configure CORS for global access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(CopilotException)
async def copilot_exception_handler(request: Request, exc: CopilotException):
    """Handle custom Copilot exceptions."""
    raise HTTPException(
        status_code=exc.status_code,
        detail={
            "error": exc.error_type,
            "message": exc.message,
            "details": exc.details
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_server_error",
            "message": "An unexpected error occurred"
        }
    )


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "SmartShelf AI Chat",
        "version": "2.0.0-minimal",
        "status": "operational",
        "features": [
            "Authentication & Authorization",
            "Chat Interface",
            "Product Suggestions",
            "Basic Analytics"
        ],
        "endpoints": {
            "auth": "/auth/*",
            "chat": "/chat/*",
            "products": "/products/*",
            "analytics": "/analytics/*"
        }
    }


# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Check components
        vector_store_status = "connected" if hasattr(app.state, 'vector_store') else "disconnected"
        llm_status = "connected" if hasattr(app.state, 'llm_client') else "disconnected"
        rag_status = "ready" if hasattr(app.state, 'rag_pipeline') else "not_ready"
        product_suggestion_status = "ready" if hasattr(app.state, 'product_recommender') else "not_ready"
        
        return {
            "status": "healthy",
            "timestamp": time.time(),
            "components": {
                "vector_store": vector_store_status,
                "llm_client": llm_status,
                "rag_pipeline": rag_status,
                "product_suggestion": product_suggestion_status
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")


# Authentication endpoints
@app.post("/auth/register", response_model=UserResponse)
async def register(user_data: UserCreate, db=Depends(get_db)):
    """User registration endpoint."""
    with LogPerformance(logger, "user_registration"):
        try:
            user_crud = UserCRUD(db)
            
            # Check if user already exists
            existing_user = user_crud.get_user_by_email(user_data.email)
            if existing_user:
                raise HTTPException(status_code=400, detail="Email already registered")
            
            # Hash password
            hashed_password = PasswordUtils.hash_password(user_data.password)
            
            # Create user
            user = user_crud.create_user(
                email=user_data.email,
                name=user_data.name,
                hashed_password=hashed_password
            )
            
            return UserResponse.from_orm(user)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Registration failed: {e}")
            raise HTTPException(status_code=500, detail="Registration failed")


@app.post("/auth/login", response_model=Token)
async def login(user_data: UserLogin, db=Depends(get_db)):
    """User login endpoint."""
    with LogPerformance(logger, "user_login"):
        try:
            user_crud = UserCRUD(db)
            
            # Get user
            user = user_crud.get_user_by_email(user_data.email)
            if not user:
                raise HTTPException(status_code=401, detail="Invalid credentials")
            
            # Verify password
            if not PasswordUtils.verify_password(user_data.password, user.hashed_password):
                raise HTTPException(status_code=401, detail="Invalid credentials")
            
            # Update last login
            user_crud.update_last_login(user.id)
            
            # Create tokens
            access_token = jwt_handler.create_access_token({"sub": str(user.id)})
            refresh_token = jwt_handler.create_refresh_token({"sub": str(user.id)})
            
            return Token(
                access_token=access_token,
                refresh_token=refresh_token,
                expires_in=1800,  # 30 minutes
                user=UserResponse.from_orm(user)
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Login failed: {e}")
            raise HTTPException(status_code=500, detail="Login failed")


# Chat endpoints
@app.post("/chat", response_model=MessageResponse)
async def chat(
    message_data: MessageCreate,
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db)
):
    """Chat endpoint."""
    try:
        if not hasattr(app.state, 'rag_pipeline') or not app.state.rag_pipeline:
            raise HTTPException(status_code=503, detail="AI service not available")
        
        # Get or create session
        session_crud = ChatSessionCRUD(db)
        message_crud = MessageCRUD(db)
        
        # For simplicity, create new session each time
        session = session_crud.create_session(current_user.id)
        
        # Record user message
        user_message = message_crud.create_message(
            session_id=session.id,
            role=MessageRole.USER,
            content=message_data.content
        )
        
        # Process query through RAG pipeline
        start_time = time.time()
        response = await app.state.rag_pipeline.process_query(
            message_data.content, 
            str(session.id)
        )
        processing_time = time.time() - start_time
        
        # Record AI response
        ai_message = message_crud.create_message(
            session_id=session.id,
            role=MessageRole.ASSISTANT,
            content=response.get('response', 'Sorry, I could not process your request.'),
            processing_time=processing_time,
            model_used=response.get('model_used', 'unknown')
        )
        
        return MessageResponse.from_orm(ai_message)
        
    except Exception as e:
        logger.error(f"Chat processing failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to process query")


# Product search endpoints
@app.get("/products/search", response_model=List[ProductResponse])
async def search_products(
    query: str,
    max_results: int = 20,
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db)
):
    """Product search endpoint."""
    try:
        product_crud = ProductCRUD(db)
        
        # Search in database
        products = product_crud.search_products(
            query=query,
            limit=max_results
        )
        
        return [ProductResponse.from_orm(p) for p in products]
        
    except Exception as e:
        logger.error(f"Product search failed: {e}")
        raise HTTPException(status_code=500, detail="Product search failed")


# Analytics endpoints
@app.get("/analytics/dashboard")
async def get_analytics_dashboard(
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db)
):
    """Get basic analytics dashboard data."""
    try:
        # Basic analytics
        user_crud = UserCRUD(db)
        session_crud = ChatSessionCRUD(db)
        message_crud = MessageCRUD(db)
        
        total_users = user_crud.count_users()
        total_sessions = session_crud.count_sessions()
        total_messages = message_crud.count_messages()
        
        return {
            'users': {
                'total_users': total_users,
                'new_users_today': 0  # TODO: Implement
            },
            'chats': {
                'total_sessions': total_sessions,
                'total_messages': total_messages,
                'avg_session_length': 0  # TODO: Implement
            },
            'products': {
                'total_products': 0,  # TODO: Implement
                'most_viewed': []
            }
        }
        
    except Exception as e:
        logger.error(f"Analytics dashboard failed: {e}")
        raise HTTPException(status_code=500, detail="Analytics failed")


if __name__ == "__main__":
    uvicorn.run(
        "main_minimal:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )
