"""
SmartShelf AI - AI Copilot Service

Main service for the AI-powered conversational assistant with RAG pipeline.
"""

import asyncio
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import time

from .rag.pipeline import RAGPipeline
from .llm.openai_client import OpenAIClient
from .vector_store.chromadb_client import ChromaDBClient
from .config import CopilotConfig
from .core.exceptions import CopilotException

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("🤖 Starting SmartShelf AI Copilot Service...")
    
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
        
        # Build initial index if needed
        if not vector_store.has_documents():
            logger.info("📚 Building initial document index...")
            await rag_pipeline.build_index()
            logger.info("✅ Document index built")
        
        logger.info("🎉 SmartShelf AI Copilot Service started successfully!")
        
    except Exception as e:
        logger.error(f"❌ Failed to start Copilot service: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down SmartShelf AI Copilot Service...")


# Create FastAPI application
app = FastAPI(
    title="SmartShelf AI Copilot Service",
    description="AI-powered conversational assistant with RAG for retail decision support",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "SmartShelf AI Copilot",
        "version": "1.0.0",
        "status": "operational",
        "features": [
            "🔍 Context-aware search",
            "💬 Intelligent conversation",
            "📊 Business insights",
            "🎯 Decision support"
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
        
        return {
            "status": "healthy",
            "timestamp": time.time(),
            "components": {
                "vector_store": vector_store_status,
                "llm_client": llm_status,
                "rag_pipeline": rag_status
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")


@app.post("/chat")
async def chat(query: str, session_id: str = None):
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


@app.post("/index/documents")
async def index_documents():
    """Build or rebuild the document index."""
    try:
        if not hasattr(app.state, 'rag_pipeline'):
            raise HTTPException(status_code=503, detail="RAG pipeline not ready")
        
        await app.state.rag_pipeline.build_index()
        
        return {"message": "Document index built successfully"}
        
    except Exception as e:
        logger.error(f"Index building failed: {e}")
        raise HTTPException(status_code=500, detail=f"Index building failed: {str(e)}")


@app.get("/stats")
async def get_service_stats():
    """Get service statistics."""
    try:
        stats = {}
        
        if hasattr(app.state, 'vector_store'):
            stats["vector_store"] = await app.state.vector_store.get_stats()
        
        if hasattr(app.state, 'rag_pipeline'):
            stats["rag_pipeline"] = await app.state.rag_pipeline.get_stats()
        
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get statistics")


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
