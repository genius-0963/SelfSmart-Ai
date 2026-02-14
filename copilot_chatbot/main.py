"""
SmartShelf AI - AI Chat Service

Simplified chat service with 4 core endpoints for global deployment.
"""

import asyncio
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import time
from typing import Optional

from .rag.pipeline import RAGPipeline
from .llm.openai_client import OpenAIClient
from .vector_store.chromadb_client import ChromaDBClient
from .product_suggestion.recommender import AmazonProductRecommender
from .config import CopilotConfig
from .core.exceptions import CopilotException

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
        if not vector_store.has_documents():
            logger.info("📚 Building initial document index...")
            await rag_pipeline.build_index()
            logger.info("✅ Document index built")
        
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


@app.post("/chat")
async def chat(query: str, session_id: Optional[str] = None):
    """
    Chat with the AI Copilot.
    
    Args:
        query: User query
        session_id: Optional session ID for conversation context
        
    Returns:
        AI response with context and insights
    """
    try:
        if not hasattr(app.state, 'rag_pipeline'):
            raise HTTPException(status_code=503, detail="RAG pipeline not ready")
        
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
async def chat_with_product_suggestions(query: str, session_id: Optional[str] = None):
    """
    Chat with AI copilot enhanced with product suggestions.
    
    Args:
        query: User query
        session_id: Optional session ID for conversation context
        
    Returns:
        AI response with product suggestions
    """
    try:
        if not hasattr(app.state, 'rag_pipeline'):
            raise HTTPException(status_code=503, detail="RAG pipeline not ready")
        
        if not hasattr(app.state, 'product_recommender'):
            raise HTTPException(status_code=503, detail="Product suggestion system not ready")
        
        # Process query through RAG pipeline
        rag_response = await app.state.rag_pipeline.process_query(query, session_id)
        
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
