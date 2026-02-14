"""
WebSocket manager for real-time communication
"""

import asyncio
import json
import logging
from typing import Dict, List, Set, Optional, Any
from datetime import datetime
from enum import Enum
import uuid

from fastapi import WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from ..monitoring.logger import get_logger
from ..monitoring.metrics import metrics
from ..monitoring.error_tracker import track_error, ErrorSeverity, ErrorCategory

logger = get_logger(__name__)


class EventType(str, Enum):
    """WebSocket event types"""
    MESSAGE = "message"
    TYPING = "typing"
    STOP_TYPING = "stop_typing"
    USER_ONLINE = "user_online"
    USER_OFFLINE = "user_offline"
    SESSION_CREATED = "session_created"
    SESSION_UPDATED = "session_updated"
    PRODUCT_SUGGESTION = "product_suggestion"
    NOTIFICATION = "notification"
    ERROR = "error"


class WebSocketMessage(BaseModel):
    """WebSocket message model"""
    type: EventType
    data: Dict[str, Any]
    timestamp: datetime
    user_id: Optional[int] = None
    session_id: Optional[str] = None
    message_id: Optional[str] = None


class ConnectionManager:
    """Manages WebSocket connections"""
    
    def __init__(self):
        # Store active connections by user_id
        self.active_connections: Dict[int, Set[WebSocket]] = {}
        # Store connection metadata
        self.connection_metadata: Dict[WebSocket, Dict[str, Any]] = {}
        # Store sessions by connection
        self.connection_sessions: Dict[WebSocket, str] = {}
        # Store typing indicators
        self.typing_users: Dict[str, Set[int]] = {}
        
    async def connect(self, websocket: WebSocket, user_id: int, session_id: str):
        """Connect a new WebSocket client"""
        try:
            await websocket.accept()
            
            # Add to user connections
            if user_id not in self.active_connections:
                self.active_connections[user_id] = set()
            self.active_connections[user_id].add(websocket)
            
            # Store metadata
            self.connection_metadata[websocket] = {
                'user_id': user_id,
                'session_id': session_id,
                'connected_at': datetime.utcnow(),
                'last_activity': datetime.utcnow()
            }
            
            # Store session mapping
            self.connection_sessions[websocket] = session_id
            
            # Update metrics
            metrics.set_custom_metric('active_connections', len(self.connection_metadata))
            
            logger.info(f"WebSocket connected: user_id={user_id}, session_id={session_id}")
            
            # Broadcast user online status
            await self.broadcast_to_session(session_id, {
                'type': EventType.USER_ONLINE,
                'data': {'user_id': user_id},
                'timestamp': datetime.utcnow().isoformat()
            }, exclude_websocket=websocket)
            
        except Exception as e:
            logger.error(f"WebSocket connection failed: {e}")
            track_error(e, ErrorSeverity.MEDIUM, ErrorCategory.NETWORK, "websocket_connect")
            raise
    
    async def disconnect(self, websocket: WebSocket):
        """Disconnect a WebSocket client"""
        try:
            metadata = self.connection_metadata.get(websocket)
            if metadata:
                user_id = metadata['user_id']
                session_id = metadata['session_id']
                
                # Remove from user connections
                if user_id in self.active_connections:
                    self.active_connections[user_id].discard(websocket)
                    if not self.active_connections[user_id]:
                        del self.active_connections[user_id]
                
                # Remove from typing indicators
                if session_id in self.typing_users:
                    self.typing_users[session_id].discard(user_id)
                
                # Clean up metadata
                del self.connection_metadata[websocket]
                del self.connection_sessions[websocket]
                
                # Update metrics
                metrics.set_custom_metric('active_connections', len(self.connection_metadata))
                
                logger.info(f"WebSocket disconnected: user_id={user_id}, session_id={session_id}")
                
                # Broadcast user offline status
                await self.broadcast_to_session(session_id, {
                    'type': EventType.USER_OFFLINE,
                    'data': {'user_id': user_id},
                    'timestamp': datetime.utcnow().isoformat()
                })
        
        except Exception as e:
            logger.error(f"WebSocket disconnection error: {e}")
    
    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket):
        """Send a message to a specific WebSocket connection"""
        try:
            await websocket.send_text(json.dumps(message))
            
            # Update last activity
            if websocket in self.connection_metadata:
                self.connection_metadata[websocket]['last_activity'] = datetime.utcnow()
                
        except Exception as e:
            logger.error(f"Failed to send personal message: {e}")
            track_error(e, ErrorSeverity.LOW, ErrorCategory.NETWORK, "websocket_send")
    
    async def broadcast_to_user(self, user_id: int, message: Dict[str, Any]):
        """Broadcast a message to all connections of a specific user"""
        if user_id not in self.active_connections:
            return
        
        # Send to all user connections
        disconnected = set()
        for websocket in self.active_connections[user_id]:
            try:
                await websocket.send_text(json.dumps(message))
                
                # Update last activity
                if websocket in self.connection_metadata:
                    self.connection_metadata[websocket]['last_activity'] = datetime.utcnow()
                    
            except Exception as e:
                logger.warning(f"Failed to send to user {user_id}: {e}")
                disconnected.add(websocket)
        
        # Clean up disconnected websockets
        for websocket in disconnected:
            await self.disconnect(websocket)
    
    async def broadcast_to_session(self, session_id: str, message: Dict[str, Any], exclude_websocket: Optional[WebSocket] = None):
        """Broadcast a message to all users in a session"""
        sent_count = 0
        disconnected = set()
        
        for websocket, metadata in self.connection_metadata.items():
            if metadata['session_id'] == session_id and websocket != exclude_websocket:
                try:
                    await websocket.send_text(json.dumps(message))
                    sent_count += 1
                    
                    # Update last activity
                    metadata['last_activity'] = datetime.utcnow()
                    
                except Exception as e:
                    logger.warning(f"Failed to broadcast to session {session_id}: {e}")
                    disconnected.add(websocket)
        
        # Clean up disconnected websockets
        for websocket in disconnected:
            await self.disconnect(websocket)
        
        logger.debug(f"Broadcasted to {sent_count} connections in session {session_id}")
    
    async def broadcast_to_all(self, message: Dict[str, Any]):
        """Broadcast a message to all connected clients"""
        sent_count = 0
        disconnected = set()
        
        for websocket in list(self.connection_metadata.keys()):
            try:
                await websocket.send_text(json.dumps(message))
                sent_count += 1
                
                # Update last activity
                if websocket in self.connection_metadata:
                    self.connection_metadata[websocket]['last_activity'] = datetime.utcnow()
                    
            except Exception as e:
                logger.warning(f"Failed to broadcast to all: {e}")
                disconnected.add(websocket)
        
        # Clean up disconnected websockets
        for websocket in disconnected:
            await self.disconnect(websocket)
        
        logger.debug(f"Broadcasted to {sent_count} total connections")
    
    async def handle_typing(self, websocket: WebSocket, is_typing: bool):
        """Handle typing indicators"""
        metadata = self.connection_metadata.get(websocket)
        if not metadata:
            return
        
        user_id = metadata['user_id']
        session_id = metadata['session_id']
        
        # Update typing state
        if session_id not in self.typing_users:
            self.typing_users[session_id] = set()
        
        if is_typing:
            self.typing_users[session_id].add(user_id)
            event_type = EventType.TYPING
        else:
            self.typing_users[session_id].discard(user_id)
            event_type = EventType.STOP_TYPING
        
        # Broadcast typing status to session
        await self.broadcast_to_session(session_id, {
            'type': event_type,
            'data': {'user_id': user_id},
            'timestamp': datetime.utcnow().isoformat()
        }, exclude_websocket=websocket)
    
    def get_session_users(self, session_id: str) -> List[int]:
        """Get all active users in a session"""
        users = set()
        for metadata in self.connection_metadata.values():
            if metadata['session_id'] == session_id:
                users.add(metadata['user_id'])
        return list(users)
    
    def get_user_sessions(self, user_id: int) -> List[str]:
        """Get all active sessions for a user"""
        sessions = set()
        for metadata in self.connection_metadata.values():
            if metadata['user_id'] == user_id:
                sessions.add(metadata['session_id'])
        return list(sessions)
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection statistics"""
        return {
            'total_connections': len(self.connection_metadata),
            'active_users': len(self.active_connections),
            'typing_sessions': len(self.typing_users),
            'connections_by_user': {
                user_id: len(connections) 
                for user_id, connections in self.active_connections.items()
            }
        }


class WebSocketManager:
    """High-level WebSocket manager with event handling"""
    
    def __init__(self):
        self.connection_manager = ConnectionManager()
        self.event_handlers = {}
        
    def register_handler(self, event_type: EventType, handler):
        """Register an event handler"""
        self.event_handlers[event_type] = handler
    
    async def handle_websocket(self, websocket: WebSocket, user_id: int, session_id: str):
        """Handle WebSocket connection lifecycle"""
        await self.connection_manager.connect(websocket, user_id, session_id)
        
        try:
            while True:
                # Receive message
                data = await websocket.receive_text()
                
                try:
                    message_data = json.loads(data)
                    message_type = message_data.get('type')
                    
                    # Handle different message types
                    if message_type == EventType.TYPING:
                        await self.connection_manager.handle_typing(websocket, True)
                    elif message_type == EventType.STOP_TYPING:
                        await self.connection_manager.handle_typing(websocket, False)
                    elif message_type == EventType.MESSAGE:
                        # Handle chat message
                        await self._handle_message(websocket, message_data)
                    else:
                        # Handle custom events
                        await self._handle_custom_event(websocket, message_data)
                
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON received: {data}")
                    await self.connection_manager.send_personal_message({
                        'type': EventType.ERROR,
                        'data': {'message': 'Invalid message format'},
                        'timestamp': datetime.utcnow().isoformat()
                    }, websocket)
                
        except WebSocketDisconnect:
            await self.connection_manager.disconnect(websocket)
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
            track_error(e, ErrorSeverity.MEDIUM, ErrorCategory.NETWORK, "websocket_handler")
            await self.connection_manager.disconnect(websocket)
    
    async def _handle_message(self, websocket: WebSocket, message_data: Dict[str, Any]):
        """Handle incoming chat message"""
        metadata = self.connection_manager.connection_metadata.get(websocket)
        if not metadata:
            return
        
        # Create message object
        message = WebSocketMessage(
            type=EventType.MESSAGE,
            data=message_data.get('data', {}),
            timestamp=datetime.utcnow(),
            user_id=metadata['user_id'],
            session_id=metadata['session_id'],
            message_id=str(uuid.uuid4())
        )
        
        # Broadcast to session
        await self.connection_manager.broadcast_to_session(
            metadata['session_id'],
            message.dict()
        )
        
        # Update metrics
        metrics.increment_chat_messages("user", metadata['session_id'])
    
    async def _handle_custom_event(self, websocket: WebSocket, message_data: Dict[str, Any]):
        """Handle custom events"""
        event_type = message_data.get('type')
        
        if event_type in self.event_handlers:
            try:
                await self.event_handlers[event_type](websocket, message_data)
            except Exception as e:
                logger.error(f"Event handler failed for {event_type}: {e}")
                track_error(e, ErrorSeverity.MEDIUM, ErrorCategory.BUSINESS_LOGIC, "event_handler")
    
    async def send_notification(self, user_id: int, notification: Dict[str, Any]):
        """Send notification to a specific user"""
        await self.connection_manager.broadcast_to_user(user_id, {
            'type': EventType.NOTIFICATION,
            'data': notification,
            'timestamp': datetime.utcnow().isoformat()
        })
    
    async def send_product_suggestion(self, session_id: str, products: List[Dict[str, Any]]):
        """Send product suggestions to a session"""
        await self.connection_manager.broadcast_to_session(session_id, {
            'type': EventType.PRODUCT_SUGGESTION,
            'data': {'products': products},
            'timestamp': datetime.utcnow().isoformat()
        })
    
    def get_stats(self) -> Dict[str, Any]:
        """Get WebSocket statistics"""
        return self.connection_manager.get_connection_stats()


# Global WebSocket manager instance
websocket_manager = WebSocketManager()
