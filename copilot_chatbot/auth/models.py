"""
Pydantic models for authentication
"""

from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, validator
from datetime import datetime


class UserBase(BaseModel):
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=100)
    bio: Optional[str] = Field(None, max_length=500)


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=128)
    
    @validator('password')
    def validate_password(cls, v):
        from .password_utils import PasswordUtils
        
        result = PasswordUtils.validate_password_strength(v)
        if not result['is_valid']:
            raise ValueError('; '.join(result['errors']))
        
        # Check if password is commonly breached
        if PasswordUtils.check_password_breached(v):
            raise ValueError('This password has been found in data breaches. Please choose a different password.')
        
        return v


class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    bio: Optional[str] = Field(None, max_length=500)
    avatar_url: Optional[str] = None


class UserResponse(UserBase):
    id: int
    role: str
    is_active: bool
    is_verified: bool
    avatar_url: Optional[str] = None
    created_at: datetime
    last_login: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class TokenData(BaseModel):
    user_id: Optional[int] = None
    email: Optional[str] = None


class TokenRefresh(BaseModel):
    refresh_token: str


class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)
    
    @validator('new_password')
    def validate_new_password(cls, v):
        from .password_utils import PasswordUtils
        
        result = PasswordUtils.validate_password_strength(v)
        if not result['is_valid']:
            raise ValueError('; '.join(result['errors']))
        
        return v


class PasswordReset(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8, max_length=128)
    
    @validator('new_password')
    def validate_new_password(cls, v):
        from .password_utils import PasswordUtils
        
        result = PasswordUtils.validate_password_strength(v)
        if not result['is_valid']:
            raise ValueError('; '.join(result['errors']))
        
        return v


class EmailVerification(BaseModel):
    token: str


class UserPreferences(BaseModel):
    notifications: bool = True
    email_updates: bool = False
    dark_mode: bool = False
    language: str = "en"
    auto_save: bool = True
    timezone: str = "UTC"


class SessionCreate(BaseModel):
    title: Optional[str] = None


class SessionResponse(BaseModel):
    id: int
    title: str
    is_active: bool
    message_count: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class MessageCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=10000)
    include_products: bool = False


class MessageResponse(BaseModel):
    id: int
    role: str
    content: str
    created_at: datetime
    product_suggestions: Optional[List[dict]] = None
    processing_time: Optional[float] = None
    
    class Config:
        from_attributes = True


class AnalyticsEventCreate(BaseModel):
    event_type: str
    event_data: Optional[dict] = None
    session_id: Optional[str] = None


class ProductResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    price: Optional[float] = None
    currency: str = "USD"
    source: str
    url: Optional[str] = None
    image_url: Optional[str] = None
    category: Optional[str] = None
    brand: Optional[str] = None
    rating: Optional[float] = None
    review_count: Optional[int] = None
    availability: Optional[str] = None
    
    class Config:
        from_attributes = True
