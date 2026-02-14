"""
Real-time communication module for SmartShelf AI
"""

from .websocket_manager import WebSocketManager, ConnectionManager
from .events import EventType, EventManager
from .presence import PresenceManager

__all__ = [
    'WebSocketManager',
    'ConnectionManager', 
    'EventType',
    'EventManager',
    'PresenceManager'
]
