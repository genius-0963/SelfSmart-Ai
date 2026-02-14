"""
Database module for SmartShelf AI
"""

from .connection import get_db, engine, SessionLocal
from .models import Base, User, ChatSession, Message, Product, AnalyticsEvent, UserPreference

__all__ = [
    'get_db',
    'engine', 
    'SessionLocal',
    'Base',
    'User',
    'ChatSession',
    'Message',
    'Product',
    'AnalyticsEvent',
    'UserPreference'
]
