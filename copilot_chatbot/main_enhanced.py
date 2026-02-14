"""
SmartShelf AI - Enhanced Chat Service with Full Feature Set

Enhanced version with authentication, analytics, monitoring, and multi-source scraping.
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

# Monitoring and analytics
from .monitoring.logger import setup_logging, get_logger, LogPerformance
from .monitoring.metrics import metrics, MetricsMiddleware, PerformanceTracker
from .monitoring.error_tracker import track_error, ErrorSeverity, ErrorCategory
from .analytics.engine import AnalyticsEngine

# Enhanced scraping
from .data_scrapers.ebay_scraper import EbayScraper
from .data_scrapers.walmart_scraper import WalmartScraper
from .data_scrapers.shopify_scraper import ShopifyScraper

# Setup logging
setup_logging(
    level="INFO",
    log_file="logs/smartshelf.log",
    enable_json=True
)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Enhanced application lifespan manager."""
    # Startup
    logger.info("🤖 Starting SmartShelf AI Enhanced Chat Service...")
    
    try:
        # Initialize database
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
        llm_client = OpenAIClient(config.llm)
        app.state.llm_client = llm_client
        logger.info("✅ LLM client initialized")
        
        # Initialize RAG pipeline
        rag_pipeline = RAGPipeline(vector_store, llm_client, config.rag)
        app.state.rag_pipeline = rag_pipeline
        logger.info("✅ RAG pipeline initialized")
        
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
        
        # Initialize analytics engine
        app.state.analytics_engine = AnalyticsEngine
        
        # Initialize scrapers
        app.state.scrapers = {
            'ebay': EbayScraper,
            'walmart': WalmartScraper,
            'shopify': ShopifyScraper
        }
        logger.info("✅ Scrapers initialized")
        
        # Build initial index if needed
        if not vector_store.has_documents():
            logger.info("📚 Building initial document index...")
            await rag_pipeline.build_index()
            logger.info("✅ Document index built")
        
        logger.info("🎉 SmartShelf AI Enhanced Chat Service started successfully!")
        
    except Exception as e:
        logger.error(f"❌ Failed to start Enhanced Chat service: {e}")
        track_error(e, ErrorSeverity.CRITICAL, ErrorCategory.SYSTEM, "startup")
        raise
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down SmartShelf AI Enhanced Chat Service...")
    await close_db()
    logger.info("✅ Database connections closed")


# Create FastAPI application
app = FastAPI(
    title="SmartShelf AI Enhanced Chat Service",
    description="AI-powered conversational assistant with full analytics and multi-source scraping",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add metrics middleware
app.add_middleware(MetricsMiddleware)

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
    track_error(exc, ErrorSeverity.MEDIUM, ErrorCategory.BUSINESS_LOGIC, "api_handler")
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
    track_error(exc, ErrorSeverity.HIGH, ErrorCategory.SYSTEM, "api_handler")
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_server_error",
            "message": "An unexpected error occurred",
            "request_id": getattr(request.state, 'request_id', None)
        }
    )


# Root endpoint
@app.get("/")
async def root():
    """Enhanced root endpoint."""
    return {
        "service": "SmartShelf AI Enhanced Chat",
        "version": "2.0.0",
        "status": "operational",
        "features": [
            "Authentication & Authorization",
            "Advanced Analytics",
            "Multi-source Product Scraping",
            "Real-time Monitoring",
            "Error Tracking",
            "Performance Metrics"
        ],
        "endpoints": {
            "auth": "/auth/*",
            "chat": "/chat/*",
            "products": "/products/*",
            "analytics": "/analytics/*",
            "admin": "/admin/*"
        }
    }


# Health check with enhanced metrics
@app.get("/health")
async def health_check():
    """Enhanced health check endpoint."""
    try:
        # Check components
        vector_store_status = "connected" if hasattr(app.state, 'vector_store') else "disconnected"
        llm_status = "connected" if hasattr(app.state, 'llm_client') else "disconnected"
        rag_status = "ready" if hasattr(app.state, 'rag_pipeline') else "not_ready"
        product_suggestion_status = "ready" if hasattr(app.state, 'product_recommender') else "not_ready"
        
        # Get system metrics
        system_metrics = metrics.get_metrics_summary()
        
        return {
            "status": "healthy",
            "timestamp": time.time(),
            "components": {
                "vector_store": vector_store_status,
                "llm_client": llm_status,
                "rag_pipeline": rag_status,
                "product_suggestion": product_suggestion_status
            },
            "system_metrics": system_metrics
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        track_error(e, ErrorSeverity.MEDIUM, ErrorCategory.SYSTEM, "health_check")
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
            
            # Track analytics
            analytics_crud = AnalyticsCRUD(db)
            analytics_crud.create_event(
                AnalyticsEventType.USER_LOGIN,
                user_id=user.id,
                event_data={"registration": True}
            )
            
            # Update metrics
            metrics.increment_user_registrations()
            
            return UserResponse.from_orm(user)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Registration failed: {e}")
            track_error(e, ErrorSeverity.MEDIUM, ErrorCategory.AUTHENTICATION, "register")
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
            
            # Track analytics
            analytics_crud = AnalyticsCRUD(db)
            analytics_crud.create_event(
                AnalyticsEventType.USER_LOGIN,
                user_id=user.id
            )
            
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
            track_error(e, ErrorSeverity.MEDIUM, ErrorCategory.AUTHENTICATION, "login")
            raise HTTPException(status_code=500, detail="Login failed")


# Chat endpoints
@app.post("/chat", response_model=MessageResponse)
async def chat(
    message_data: MessageCreate,
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db)
):
    """Enhanced chat endpoint with analytics."""
    with PerformanceTracker("chat_response"):
        try:
            if not hasattr(app.state, 'rag_pipeline'):
                raise HTTPException(status_code=503, detail="RAG pipeline not ready")
            
            # Get or create session
            session_crud = ChatSessionCRUD(db)
            message_crud = MessageCRUD(db)
            analytics_crud = AnalyticsCRUD(db)
            
            # For simplicity, create new session each time (in production, you'd manage sessions)
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
            
            # Track analytics
            analytics_crud.create_event(
                AnalyticsEventType.MESSAGE_SENT,
                user_id=current_user.id,
                session_id=str(session.id),
                event_data={
                    "message_role": "user",
                    "content_length": len(message_data.content)
                }
            )
            
            analytics_crud.create_event(
                AnalyticsEventType.MESSAGE_SENT,
                user_id=current_user.id,
                session_id=str(session.id),
                event_data={
                    "message_role": "assistant",
                    "processing_time": processing_time,
                    "model_used": response.get('model_used')
                }
            )
            
            # Update metrics
            metrics.increment_chat_messages("user", str(session.id))
            metrics.increment_chat_messages("assistant", str(session.id))
            metrics.record_chat_response_duration(response.get('model_used', 'unknown'), processing_time)
            
            return MessageResponse.from_orm(ai_message)
            
        except Exception as e:
            logger.error(f"Chat processing failed: {e}")
            track_error(e, ErrorSeverity.HIGH, ErrorCategory.BUSINESS_LOGIC, "chat")
            raise HTTPException(status_code=500, detail="Failed to process query")


# Product search endpoints
@app.get("/products/search", response_model=List[ProductResponse])
async def search_products(
    query: str,
    source: Optional[str] = None,
    max_results: int = 20,
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db)
):
    """Enhanced product search with multiple sources."""
    try:
        product_crud = ProductCRUD(db)
        analytics_crud = AnalyticsCRUD(db)
        
        # Search in database first
        products = product_crud.search_products(
            query=query,
            source=source,
            limit=max_results
        )
        
        # If no products found, try scraping
        if not products and source in app.state.scrapers:
            scraper_class = app.state.scrapers[source]
            
            async with scraper_class() as scraper:
                scraped_products = await scraper.search_products(query, max_results)
                
                # Save scraped products to database
                for product_data in scraped_products:
                    product_crud.create_or_update_product(product_data)
                
                # Search again in database
                products = product_crud.search_products(
                    query=query,
                    source=source,
                    limit=max_results
                )
        
        # Track analytics
        analytics_crud.create_event(
            AnalyticsEventType.SEARCH_PERFORMED,
            user_id=current_user.id,
            event_data={
                "query": query,
                "source": source,
                "results_count": len(products)
            }
        )
        
        # Update metrics
        metrics.increment_product_searches(source or "database", "user_query")
        
        return [ProductResponse.from_orm(p) for p in products]
        
    except Exception as e:
        logger.error(f"Product search failed: {e}")
        track_error(e, ErrorSeverity.MEDIUM, ErrorCategory.EXTERNAL_API, "product_search")
        raise HTTPException(status_code=500, detail="Product search failed")


# Analytics endpoints
@app.get("/analytics/dashboard")
async def get_analytics_dashboard(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db)
):
    """Get analytics dashboard data."""
    try:
        # Parse dates
        start_dt = datetime.fromisoformat(start_date) if start_date else None
        end_dt = datetime.fromisoformat(end_date) if end_date else None
        
        # Get analytics
        analytics_engine = app.state.analytics_engine(db)
        dashboard_data = await analytics_engine.get_dashboard_summary(start_dt, end_dt)
        
        return dashboard_data
        
    except Exception as e:
        logger.error(f"Analytics dashboard failed: {e}")
        track_error(e, ErrorSeverity.MEDIUM, ErrorCategory.SYSTEM, "analytics")
        raise HTTPException(status_code=500, detail="Analytics failed")


# Metrics endpoint for monitoring
@app.get("/metrics")
async def get_metrics():
    """Get Prometheus metrics."""
    try:
        return Response(
            content=metrics.get_prometheus_metrics(),
            media_type="text/plain"
        )
    except Exception as e:
        logger.error(f"Metrics endpoint failed: {e}")
        raise HTTPException(status_code=500, detail="Metrics failed")


if __name__ == "__main__":
    uvicorn.run(
        "main_enhanced:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )
