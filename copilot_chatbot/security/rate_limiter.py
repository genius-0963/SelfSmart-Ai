"""
Rate limiting implementation for API protection
"""

import asyncio
import time
from typing import Dict, Optional, Callable, Any
from functools import wraps
from datetime import datetime, timedelta
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
import hashlib

from ..cache.redis_client import cache_client
from ..monitoring.logger import get_logger
from ..monitoring.metrics import metrics
from ..monitoring.error_tracker import track_error, ErrorSeverity, ErrorCategory

logger = get_logger(__name__)


class RateLimitExceeded(HTTPException):
    """Exception raised when rate limit is exceeded"""
    def __init__(self, limit: int, window: int, retry_after: int):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "rate_limit_exceeded",
                "message": f"Rate limit exceeded. Maximum {limit} requests per {window} seconds.",
                "retry_after": retry_after
            }
        )
        self.headers = {"Retry-After": str(retry_after)}


class RateLimiter:
    """Advanced rate limiter with multiple strategies"""
    
    def __init__(self):
        self.limits = {}
        self.default_limits = {
            'global': {'limit': 1000, 'window': 3600},  # 1000 requests per hour globally
            'user': {'limit': 100, 'window': 3600},      # 100 requests per hour per user
            'ip': {'limit': 200, 'window': 3600},       # 200 requests per hour per IP
            'endpoint': {'limit': 50, 'window': 3600},   # 50 requests per hour per endpoint
            'auth': {'limit': 10, 'window': 900},        # 10 auth requests per 15 minutes
            'search': {'limit': 30, 'window': 3600},      # 30 search requests per hour
            'chat': {'limit': 60, 'window': 3600},       # 60 chat messages per hour
        }
        
        # Initialize default limits
        self.limits.update(self.default_limits)
    
    def set_limit(self, key: str, limit: int, window: int):
        """Set rate limit for a specific key"""
        self.limits[key] = {'limit': limit, 'window': window}
    
    def get_limit(self, key: str) -> Dict[str, int]:
        """Get rate limit for a specific key"""
        return self.limits.get(key, self.limits['global'])
    
    async def is_allowed(
        self, 
        key: str, 
        identifier: str,
        limit: Optional[int] = None,
        window: Optional[int] = None
    ) -> tuple[bool, int]:
        """
        Check if request is allowed
        
        Args:
            key: Rate limit key type
            identifier: Unique identifier (user_id, ip_address, etc.)
            limit: Override limit
            window: Override window
        
        Returns:
            Tuple of (is_allowed, current_count)
        """
        try:
            # Get limit configuration
            limit_config = self.get_limit(key)
            request_limit = limit or limit_config['limit']
            request_window = window or limit_config['window']
            
            # Create Redis key
            redis_key = f"rate_limit:{key}:{identifier}"
            
            # Increment counter
            current_count = await cache_client.increment_rate_limit(
                redis_key, 
                request_limit, 
                request_window
            )
            
            is_allowed = current_count <= request_limit
            
            # Update metrics
            if is_allowed:
                metrics.increment_cache_hits("rate_limit_allow")
            else:
                metrics.increment_cache_hits("rate_limit_block")
                logger.warning(f"Rate limit exceeded: {key}:{identifier} ({current_count}/{request_limit})")
            
            return is_allowed, current_count
            
        except Exception as e:
            logger.error(f"Rate limit check error: {e}")
            track_error(e, ErrorSeverity.MEDIUM, ErrorCategory.SYSTEM, "rate_limiter")
            # Fail open - allow request if rate limiter fails
            return True, 0
    
    async def get_remaining_requests(
        self, 
        key: str, 
        identifier: str
    ) -> Dict[str, Any]:
        """
        Get remaining requests and reset time
        
        Args:
            key: Rate limit key type
            identifier: Unique identifier
        
        Returns:
            Dict with remaining requests and reset time
        """
        try:
            limit_config = self.get_limit(key)
            redis_key = f"rate_limit:{key}:{identifier}"
            
            # Get current count
            current_count = await cache_client.increment_rate_limit(
                redis_key,
                limit_config['limit'] + 1,  # Don't actually limit
                limit_config['window']
            ) - 1  # Subtract the increment we just did
            
            # Get TTL
            ttl = await cache_client.ttl(redis_key)
            reset_time = int(time.time()) + max(ttl, 0)
            
            remaining = max(0, limit_config['limit'] - current_count)
            
            return {
                'remaining': remaining,
                'limit': limit_config['limit'],
                'reset_time': reset_time,
                'retry_after': max(ttl, 0)
            }
            
        except Exception as e:
            logger.error(f"Get remaining requests error: {e}")
            return {
                'remaining': 0,
                'limit': 0,
                'reset_time': 0,
                'retry_after': 0
            }


class RateLimitMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for rate limiting"""
    
    def __init__(self, app, rate_limiter: RateLimiter = None):
        super().__init__(app)
        self.rate_limiter = rate_limiter or RateLimiter()
    
    async def dispatch(self, request: Request, call_next):
        """Process request with rate limiting"""
        try:
            # Get client IP
            client_ip = self._get_client_ip(request)
            
            # Get user ID if authenticated
            user_id = getattr(request.state, 'user_id', None)
            
            # Determine rate limit key
            path = request.url.path
            method = request.method
            
            # Different limits for different endpoints
            if '/auth/' in path:
                limit_key = 'auth'
            elif '/search' in path:
                limit_key = 'search'
            elif '/chat' in path:
                limit_key = 'chat'
            else:
                limit_key = 'endpoint'
            
            # Check IP-based rate limit
            ip_allowed, ip_count = await self.rate_limiter.is_allowed(
                'ip', client_ip
            )
            
            if not ip_allowed:
                retry_after = await self.rate_limiter.get_remaining_requests('ip', client_ip)
                raise RateLimitExceeded(
                    self.rate_limiter.limits['ip']['limit'],
                    self.rate_limiter.limits['ip']['window'],
                    retry_after['retry_after']
                )
            
            # Check user-based rate limit if authenticated
            if user_id:
                user_allowed, user_count = await self.rate_limiter.is_allowed(
                    'user', str(user_id)
                )
                
                if not user_allowed:
                    retry_after = await self.rate_limiter.get_remaining_requests('user', str(user_id))
                    raise RateLimitExceeded(
                        self.rate_limiter.limits['user']['limit'],
                        self.rate_limiter.limits['user']['window'],
                        retry_after['retry_after']
                    )
            
            # Check endpoint-based rate limit
            endpoint_identifier = f"{client_ip}:{path}"
            endpoint_allowed, endpoint_count = await self.rate_limiter.is_allowed(
                limit_key, endpoint_identifier
            )
            
            if not endpoint_allowed:
                retry_after = await self.rate_limiter.get_remaining_requests(
                    limit_key, endpoint_identifier
                )
                raise RateLimitExceeded(
                    self.rate_limiter.limits[limit_key]['limit'],
                    self.rate_limiter.limits[limit_key]['window'],
                    retry_after['retry_after']
                )
            
            # Add rate limit headers
            response = await call_next(request)
            
            # Add rate limit info to response headers
            if user_id:
                user_remaining = await self.rate_limiter.get_remaining_requests('user', str(user_id))
                response.headers['X-RateLimit-User-Remaining'] = str(user_remaining['remaining'])
                response.headers['X-RateLimit-User-Limit'] = str(user_remaining['limit'])
                response.headers['X-RateLimit-User-Reset'] = str(user_remaining['reset_time'])
            
            ip_remaining = await self.rate_limiter.get_remaining_requests('ip', client_ip)
            response.headers['X-RateLimit-IP-Remaining'] = str(ip_remaining['remaining'])
            response.headers['X-RateLimit-IP-Limit'] = str(ip_remaining['limit'])
            response.headers['X-RateLimit-IP-Reset'] = str(ip_remaining['reset_time'])
            
            endpoint_remaining = await self.rate_limiter.get_remaining_requests(
                limit_key, endpoint_identifier
            )
            response.headers['X-RateLimit-Endpoint-Remaining'] = str(endpoint_remaining['remaining'])
            response.headers['X-RateLimit-Endpoint-Limit'] = str(endpoint_remaining['limit'])
            response.headers['X-RateLimit-Endpoint-Reset'] = str(endpoint_remaining['reset_time'])
            
            return response
            
        except RateLimitExceeded:
            raise
        except Exception as e:
            logger.error(f"Rate limit middleware error: {e}")
            track_error(e, ErrorSeverity.MEDIUM, ErrorCategory.SYSTEM, "rate_limit_middleware")
            # Fail open - allow request if middleware fails
            return await call_next(request)
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address from request"""
        # Check for forwarded IP
        forwarded_for = request.headers.get('X-Forwarded-For')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()
        
        real_ip = request.headers.get('X-Real-IP')
        if real_ip:
            return real_ip
        
        # Fall back to client IP
        return request.client.host if request.client else 'unknown'


# Decorator for rate limiting specific functions
def rate_limit(
    key: str = 'endpoint',
    limit: Optional[int] = None,
    window: Optional[int] = None,
    identifier_func: Optional[Callable] = None
):
    """
    Decorator for rate limiting specific functions
    
    Args:
        key: Rate limit key type
        limit: Override limit
        window: Override window
        identifier_func: Function to get identifier from request/args
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                # Get identifier
                if identifier_func:
                    identifier = identifier_func(*args, **kwargs)
                else:
                    # Try to get from request state
                    request = None
                    for arg in args:
                        if hasattr(arg, 'state'):
                            request = arg
                            break
                    
                    if request and hasattr(request.state, 'user_id'):
                        identifier = str(request.state.user_id)
                    elif request:
                        identifier = request.client.host if request.client else 'unknown'
                    else:
                        identifier = 'function_call'
                
                # Check rate limit
                limiter = RateLimiter()
                allowed, count = await limiter.is_allowed(key, identifier, limit, window)
                
                if not allowed:
                    limit_config = limiter.get_limit(key)
                    retry_after = await limiter.get_remaining_requests(key, identifier)
                    raise RateLimitExceeded(
                        limit or limit_config['limit'],
                        window or limit_config['window'],
                        retry_after['retry_after']
                    )
                
                return await func(*args, **kwargs)
                
            except RateLimitExceeded:
                raise
            except Exception as e:
                logger.error(f"Rate limit decorator error: {e}")
                # Fail open
                return await func(*args, **kwargs)
        
        return wrapper
    return decorator


# Global rate limiter instance
rate_limiter = RateLimiter()
