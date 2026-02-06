"""
SmartShelf AI - Security Module

Authentication and authorization utilities.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional

security = HTTPBearer()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current user from JWT token."""
    # Mock implementation - in production, decode JWT token
    if credentials.credentials != "demo_token":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return {"user_id": "demo_user", "permissions": ["read", "write"]}


async def verify_api_key(api_key: str):
    """Verify API key for external access."""
    # Mock implementation
    valid_keys = ["demo_api_key"]
    if api_key not in valid_keys:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    return True
