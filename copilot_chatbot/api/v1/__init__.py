"""
SmartShelf AI - API v1 Module
Enhanced API endpoints with production features
"""

from .enhanced_chat import router as chat_router

__all__ = ["chat_router"]
