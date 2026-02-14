"""
Intelligent AI Backend - Memory and Context Management System
Production-grade OOP implementation for conversation memory and context persistence
"""

import json
import pickle
import sqlite3
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)


class MemoryType(Enum):
    """Enumeration of memory types"""
    SHORT_TERM = "short_term"
    LONG_TERM = "long_term"
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    WORKING = "working"


class ContextScope(Enum):
    """Enumeration of context scopes"""
    SESSION = "session"
    USER = "user"
    GLOBAL = "global"
    TOPIC = "topic"


@dataclass
class MemoryItem:
    """Data class for memory items"""
    id: str
    type: MemoryType
    scope: ContextScope
    content: Dict[str, Any]
    timestamp: datetime
    expiration: Optional[datetime] = None
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    importance_score: float = 0.5
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ContextSnapshot:
    """Data class for context snapshots"""
    id: str
    user_id: str
    session_id: str
    context: Dict[str, Any]
    timestamp: datetime
    intent_history: List[str]
    entity_history: Dict[str, List[Any]]
    conversation_state: str
    summary: str


class MemoryStorage(ABC):
    """Abstract base class for memory storage"""
    
    @abstractmethod
    def store_memory(self, memory: MemoryItem) -> bool:
        """Store a memory item"""
        pass
    
    @abstractmethod
    def retrieve_memory(self, memory_id: str) -> Optional[MemoryItem]:
        """Retrieve a memory item by ID"""
        pass
    
    @abstractmethod
    def search_memories(self, query: Dict[str, Any]) -> List[MemoryItem]:
        """Search memories based on query"""
        pass
    
    @abstractmethod
    def delete_memory(self, memory_id: str) -> bool:
        """Delete a memory item"""
        pass
    
    @abstractmethod
    def cleanup_expired(self) -> int:
        """Clean up expired memories"""
        pass


class SQLiteMemoryStorage(MemoryStorage):
    """SQLite-based memory storage implementation"""
    
    def __init__(self, db_path: str = "memory.db"):
        self.db_path = db_path
        self._initialize_database()
        logger.info(f"SQLite Memory Storage initialized at {db_path}")
    
    def _initialize_database(self):
        """Initialize the database schema"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    id TEXT PRIMARY KEY,
                    type TEXT NOT NULL,
                    scope TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    expiration TEXT,
                    access_count INTEGER DEFAULT 0,
                    last_accessed TEXT,
                    importance_score REAL DEFAULT 0.5,
                    tags TEXT,
                    metadata TEXT
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS context_snapshots (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    context TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    intent_history TEXT,
                    entity_history TEXT,
                    conversation_state TEXT,
                    summary TEXT
                )
            """)
            
            # Create indexes for better performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_memories_type ON memories(type)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_memories_scope ON memories(scope)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_memories_timestamp ON memories(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_context_user ON context_snapshots(user_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_context_session ON context_snapshots(session_id)")
            
            conn.commit()
    
    def store_memory(self, memory: MemoryItem) -> bool:
        """Store a memory item"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO memories 
                    (id, type, scope, content, timestamp, expiration, access_count, 
                     last_accessed, importance_score, tags, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    memory.id,
                    memory.type.value,
                    memory.scope.value,
                    json.dumps(memory.content),
                    memory.timestamp.isoformat(),
                    memory.expiration.isoformat() if memory.expiration else None,
                    memory.access_count,
                    memory.last_accessed.isoformat() if memory.last_accessed else None,
                    memory.importance_score,
                    json.dumps(memory.tags),
                    json.dumps(memory.metadata)
                ))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error storing memory: {str(e)}")
            return False
    
    def retrieve_memory(self, memory_id: str) -> Optional[MemoryItem]:
        """Retrieve a memory item by ID"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT id, type, scope, content, timestamp, expiration, access_count,
                           last_accessed, importance_score, tags, metadata
                    FROM memories WHERE id = ?
                """, (memory_id,))
                
                row = cursor.fetchone()
                if row:
                    return self._row_to_memory(row)
                return None
        except Exception as e:
            logger.error(f"Error retrieving memory: {str(e)}")
            return None
    
    def search_memories(self, query: Dict[str, Any]) -> List[MemoryItem]:
        """Search memories based on query"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                sql = "SELECT id, type, scope, content, timestamp, expiration, access_count, last_accessed, importance_score, tags, metadata FROM memories WHERE 1=1"
                params = []
                
                if 'type' in query:
                    sql += " AND type = ?"
                    params.append(query['type'])
                
                if 'scope' in query:
                    sql += " AND scope = ?"
                    params.append(query['scope'])
                
                if 'user_id' in query:
                    sql += " AND json_extract(metadata, '$.user_id') = ?"
                    params.append(query['user_id'])
                
                if 'session_id' in query:
                    sql += " AND json_extract(metadata, '$.session_id') = ?"
                    params.append(query['session_id'])
                
                if 'tags' in query:
                    for tag in query['tags']:
                        sql += " AND tags LIKE ?"
                        params.append(f'%"{tag}"%')
                
                if 'limit' in query:
                    sql += f" LIMIT {query['limit']}"
                
                cursor = conn.execute(sql, params)
                rows = cursor.fetchall()
                
                return [self._row_to_memory(row) for row in rows]
        except Exception as e:
            logger.error(f"Error searching memories: {str(e)}")
            return []
    
    def delete_memory(self, memory_id: str) -> bool:
        """Delete a memory item"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error deleting memory: {str(e)}")
            return False
    
    def cleanup_expired(self) -> int:
        """Clean up expired memories"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    DELETE FROM memories 
                    WHERE expiration IS NOT NULL AND expiration < ?
                """, (datetime.now().isoformat(),))
                
                conn.commit()
                return cursor.rowcount
        except Exception as e:
            logger.error(f"Error cleaning up expired memories: {str(e)}")
            return 0
    
    def _row_to_memory(self, row) -> MemoryItem:
        """Convert database row to MemoryItem"""
        return MemoryItem(
            id=row[0],
            type=MemoryType(row[1]),
            scope=ContextScope(row[2]),
            content=json.loads(row[3]),
            timestamp=datetime.fromisoformat(row[4]),
            expiration=datetime.fromisoformat(row[5]) if row[5] else None,
            access_count=row[6],
            last_accessed=datetime.fromisoformat(row[7]) if row[7] else None,
            importance_score=row[8],
            tags=json.loads(row[9]) if row[9] else [],
            metadata=json.loads(row[10]) if row[10] else {}
        )
    
    def store_context_snapshot(self, snapshot: ContextSnapshot) -> bool:
        """Store a context snapshot"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO context_snapshots 
                    (id, user_id, session_id, context, timestamp, intent_history, 
                     entity_history, conversation_state, summary)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    snapshot.id,
                    snapshot.user_id,
                    snapshot.session_id,
                    json.dumps(snapshot.context),
                    snapshot.timestamp.isoformat(),
                    json.dumps(snapshot.intent_history),
                    json.dumps(snapshot.entity_history),
                    snapshot.conversation_state,
                    snapshot.summary
                ))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error storing context snapshot: {str(e)}")
            return False
    
    def get_context_snapshots(self, user_id: str, session_id: Optional[str] = None, 
                            limit: int = 10) -> List[ContextSnapshot]:
        """Get context snapshots for a user or session"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                sql = """
                    SELECT id, user_id, session_id, context, timestamp, intent_history,
                           entity_history, conversation_state, summary
                    FROM context_snapshots WHERE user_id = ?
                """
                params = [user_id]
                
                if session_id:
                    sql += " AND session_id = ?"
                    params.append(session_id)
                
                sql += " ORDER BY timestamp DESC LIMIT ?"
                params.append(limit)
                
                cursor = conn.execute(sql, params)
                rows = cursor.fetchall()
                
                snapshots = []
                for row in rows:
                    snapshots.append(ContextSnapshot(
                        id=row[0],
                        user_id=row[1],
                        session_id=row[2],
                        context=json.loads(row[3]),
                        timestamp=datetime.fromisoformat(row[4]),
                        intent_history=json.loads(row[5]) if row[5] else [],
                        entity_history=json.loads(row[6]) if row[6] else {},
                        conversation_state=row[7],
                        summary=row[8]
                    ))
                
                return snapshots
        except Exception as e:
            logger.error(f"Error getting context snapshots: {str(e)}")
            return []


class MemoryManager:
    """Main memory management system"""
    
    def __init__(self, storage: MemoryStorage):
        self.storage = storage
        self.memory_policies = self._initialize_memory_policies()
        self.context_cache = {}
        logger.info("Memory Manager initialized")
    
    def _initialize_memory_policies(self) -> Dict[MemoryType, Dict[str, Any]]:
        """Initialize memory retention policies"""
        return {
            MemoryType.SHORT_TERM: {
                'default_ttl': timedelta(hours=1),
                'max_count': 100,
                'importance_threshold': 0.3
            },
            MemoryType.LONG_TERM: {
                'default_ttl': timedelta(days=30),
                'max_count': 1000,
                'importance_threshold': 0.7
            },
            MemoryType.EPISODIC: {
                'default_ttl': timedelta(days=7),
                'max_count': 500,
                'importance_threshold': 0.5
            },
            MemoryType.SEMANTIC: {
                'default_ttl': None,  # Never expires
                'max_count': 2000,
                'importance_threshold': 0.8
            },
            MemoryType.WORKING: {
                'default_ttl': timedelta(minutes=30),
                'max_count': 50,
                'importance_threshold': 0.2
            }
        }
    
    def store_memory(self, content: Dict[str, Any], memory_type: MemoryType, 
                    scope: ContextScope, user_id: str = None, session_id: str = None,
                    importance_score: float = 0.5, tags: List[str] = None,
                    ttl: Optional[timedelta] = None) -> str:
        """Store a new memory item"""
        
        # Generate unique ID
        memory_id = f"{memory_type.value}_{scope.value}_{datetime.now().timestamp()}"
        
        # Calculate expiration
        policy = self.memory_policies[memory_type]
        expiration = None
        if ttl:
            expiration = datetime.now() + ttl
        elif policy['default_ttl']:
            expiration = datetime.now() + policy['default_ttl']
        
        # Create memory item
        memory = MemoryItem(
            id=memory_id,
            type=memory_type,
            scope=scope,
            content=content,
            timestamp=datetime.now(),
            expiration=expiration,
            importance_score=importance_score,
            tags=tags or [],
            metadata={
                'user_id': user_id,
                'session_id': session_id
            }
        )
        
        # Store memory
        success = self.storage.store_memory(memory)
        if success:
            logger.info(f"Stored memory {memory_id} of type {memory_type.value}")
            return memory_id
        else:
            logger.error(f"Failed to store memory {memory_id}")
            return None
    
    def retrieve_memory(self, memory_id: str) -> Optional[MemoryItem]:
        """Retrieve a memory item and update access statistics"""
        memory = self.storage.retrieve_memory(memory_id)
        
        if memory:
            # Update access statistics
            memory.access_count += 1
            memory.last_accessed = datetime.now()
            self.storage.store_memory(memory)
        
        return memory
    
    def search_memories(self, query: Dict[str, Any]) -> List[MemoryItem]:
        """Search memories based on query parameters"""
        return self.storage.search_memories(query)
    
    def get_user_memories(self, user_id: str, memory_type: Optional[MemoryType] = None,
                         limit: int = 50) -> List[MemoryItem]:
        """Get memories for a specific user"""
        query = {'user_id': user_id, 'limit': limit}
        if memory_type:
            query['type'] = memory_type.value
        
        return self.search_memories(query)
    
    def get_session_memories(self, session_id: str, limit: int = 20) -> List[MemoryItem]:
        """Get memories for a specific session"""
        query = {'session_id': session_id, 'limit': limit}
        return self.search_memories(query)
    
    def store_conversation_context(self, user_id: str, session_id: str, 
                                 context: Dict[str, Any], intent_history: List[str],
                                 entity_history: Dict[str, List[Any]], 
                                 conversation_state: str, summary: str = "") -> str:
        """Store conversation context snapshot"""
        
        snapshot_id = f"context_{session_id}_{datetime.now().timestamp()}"
        
        snapshot = ContextSnapshot(
            id=snapshot_id,
            user_id=user_id,
            session_id=session_id,
            context=context,
            timestamp=datetime.now(),
            intent_history=intent_history,
            entity_history=entity_history,
            conversation_state=conversation_state,
            summary=summary
        )
        
        success = self.storage.store_context_snapshot(snapshot)
        if success:
            # Also store as episodic memory
            self.store_memory(
                content={
                    'context': context,
                    'intent_history': intent_history,
                    'entity_history': entity_history,
                    'conversation_state': conversation_state,
                    'summary': summary
                },
                memory_type=MemoryType.EPISODIC,
                scope=ContextScope.SESSION,
                user_id=user_id,
                session_id=session_id,
                importance_score=0.6,
                tags=['conversation', 'context']
            )
            
            logger.info(f"Stored conversation context for session {session_id}")
            return snapshot_id
        else:
            logger.error(f"Failed to store conversation context for session {session_id}")
            return None
    
    def get_conversation_history(self, user_id: str, session_id: Optional[str] = None,
                               limit: int = 10) -> List[ContextSnapshot]:
        """Get conversation history for a user or session"""
        return self.storage.get_context_snapshots(user_id, session_id, limit)
    
    def update_memory_importance(self, memory_id: str, new_score: float) -> bool:
        """Update the importance score of a memory"""
        memory = self.retrieve_memory(memory_id)
        if memory:
            memory.importance_score = new_score
            return self.storage.store_memory(memory)
        return False
    
    def add_memory_tags(self, memory_id: str, tags: List[str]) -> bool:
        """Add tags to a memory"""
        memory = self.retrieve_memory(memory_id)
        if memory:
            memory.tags.extend(tag for tag in tags if tag not in memory.tags)
            return self.storage.store_memory(memory)
        return False
    
    def cleanup_memories(self) -> Dict[str, int]:
        """Clean up expired and low-importance memories"""
        cleanup_stats = {
            'expired': 0,
            'low_importance': 0,
            'over_limit': 0
        }
        
        # Clean up expired memories
        cleanup_stats['expired'] = self.storage.cleanup_expired()
        
        # Clean up low importance memories for each type
        for memory_type, policy in self.memory_policies.items():
            memories = self.search_memories({
                'type': memory_type.value,
                'limit': policy['max_count'] * 2  # Get more to evaluate
            })
            
            # Sort by importance and access count
            memories.sort(key=lambda m: (m.importance_score, m.access_count))
            
            # Remove memories below threshold and over limit
            memories_to_remove = []
            for i, memory in enumerate(memories):
                if (i >= policy['max_count'] or 
                    memory.importance_score < policy['importance_threshold']):
                    memories_to_remove.append(memory.id)
            
            for memory_id in memories_to_remove:
                if self.storage.delete_memory(memory_id):
                    cleanup_stats['low_importance'] += 1
        
        logger.info(f"Memory cleanup completed: {cleanup_stats}")
        return cleanup_stats
    
    def get_memory_statistics(self) -> Dict[str, Any]:
        """Get memory system statistics"""
        stats = {
            'total_memories': 0,
            'by_type': {},
            'by_scope': {},
            'average_importance': 0.0,
            'expired_count': 0
        }
        
        # Get all memories (with reasonable limit)
        all_memories = self.search_memories({'limit': 1000})
        stats['total_memories'] = len(all_memories)
        
        if all_memories:
            # Calculate statistics
            importance_scores = []
            for memory in all_memories:
                # Count by type
                type_key = memory.type.value
                stats['by_type'][type_key] = stats['by_type'].get(type_key, 0) + 1
                
                # Count by scope
                scope_key = memory.scope.value
                stats['by_scope'][scope_key] = stats['by_scope'].get(scope_key, 0) + 1
                
                # Collect importance scores
                importance_scores.append(memory.importance_score)
                
                # Count expired
                if memory.expiration and memory.expiration < datetime.now():
                    stats['expired_count'] += 1
            
            # Calculate average importance
            stats['average_importance'] = sum(importance_scores) / len(importance_scores)
        
        return stats


class ContextManager:
    """Context management for conversations"""
    
    def __init__(self, memory_manager: MemoryManager):
        self.memory_manager = memory_manager
        self.active_contexts = {}  # In-memory cache for active sessions
        logger.info("Context Manager initialized")
    
    def update_context(self, session_id: str, user_id: str, context: Dict[str, Any],
                      intent: str, entities: Dict[str, Any], conversation_state: str):
        """Update context for a conversation session"""
        
        # Get or create active context
        if session_id not in self.active_contexts:
            self.active_contexts[session_id] = {
                'user_id': user_id,
                'context': {},
                'intent_history': [],
                'entity_history': {},
                'conversation_state': 'initial',
                'last_updated': datetime.now()
            }
        
        active_ctx = self.active_contexts[session_id]
        
        # Update context
        active_ctx['context'].update(context)
        active_ctx['intent_history'].append(intent)
        active_ctx['conversation_state'] = conversation_state
        active_ctx['last_updated'] = datetime.now()
        
        # Update entity history
        for entity_type, entity_values in entities.items():
            if entity_type not in active_ctx['entity_history']:
                active_ctx['entity_history'][entity_type] = []
            
            for value in entity_values:
                if value not in active_ctx['entity_history'][entity_type]:
                    active_ctx['entity_history'][entity_type].append(value)
        
        # Store in memory periodically (every 5 messages or state change)
        if (len(active_ctx['intent_history']) % 5 == 0 or 
            conversation_state != active_ctx.get('previous_state', conversation_state)):
            
            summary = self._generate_context_summary(active_ctx)
            self.memory_manager.store_conversation_context(
                user_id=user_id,
                session_id=session_id,
                context=active_ctx['context'],
                intent_history=active_ctx['intent_history'][-10:],  # Last 10 intents
                entity_history=active_ctx['entity_history'],
                conversation_state=conversation_state,
                summary=summary
            )
            
            active_ctx['previous_state'] = conversation_state
        
        # Store working memory
        self.memory_manager.store_memory(
            content={
                'session_context': active_ctx['context'],
                'last_intent': intent,
                'last_entities': entities
            },
            memory_type=MemoryType.WORKING,
            scope=ContextScope.SESSION,
            user_id=user_id,
            session_id=session_id,
            importance_score=0.3,
            tags=['working', 'session']
        )
    
    def get_context(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get current context for a session"""
        if session_id in self.active_contexts:
            return self.active_contexts[session_id]
        
        # Try to retrieve from memory
        memories = self.memory_manager.get_session_memories(session_id, limit=1)
        if memories:
            latest_memory = memories[0]
            return {
                'context': latest_memory.content.get('session_context', {}),
                'intent_history': [],
                'entity_history': {},
                'conversation_state': 'recovered',
                'last_updated': latest_memory.timestamp
            }
        
        return None
    
    def get_relevant_context(self, user_id: str, current_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get relevant context from user's conversation history"""
        
        # Get recent conversation snapshots
        snapshots = self.memory_manager.get_conversation_history(user_id, limit=5)
        
        relevant_contexts = []
        for snapshot in snapshots:
            # Calculate relevance based on context similarity
            relevance_score = self._calculate_context_relevance(
                current_context, snapshot.context
            )
            
            if relevance_score > 0.3:  # Threshold for relevance
                relevant_contexts.append({
                    'snapshot': snapshot,
                    'relevance_score': relevance_score,
                    'context': snapshot.context
                })
        
        # Sort by relevance
        relevant_contexts.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        return relevant_contexts[:3]  # Return top 3 most relevant
    
    def _generate_context_summary(self, context_data: Dict[str, Any]) -> str:
        """Generate a summary of the conversation context"""
        intents = context_data.get('intent_history', [])
        entities = context_data.get('entity_history', {})
        state = context_data.get('conversation_state', 'unknown')
        
        summary_parts = []
        
        if intents:
            most_common_intent = max(set(intents[-5:]), key=intents[-5:].count) if len(intents) >= 5 else intents[-1]
            summary_parts.append(f"Primary intent: {most_common_intent}")
        
        if entities:
            entity_types = list(entities.keys())
            summary_parts.append(f"Topics: {', '.join(entity_types[:3])}")
        
        summary_parts.append(f"State: {state}")
        
        return " | ".join(summary_parts)
    
    def _calculate_context_relevance(self, current_context: Dict[str, Any], 
                                   historical_context: Dict[str, Any]) -> float:
        """Calculate relevance score between current and historical context"""
        
        # Simple relevance calculation based on overlapping keys and values
        current_keys = set(current_context.keys())
        historical_keys = set(historical_context.keys())
        
        # Key overlap
        key_overlap = len(current_keys & historical_keys) / len(current_keys | historical_keys) if current_keys | historical_keys else 0
        
        # Value similarity for common keys
        value_similarity = 0.0
        common_keys = current_keys & historical_keys
        
        if common_keys:
            similarity_scores = []
            for key in common_keys:
                current_val = str(current_context[key])
                historical_val = str(historical_context[key])
                
                # Simple string similarity
                common_chars = set(current_val.lower()) & set(historical_val.lower())
                total_chars = set(current_val.lower()) | set(historical_val.lower())
                
                if total_chars:
                    similarity_scores.append(len(common_chars) / len(total_chars))
            
            if similarity_scores:
                value_similarity = sum(similarity_scores) / len(similarity_scores)
        
        # Combine scores
        relevance = (key_overlap * 0.6) + (value_similarity * 0.4)
        
        return relevance
    
    def clear_session_context(self, session_id: str):
        """Clear context for a specific session"""
        if session_id in self.active_contexts:
            del self.active_contexts[session_id]
        
        # Clean up working memories for this session
        memories = self.memory_manager.search_memories({
            'session_id': session_id,
            'type': MemoryType.WORKING.value
        })
        
        for memory in memories:
            self.memory_manager.storage.delete_memory(memory.id)
        
        logger.info(f"Cleared context for session {session_id}")
    
    def cleanup_inactive_contexts(self, max_age_hours: int = 24):
        """Clean up inactive contexts from memory"""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        
        inactive_sessions = []
        for session_id, context in self.active_contexts.items():
            if context['last_updated'] < cutoff_time:
                inactive_sessions.append(session_id)
        
        for session_id in inactive_sessions:
            self.clear_session_context(session_id)
        
        logger.info(f"Cleaned up {len(inactive_sessions)} inactive contexts")
        return len(inactive_sessions)


# Factory function for easy instantiation
def create_memory_system(db_path: str = "memory.db") -> Tuple[MemoryManager, ContextManager]:
    """Factory function to create complete memory system"""
    storage = SQLiteMemoryStorage(db_path)
    memory_manager = MemoryManager(storage)
    context_manager = ContextManager(memory_manager)
    
    return memory_manager, context_manager


if __name__ == "__main__":
    # Test the memory system
    memory_manager, context_manager = create_memory_system("test_memory.db")
    
    # Test storing and retrieving memories
    print("=== Memory System Test ===")
    
    # Store some test memories
    memory_id1 = memory_manager.store_memory(
        content={"message": "Hello", "intent": "greeting"},
        memory_type=MemoryType.SHORT_TERM,
        scope=ContextScope.SESSION,
        user_id="test_user",
        session_id="test_session",
        importance_score=0.7,
        tags=["test", "greeting"]
    )
    
    memory_id2 = memory_manager.store_memory(
        content={"product": "laptop", "budget": "$1000"},
        memory_type=MemoryType.EPISODIC,
        scope=ContextScope.USER,
        user_id="test_user",
        importance_score=0.8,
        tags=["product", "laptop"]
    )
    
    print(f"Stored memories: {memory_id1}, {memory_id2}")
    
    # Retrieve memories
    memory1 = memory_manager.retrieve_memory(memory_id1)
    if memory1:
        print(f"Retrieved memory: {memory1.content}")
    
    # Search memories
    user_memories = memory_manager.get_user_memories("test_user")
    print(f"User memories: {len(user_memories)}")
    
    # Test context management
    context_manager.update_context(
        session_id="test_session",
        user_id="test_user",
        context={"current_topic": "laptops"},
        intent="product_inquiry",
        entities={"product_type": ["laptop"]},
        conversation_state="information_gathering"
    )
    
    context = context_manager.get_context("test_session")
    if context:
        print(f"Retrieved context: {context['conversation_state']}")
    
    # Get statistics
    stats = memory_manager.get_memory_statistics()
    print(f"Memory statistics: {stats}")
    
    print("Memory system test completed!")
