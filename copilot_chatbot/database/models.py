"""
Database models for SmartShelf AI
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, JSON, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from .connection import Base


class UserRole(enum.Enum):
    USER = "user"
    ADMIN = "admin"
    MODERATOR = "moderator"


class MessageRole(enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class AnalyticsEventType(enum.Enum):
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    MESSAGE_SENT = "message_sent"
    PRODUCT_CLICKED = "product_clicked"
    SEARCH_PERFORMED = "search_performed"
    SESSION_STARTED = "session_started"
    SESSION_ENDED = "session_ended"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.USER)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    avatar_url = Column(String, nullable=True)
    bio = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    chat_sessions = relationship("ChatSession", back_populates="user", cascade="all, delete-orphan")
    preferences = relationship("UserPreference", back_populates="user", cascade="all, delete-orphan")
    analytics_events = relationship("AnalyticsEvent", back_populates="user", cascade="all, delete-orphan")


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    ended_at = Column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    message_count = Column(Integer, default=0)
    session_metadata = Column(JSON, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="chat_sessions")
    messages = relationship("Message", back_populates="session", cascade="all, delete-orphan")


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=False)
    role = Column(Enum(MessageRole), nullable=False)
    content = Column(Text, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Metadata
    token_count = Column(Integer, nullable=True)
    processing_time = Column(Float, nullable=True)
    model_used = Column(String, nullable=True)
    message_metadata = Column(JSON, nullable=True)
    
    # Product suggestions
    product_suggestions = Column(JSON, nullable=True)
    
    # Relationships
    session = relationship("ChatSession", back_populates="messages")


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Float, nullable=True)
    currency = Column(String, default="USD")
    
    # Source information
    source = Column(String, nullable=False)  # amazon, ebay, walmart, etc.
    source_id = Column(String, nullable=True)  # External product ID
    url = Column(String, nullable=True)
    image_url = Column(String, nullable=True)
    
    # Product details
    category = Column(String, nullable=True)
    brand = Column(String, nullable=True)
    rating = Column(Float, nullable=True)
    review_count = Column(Integer, nullable=True)
    availability = Column(String, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_scraped = Column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    product_metadata = Column(JSON, nullable=True)
    
    # Search and analytics
    view_count = Column(Integer, default=0)
    click_count = Column(Integer, default=0)
    conversion_count = Column(Integer, default=0)


class AnalyticsEvent(Base):
    __tablename__ = "analytics_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    event_type = Column(Enum(AnalyticsEventType), nullable=False)
    
    # Event data
    event_data = Column(JSON, nullable=True)
    session_id = Column(String, nullable=True)
    
    # Request information
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="analytics_events")


class UserPreference(Base):
    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    key = Column(String, nullable=False)
    value = Column(JSON, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="preferences")


class ScrapingJob(Base):
    __tablename__ = "scraping_jobs"

    id = Column(Integer, primary_key=True, index=True)
    source = Column(String, nullable=False)  # amazon, ebay, walmart, etc.
    job_type = Column(String, nullable=False)  # search, category, product
    
    # Job configuration
    config = Column(JSON, nullable=False)
    status = Column(String, default="pending")  # pending, running, completed, failed
    
    # Results
    products_found = Column(Integer, default=0)
    errors = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    job_metadata = Column(JSON, nullable=True)
