"""
SmartShelf AI - Cache Service
Redis-based caching with TTL and error handling
"""

import redis
import pickle
import json
import logging
from typing import Any, Optional, Union, List
from core.config import settings, REDIS_CONFIG

logger = logging.getLogger(__name__)

class CacheService:
    """Redis-based caching service with comprehensive error handling"""
    
    def __init__(self):
        self.redis_client = None
        self._connect()
    
    def _connect(self):
        """Establish Redis connection with retry logic"""
        try:
            self.redis_client = redis.Redis(**REDIS_CONFIG)
            # Test connection
            self.redis_client.ping()
            logger.info("Redis connection established successfully")
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
            self.redis_client = None
    
    async def get(self, key: str) -> Optional[Any]:
        """Get cached value with error handling"""
        if not self.redis_client:
            logger.warning("Redis not available, cache get skipped")
            return None
        
        try:
            data = self.redis_client.get(key)
            if data:
                return pickle.loads(data)
            return None
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """Set cached value with TTL"""
        if not self.redis_client:
            logger.warning("Redis not available, cache set skipped")
            return False
        
        try:
            ttl = ttl or settings.cache_ttl
            serialized = pickle.dumps(value)
            return self.redis_client.setex(key, ttl, serialized)
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete cached value"""
        if not self.redis_client:
            return False
        
        try:
            return bool(self.redis_client.delete(key))
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False
    
    async def delete_pattern(self, pattern: str) -> int:
        """Delete keys matching pattern"""
        if not self.redis_client:
            return 0
        
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                return self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Cache delete pattern error for {pattern}: {e}")
            return 0
    
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        if not self.redis_client:
            return False
        
        try:
            return bool(self.redis_client.exists(key))
        except Exception as e:
            logger.error(f"Cache exists error for key {key}: {e}")
            return False
    
    async def get_ttl(self, key: str) -> int:
        """Get time-to-live for key"""
        if not self.redis_client:
            return -1
        
        try:
            return self.redis_client.ttl(key)
        except Exception as e:
            logger.error(f"Cache TTL error for key {key}: {e}")
            return -1
    
    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment counter"""
        if not self.redis_client:
            return None
        
        try:
            return self.redis_client.incr(key, amount)
        except Exception as e:
            logger.error(f"Cache increment error for key {key}: {e}")
            return None
    
    async def get_multiple(self, keys: List[str]) -> dict:
        """Get multiple cached values"""
        if not self.redis_client:
            return {}
        
        try:
            values = self.redis_client.mget(keys)
            result = {}
            for i, key in enumerate(keys):
                if values[i]:
                    result[key] = pickle.loads(values[i])
            return result
        except Exception as e:
            logger.error(f"Cache get multiple error: {e}")
            return {}
    
    async def set_multiple(self, mapping: dict, ttl: int = None) -> bool:
        """Set multiple cached values"""
        if not self.redis_client:
            return False
        
        try:
            ttl = ttl or settings.cache_ttl
            pipe = self.redis_client.pipeline()
            
            for key, value in mapping.items():
                serialized = pickle.dumps(value)
                pipe.setex(key, ttl, serialized)
            
            pipe.execute()
            return True
        except Exception as e:
            logger.error(f"Cache set multiple error: {e}")
            return False
    
    def health_check(self) -> dict:
        """Check Redis health"""
        if not self.redis_client:
            return {"status": "unhealthy", "error": "No connection"}
        
        try:
            info = self.redis_client.info()
            return {
                "status": "healthy",
                "connected_clients": info.get("connected_clients", 0),
                "used_memory": info.get("used_memory_human", "unknown"),
                "uptime_seconds": info.get("uptime_in_seconds", 0)
            }
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    
    def close(self):
        """Close Redis connection"""
        if self.redis_client:
            self.redis_client.close()

# Global cache service instance
cache_service = CacheService()
