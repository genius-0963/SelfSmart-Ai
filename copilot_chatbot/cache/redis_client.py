"""
Redis client for caching and session management
"""

import json
import pickle
import asyncio
from typing import Any, Optional, Dict, List, Union
from datetime import datetime, timedelta
import redis.asyncio as redis
from redis.asyncio import Redis
import logging

from ..monitoring.logger import get_logger
from ..monitoring.metrics import metrics
from ..monitoring.error_tracker import track_error, ErrorSeverity, ErrorCategory

logger = get_logger(__name__)


class RedisClient:
    """Enhanced Redis client with caching strategies"""
    
    def __init__(self, redis_url: str = None, **redis_kwargs):
        """
        Initialize Redis client
        
        Args:
            redis_url: Redis connection URL
            **redis_kwargs: Additional Redis connection parameters
        """
        self.redis_url = redis_url or "redis://localhost:6379"
        self.redis_kwargs = redis_kwargs
        self._client: Optional[Redis] = None
        self._connection_pool = None
        
        # Default settings
        self.default_ttl = 3600  # 1 hour
        self.max_connections = 10
        
    async def connect(self):
        """Establish Redis connection"""
        try:
            self._client = Redis.from_url(
                self.redis_url,
                max_connections=self.max_connections,
                **self.redis_kwargs
            )
            
            # Test connection
            await self._client.ping()
            logger.info("✅ Redis connection established")
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to Redis: {e}")
            track_error(e, ErrorSeverity.HIGH, ErrorCategory.DATABASE, "redis_connect")
            raise
    
    async def disconnect(self):
        """Close Redis connection"""
        if self._client:
            await self._client.close()
            logger.info("Redis connection closed")
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache
        
        Args:
            key: Cache key
        
        Returns:
            Cached value or None
        """
        try:
            if not self._client:
                await self.connect()
            
            value = await self._client.get(key)
            
            if value is None:
                metrics.increment_cache_misses("general")
                return None
            
            # Deserialize value
            try:
                # Try JSON first
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                # Try pickle
                try:
                    return pickle.loads(value)
                except (pickle.PickleError, TypeError):
                    # Return as string
                    return value.decode('utf-8')
            
            metrics.increment_cache_hits("general")
            
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            track_error(e, ErrorSeverity.LOW, ErrorCategory.DATABASE, "cache_get")
            return None
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[int] = None,
        serialize_method: str = "json"
    ) -> bool:
        """
        Set value in cache
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (default: 3600)
            serialize_method: Serialization method ('json' or 'pickle')
        
        Returns:
            True if successful
        """
        try:
            if not self._client:
                await self.connect()
            
            # Serialize value
            if serialize_method == "json":
                serialized_value = json.dumps(value, default=str)
            elif serialize_method == "pickle":
                serialized_value = pickle.dumps(value)
            else:
                serialized_value = str(value)
            
            # Set with TTL
            ttl = ttl or self.default_ttl
            result = await self._client.setex(key, ttl, serialized_value)
            
            if result:
                logger.debug(f"Cache set: key={key}, ttl={ttl}")
            
            return bool(result)
            
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            track_error(e, ErrorSeverity.LOW, ErrorCategory.DATABASE, "cache_set")
            return False
    
    async def delete(self, key: str) -> bool:
        """
        Delete key from cache
        
        Args:
            key: Cache key
        
        Returns:
            True if key was deleted
        """
        try:
            if not self._client:
                await self.connect()
            
            result = await self._client.delete(key)
            return bool(result)
            
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            track_error(e, ErrorSeverity.LOW, ErrorCategory.DATABASE, "cache_delete")
            return False
    
    async def exists(self, key: str) -> bool:
        """
        Check if key exists in cache
        
        Args:
            key: Cache key
        
        Returns:
            True if key exists
        """
        try:
            if not self._client:
                await self.connect()
            
            result = await self._client.exists(key)
            return bool(result)
            
        except Exception as e:
            logger.error(f"Cache exists error for key {key}: {e}")
            return False
    
    async def expire(self, key: str, ttl: int) -> bool:
        """
        Set expiration for existing key
        
        Args:
            key: Cache key
            ttl: Time to live in seconds
        
        Returns:
            True if successful
        """
        try:
            if not self._client:
                await self.connect()
            
            result = await self._client.expire(key, ttl)
            return bool(result)
            
        except Exception as e:
            logger.error(f"Cache expire error for key {key}: {e}")
            return False
    
    async def ttl(self, key: str) -> int:
        """
        Get remaining time to live for key
        
        Args:
            key: Cache key
        
        Returns:
            TTL in seconds, -1 if no TTL, -2 if key doesn't exist
        """
        try:
            if not self._client:
                await self.connect()
            
            return await self._client.ttl(key)
            
        except Exception as e:
            logger.error(f"Cache TTL error for key {key}: {e}")
            return -2
    
    async def keys(self, pattern: str = "*") -> List[str]:
        """
        Get all keys matching pattern
        
        Args:
            pattern: Key pattern (default: "*")
        
        Returns:
            List of matching keys
        """
        try:
            if not self._client:
                await self.connect()
            
            keys = await self._client.keys(pattern)
            return [key.decode('utf-8') for key in keys]
            
        except Exception as e:
            logger.error(f"Cache keys error for pattern {pattern}: {e}")
            return []
    
    async def flushdb(self) -> bool:
        """
        Flush all keys from current database
        
        Returns:
            True if successful
        """
        try:
            if not self._client:
                await self.connect()
            
            result = await self._client.flushdb()
            logger.warning("Cache database flushed")
            return bool(result)
            
        except Exception as e:
            logger.error(f"Cache flush error: {e}")
            track_error(e, ErrorSeverity.MEDIUM, ErrorCategory.DATABASE, "cache_flush")
            return False
    
    # Hash operations
    async def hget(self, key: str, field: str) -> Optional[Any]:
        """Get field from hash"""
        try:
            if not self._client:
                await self.connect()
            
            value = await self._client.hget(key, field)
            if value is None:
                return None
            
            return json.loads(value) if value else None
            
        except Exception as e:
            logger.error(f"Cache hget error: {e}")
            return None
    
    async def hset(self, key: str, field: str, value: Any) -> bool:
        """Set field in hash"""
        try:
            if not self._client:
                await self.connect()
            
            serialized_value = json.dumps(value, default=str)
            result = await self._client.hset(key, field, serialized_value)
            return bool(result)
            
        except Exception as e:
            logger.error(f"Cache hset error: {e}")
            return False
    
    async def hgetall(self, key: str) -> Dict[str, Any]:
        """Get all fields from hash"""
        try:
            if not self._client:
                await self.connect()
            
            hash_data = await self._client.hgetall(key)
            result = {}
            
            for field, value in hash_data.items():
                field_str = field.decode('utf-8')
                try:
                    result[field_str] = json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    result[field_str] = value.decode('utf-8')
            
            return result
            
        except Exception as e:
            logger.error(f"Cache hgetall error: {e}")
            return {}
    
    # List operations
    async def lpush(self, key: str, *values: Any) -> int:
        """Push values to list head"""
        try:
            if not self._client:
                await self.connect()
            
            serialized_values = [json.dumps(v, default=str) for v in values]
            return await self._client.lpush(key, *serialized_values)
            
        except Exception as e:
            logger.error(f"Cache lpush error: {e}")
            return 0
    
    async def rpop(self, key: str) -> Optional[Any]:
        """Pop value from list tail"""
        try:
            if not self._client:
                await self.connect()
            
            value = await self._client.rpop(key)
            if value is None:
                return None
            
            return json.loads(value)
            
        except Exception as e:
            logger.error(f"Cache rpop error: {e}")
            return None
    
    async def lrange(self, key: str, start: int = 0, end: int = -1) -> List[Any]:
        """Get range of list values"""
        try:
            if not self._client:
                await self.connect()
            
            values = await self._client.lrange(key, start, end)
            result = []
            
            for value in values:
                try:
                    result.append(json.loads(value))
                except (json.JSONDecodeError, TypeError):
                    result.append(value.decode('utf-8'))
            
            return result
            
        except Exception as e:
            logger.error(f"Cache lrange error: {e}")
            return []
    
    # Set operations
    async def sadd(self, key: str, *members: Any) -> int:
        """Add members to set"""
        try:
            if not self._client:
                await self.connect()
            
            serialized_members = [json.dumps(m, default=str) for m in members]
            return await self._client.sadd(key, *serialized_members)
            
        except Exception as e:
            logger.error(f"Cache sadd error: {e}")
            return 0
    
    async def smembers(self, key: str) -> set:
        """Get all set members"""
        try:
            if not self._client:
                await self.connect()
            
            members = await self._client.smembers(key)
            result = set()
            
            for member in members:
                try:
                    result.add(json.loads(member))
                except (json.JSONDecodeError, TypeError):
                    result.add(member.decode('utf-8'))
            
            return result
            
        except Exception as e:
            logger.error(f"Cache smembers error: {e}")
            return set()
    
    async def sismember(self, key: str, member: Any) -> bool:
        """Check if member is in set"""
        try:
            if not self._client:
                await self.connect()
            
            serialized_member = json.dumps(member, default=str)
            return bool(await self._client.sismember(key, serialized_member))
            
        except Exception as e:
            logger.error(f"Cache sismember error: {e}")
            return False
    
    # Session management
    async def set_session(self, session_id: str, user_data: Dict[str, Any], ttl: int = 86400):
        """Set user session data"""
        key = f"session:{session_id}"
        await self.hset(key, "user_data", user_data)
        await self.expire(key, ttl)
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get user session data"""
        key = f"session:{session_id}"
        return await self.hget(key, "user_data")
    
    async def delete_session(self, session_id: str):
        """Delete user session"""
        key = f"session:{session_id}"
        await self.delete(key)
    
    # Rate limiting
    async def increment_rate_limit(self, key: str, limit: int, window: int) -> int:
        """
        Increment rate limit counter
        
        Args:
            key: Rate limit key
            limit: Maximum allowed requests
            window: Time window in seconds
        
        Returns:
            Current count
        """
        try:
            if not self._client:
                await self.connect()
            
            # Use Redis pipeline for atomic operations
            pipe = self._client.pipeline()
            pipe.incr(key)
            pipe.expire(key, window)
            results = await pipe.execute()
            
            current_count = results[0]
            
            # Update metrics
            if current_count > limit:
                metrics.increment_cache_hits("rate_limit_block")
            else:
                metrics.increment_cache_hits("rate_limit_allow")
            
            return current_count
            
        except Exception as e:
            logger.error(f"Rate limit error: {e}")
            return 0
    
    async def get_cache_info(self) -> Dict[str, Any]:
        """Get Redis cache information"""
        try:
            if not self._client:
                await self.connect()
            
            info = await self._client.info()
            
            return {
                'redis_version': info.get('redis_version'),
                'used_memory': info.get('used_memory_human'),
                'connected_clients': info.get('connected_clients'),
                'total_commands_processed': info.get('total_commands_processed'),
                'keyspace_hits': info.get('keyspace_hits'),
                'keyspace_misses': info.get('keyspace_misses'),
                'hit_rate': (
                    info.get('keyspace_hits', 0) / 
                    max(info.get('keyspace_hits', 0) + info.get('keyspace_misses', 0), 1)
                ) * 100
            }
            
        except Exception as e:
            logger.error(f"Cache info error: {e}")
            return {}


# Global Redis client instance
cache_client = RedisClient()
