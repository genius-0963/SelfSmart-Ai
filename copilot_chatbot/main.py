"""
SmartShelf AI - AI Chat Service

Simplified chat service with 4 core endpoints for global deployment.
"""

# Load .env BEFORE any config imports so API keys are available
import os
from pathlib import Path
_env_path = Path(__file__).resolve().parent.parent / ".env"
if _env_path.exists():
    from dotenv import load_dotenv
    load_dotenv(_env_path)

import asyncio
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import time
from typing import Optional
from pydantic import BaseModel

from .rag.pipeline import RAGPipeline
from .llm.openai_client import OpenAIClient
from .vector_store.chromadb_client import ChromaDBClient
from .product_suggestion.recommender import AmazonProductRecommender
from .config import CopilotConfig
from .core.exceptions import CopilotException

# Phase 1 NLU (optional): intent recognition, response generation, sports, product knowledge
try:
    from .nlp.intent_recognition import create_intent_engine
    from .nlp.intent_recognition import IntentType  # noqa: F401 - used when Phase 1 active
    from .nlp.response_generation import create_response_generator
    from .nlp.conversation_flow import create_conversation_manager
    _PHASE1_NLU_AVAILABLE = True
except Exception:
    _PHASE1_NLU_AVAILABLE = False
    IntentType = None  # type: ignore

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("🤖 Starting SmartShelf AI Chat Service...")
    
    try:
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
            logger.warning("⚠️  Server will start but chat features will be limited. Please set OPENAI_API_KEY or DEEPSEEK_API_KEY in .env file.")
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
            # Try to load pre-built embeddings
            product_recommender.load_embeddings(config.product_suggestion.embeddings_path)
            logger.info("✅ Loaded existing product embeddings")
        except FileNotFoundError:
            logger.warning("⚠️  No pre-built embeddings found, product suggestions will be limited")
            # Create empty recommender - embeddings will need to be built separately
            product_recommender = AmazonProductRecommender(config.product_suggestion.model_name)
        
        app.state.product_recommender = product_recommender
        logger.info("✅ Product suggestion system initialized")
        
        # Build initial index if needed
        if app.state.rag_pipeline and not vector_store.has_documents():
            logger.info("📚 Building initial document index...")
            await app.state.rag_pipeline.build_index()
            logger.info("✅ Document index built")
        
        # Phase 1 NLU: intent recognition, responses, sports, product knowledge (no API key required)
        if _PHASE1_NLU_AVAILABLE:
            try:
                app.state.intent_engine = create_intent_engine()
                app.state.response_generator = create_response_generator()
                app.state.conversation_manager = create_conversation_manager()
                logger.info("✅ Phase 1 NLU initialized (intent, responses, sports, products)")
            except Exception as e:
                logger.warning(f"⚠️  Phase 1 NLU init failed: {e}")
                app.state.intent_engine = None
                app.state.response_generator = None
                app.state.conversation_manager = None
        else:
            app.state.intent_engine = None
            app.state.response_generator = None
            app.state.conversation_manager = None
            logger.debug("Phase 1 NLU not loaded (import failed)")
        
        logger.info("🎉 SmartShelf AI Chat Service started successfully!")
        
    except Exception as e:
        logger.error(f"❌ Failed to start Chat service: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down SmartShelf AI Chat Service...")


# Create FastAPI application
app = FastAPI(
    title="SmartShelf AI Chat Service",
    description="AI-powered conversational assistant with RAG",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configure CORS for global access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for global access
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "SmartShelf AI Chat",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": [
            "/chat - Basic chat functionality",
            "/products/chat - Chat with product suggestions", 
            "/search - Context search",
            "/health - Service health check"
        ]
    }


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


class ChatRequest(BaseModel):
    """Request body for /chat (JSON from frontend)."""
    query: str
    session_id: Optional[str] = "default"


@app.post("/chat")
async def chat(req: ChatRequest):
    """
    Chat with the AI Copilot.
    Accepts JSON body: { "query": "...", "session_id": "optional" }
    Uses Phase 1 NLU (intent, sports, products) when available; otherwise RAG/fallback.
    """
    query = req.query or ""
    session_id = req.session_id or "default"
    try:
        # Phase 1 NLU: use intent + response + conversation flow when available and confident
        if (
            getattr(app.state, "conversation_manager", None)
            and getattr(app.state, "intent_engine", None)
            and getattr(app.state, "response_generator", None)
        ):
            try:
                intent = app.state.intent_engine.process_input(query)
                # Use Phase 1 for greeting, help, product_inquiry, sports_topic (and optionally general_question)
                if intent.confidence >= 0.5 and intent.intent_type != IntentType.UNKNOWN:
                    session_id_inner = session_id or "default"
                    session = app.state.conversation_manager.get_session(session_id_inner)
                    if not session:
                        session_id_inner = app.state.conversation_manager.create_session("default")
                    response_obj = app.state.response_generator.generate_response(intent)
                    conv_result = app.state.conversation_manager.process_message(
                        session_id_inner, query, intent, response_obj
                    )
                    text = response_obj.text
                    if conv_result.get("specialized_response") and conv_result["specialized_response"].get("response"):
                        text = conv_result["specialized_response"]["response"]
                    return {
                        "response": text,
                        "session_id": session_id_inner,
                        "query": query,
                        "context": [],
                        "model": "phase1_nlu",
                        "intent": intent.intent_type.value,
                        "follow_up_questions": response_obj.follow_up_questions or conv_result.get("follow_up_questions", []),
                    }
            except Exception as nlu_err:
                logger.debug(f"Phase 1 NLU path skipped: {nlu_err}")
        
        if not hasattr(app.state, 'rag_pipeline') or app.state.rag_pipeline is None:
            # Fallback response when LLM is not configured
            return {
                "response": "⚠️ No API key configured. Please set OPENAI_API_KEY or DEEPSEEK_API_KEY in your .env file to enable chat features.\n\nFor now, I can help you with:\n- Product searches\n- Basic information\n\nTo enable full chat capabilities, add your OpenAI API key to the .env file and restart the server.",
                "session_id": session_id,
                "query": query,
                "context": [],
                "model": "fallback"
            }
        
        # Process query through RAG pipeline
        response = await app.state.rag_pipeline.process_query(query, session_id)
        
        return response
        
    except Exception as e:
        logger.error(f"Chat processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process query: {str(e)}")


@app.post("/search")
async def search_context(query: str, max_results: int = 5):
    """
    Search for relevant context documents.
    
    Args:
        query: Search query
        max_results: Maximum number of results
        
    Returns:
        Relevant documents with similarity scores
    """
    try:
        if not hasattr(app.state, 'vector_store'):
            raise HTTPException(status_code=503, detail="Vector store not ready")
        
        results = await app.state.vector_store.search(query, max_results)
        
        return {
            "query": query,
            "results": results,
            "total_found": len(results)
        }
        
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@app.post("/products/chat")
async def chat_with_product_suggestions(req: ChatRequest):
    """
    Chat with AI copilot enhanced with product suggestions.
    Accepts JSON body: { "query": "...", "session_id": "optional" }
    """
    query = req.query or ""
    session_id = req.session_id or "default"
    try:
        if not hasattr(app.state, 'rag_pipeline') or app.state.rag_pipeline is None:
            # Fallback response when LLM is not configured
            rag_response = {
                "response": "⚠️ No API key configured. Please set OPENAI_API_KEY or DEEPSEEK_API_KEY in your .env file to enable chat features with product suggestions.",
                "session_id": session_id,
                "query": query,
                "context": [],
                "model": "fallback"
            }
        else:
            # Process query through RAG pipeline
            rag_response = await app.state.rag_pipeline.process_query(query, session_id)
        
        if not hasattr(app.state, 'product_recommender'):
            raise HTTPException(status_code=503, detail="Product suggestion system not ready")
        
        # Check if query might be product-related and add suggestions
        product_keywords = ['product', 'recommend', 'suggest', 'find', 'buy', 'price', 'best']
        is_product_query = any(keyword in query.lower() for keyword in product_keywords)
        
        product_suggestions = []
        if is_product_query:
            try:
                product_suggestions = app.state.product_recommender.find_similar_products(query, 5)
            except Exception as e:
                logger.warning(f"Failed to get product suggestions: {e}")
        
        # Combine responses
        enhanced_response = {
            **rag_response,
            "product_suggestions": [rec.__dict__ for rec in product_suggestions] if product_suggestions else []
        }
        
        return enhanced_response
        
    except Exception as e:
        logger.error(f"Enhanced chat processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process query: {str(e)}")


# Global exception handler
@app.exception_handler(CopilotException)
async def copilot_exception_handler(request, exc: CopilotException):
    """Handle custom Copilot exceptions."""
    logger.error(f"Copilot exception: {exc.message}")
    raise HTTPException(
        status_code=exc.status_code,
        detail={
            "error": exc.error_type,
            "message": exc.message,
            "details": exc.details
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )
