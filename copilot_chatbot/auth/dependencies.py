"""
FastAPI dependencies for authentication
"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from ..database.connection import get_db
from ..database.models import User
from ..database.crud import UserCRUD
from .jwt_handler import jwt_handler

# HTTP Bearer token scheme
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Get the current authenticated user from JWT token
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Get user ID from token
        user_id = jwt_handler.get_user_id_from_token(credentials.credentials)
    except HTTPException:
        raise credentials_exception
    
    # Get user from database
    user_crud = UserCRUD(db)
    user = user_crud.get_user(user_id)
    
    if user is None:
        raise credentials_exception
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get the current active user (user must be active)
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


async def get_current_verified_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Get the current verified user (user must be email verified)
    """
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email not verified"
        )
    return current_user


async def get_current_admin_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Get the current admin user (user must have admin role)
    """
    from ..database.models import UserRole
    
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user


def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Get the current user if token is provided, otherwise return None
    """
    if not credentials:
        return None
    
    try:
        user_id = jwt_handler.get_user_id_from_token(credentials.credentials)
        user_crud = UserCRUD(db)
        return user_crud.get_user(user_id)
    except HTTPException:
        return None
