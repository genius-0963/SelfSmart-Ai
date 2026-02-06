"""
SmartShelf AI - FastAPI Backend Application

Main FastAPI application with all API endpoints for the retail analytics platform.
"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import time
from typing import Dict, Any

from .database import engine, create_tables, get_database_stats
from .api.v1 import data, forecast, pricing, inventory, analytics, copilot
from .core.exceptions import SmartShelfException
from .core.logging import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("🚀 Starting SmartShelf AI Backend...")
    
    # Create database tables
    try:
        create_tables()
        logger.info("✅ Database tables created/verified")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        raise
    
    # Log startup statistics
    try:
        stats = get_database_stats()
        logger.info(f"📊 Database stats: {stats}")
    except Exception as e:
        logger.warning(f"Could not get database stats: {e}")
    
    logger.info("🎉 SmartShelf AI Backend started successfully!")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down SmartShelf AI Backend...")


# Create FastAPI application
app = FastAPI(
    title="SmartShelf AI API",
    description="Intelligent retail analytics platform with demand forecasting, pricing optimization, and AI-powered decision support",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Middleware for request timing
@app.middleware("http")
async def add_process_time_header(request, call_next):
    """Add processing time header to responses."""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


# Include API routers
app.include_router(data.router, prefix="/api/v1/data", tags=["Data Management"])
app.include_router(forecast.router, prefix="/api/v1/forecast", tags=["Demand Forecasting"])
app.include_router(pricing.router, prefix="/api/v1/pricing", tags=["Pricing Optimization"])
app.include_router(inventory.router, prefix="/api/v1/inventory", tags=["Inventory Intelligence"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["Analytics Dashboard"])
app.include_router(copilot.router, prefix="/api/v1/copilot", tags=["AI Copilot"])


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Welcome to SmartShelf AI API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "status": "operational"
    }


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    try:
        # Check database connection
        stats = get_database_stats()
        
        return {
            "status": "healthy",
            "timestamp": time.time(),
            "database": "connected",
            "stats": {
                "products": stats.get("products", 0),
                "sales": stats.get("sales", 0),
                "inventory_records": stats.get("inventory_records", 0)
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "timestamp": time.time(),
                "error": str(e)
            }
        )


# API info endpoint
@app.get("/api/info", tags=["API Info"])
async def api_info():
    """Get API information and statistics."""
    try:
        stats = get_database_stats()
        
        return {
            "api_name": "SmartShelf AI",
            "version": "1.0.0",
            "description": "Intelligent retail analytics platform",
            "endpoints": {
                "data_management": "/api/v1/data",
                "demand_forecasting": "/api/v1/forecast",
                "pricing_optimization": "/api/v1/pricing",
                "inventory_intelligence": "/api/v1/inventory",
                "analytics_dashboard": "/api/v1/analytics",
                "ai_copilot": "/api/v1/copilot"
            },
            "database_stats": stats,
            "features": [
                "🤖 AI-powered demand forecasting",
                "💰 Dynamic pricing optimization",
                "📦 Intelligent inventory management",
                "📊 Real-time analytics dashboard",
                "🎯 Context-aware AI copilot",
                "📈 Business intelligence insights"
            ]
        }
    except Exception as e:
        logger.error(f"API info endpoint failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to get API information")


# Global exception handler
@app.exception_handler(SmartShelfException)
async def smartshelf_exception_handler(request, exc: SmartShelfException):
    """Handle custom SmartShelf exceptions."""
    logger.error(f"SmartShelf exception: {exc.message}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "type": exc.error_type,
                "message": exc.message,
                "details": exc.details
            }
        }
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "type": "http_exception",
                "message": exc.detail,
                "status_code": exc.status_code
            }
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc: Exception):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "type": "internal_server_error",
                "message": "An unexpected error occurred",
                "details": str(exc) if app.debug else None
            }
        }
    )


# Startup event (deprecated in favor of lifespan, but kept for reference)
@app.on_event("startup")
async def startup_event():
    """Startup event handler."""
    logger.info("SmartShelf AI Backend is ready!")


# Shutdown event (deprecated in favor of lifespan, but kept for reference)
@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event handler."""
    logger.info("SmartShelf AI Backend is shutting down.")


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
