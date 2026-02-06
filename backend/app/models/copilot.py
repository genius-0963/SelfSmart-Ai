"""
AI Copilot-related Pydantic models for API validation.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime


class MessageType(str, Enum):
    """Message type enumeration."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatMessageBase(BaseModel):
    """Base chat message model."""
    message_type: MessageType = Field(..., description="Type of message")
    message_content: str = Field(..., min_length=1, max_length=10000, description="Message content")


class ChatMessageCreate(ChatMessageBase):
    """Model for creating a chat message."""
    session_id: str = Field(..., description="Chat session ID")
    message_data: Optional[Dict[str, Any]] = Field(None, description="Structured message data")
    context_used: Optional[List[str]] = Field(None, description="Context documents used")


class ChatMessageResponse(ChatMessageBase):
    """Model for chat message response."""
    id: int
    session_id: str
    message_data: Optional[Dict[str, Any]]
    context_used: Optional[List[str]]
    model_used: Optional[str]
    tokens_used: Optional[int]
    response_time_ms: Optional[int]
    user_feedback: Optional[int] = Field(None, ge=1, le=5)
    created_date: datetime
    
    class Config:
        from_attributes = True


class ChatSessionBase(BaseModel):
    """Base chat session model."""
    user_id: Optional[str] = Field(None, description="User identifier")
    session_metadata: Optional[Dict[str, Any]] = Field(None, description="Session metadata")


class ChatSessionCreate(ChatSessionBase):
    """Model for creating a chat session."""
    pass


class ChatSessionResponse(ChatSessionBase):
    """Model for chat session response."""
    id: int
    session_id: str
    created_date: datetime
    last_activity: datetime
    is_active: bool
    
    # Session statistics
    message_count: int
    average_response_time_ms: Optional[float]
    user_satisfaction_score: Optional[float]
    
    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    """Model for chat request."""
    session_id: Optional[str] = Field(None, description="Existing session ID (creates new if not provided)")
    message: str = Field(..., min_length=1, max_length=10000, description="User message")
    context_filter: Optional[Dict[str, Any]] = Field(None, description="Context filtering criteria")
    include_visualizations: bool = Field(True, description="Include charts and visualizations")
    response_format: str = Field("text", description="Response format: 'text', 'json', 'structured'")
    
    @validator('response_format')
    def validate_response_format(cls, v):
        allowed_formats = ['text', 'json', 'structured']
        if v not in allowed_formats:
            raise ValueError(f'Response format must be one of: {allowed_formats}')
        return v


class ChatResponse(BaseModel):
    """Model for chat response."""
    session_id: str
    message_id: int
    
    # Response content
    response: str
    message_data: Optional[Dict[str, Any]] = None
    
    # Context information
    context_used: List[Dict[str, Any]] = Field(default_factory=list)
    sources_cited: List[str] = Field(default_factory=list)
    
    # Metadata
    model_used: str
    tokens_used: int
    response_time_ms: int
    confidence_score: Optional[float] = Field(None, ge=0, le=1)
    
    # Follow-up suggestions
    suggested_questions: List[str] = Field(default_factory=list)
    related_topics: List[str] = Field(default_factory=list)


class ContextDocument(BaseModel):
    """Model for context document used in RAG."""
    document_id: str
    content: str
    source: str
    source_type: str  # 'product', 'sales', 'inventory', 'forecast', 'general'
    relevance_score: float
    metadata: Dict[str, Any]
    retrieved_at: datetime


class ContextSearchRequest(BaseModel):
    """Model for context search request."""
    query: str = Field(..., min_length=1, description="Search query")
    max_results: int = Field(10, ge=1, le=50, description="Maximum results to return")
    source_types: Optional[List[str]] = Field(None, description="Filter by source types")
    date_range: Optional[Dict[str, datetime]] = Field(None, description="Filter by date range")
    min_relevance_score: float = Field(0.5, ge=0, le=1, description="Minimum relevance score")


class ContextSearchResponse(BaseModel):
    """Model for context search response."""
    query: str
    results: List[ContextDocument]
    total_found: int
    search_time_ms: int
    search_metadata: Dict[str, Any]


class CopilotAnalytics(BaseModel):
    """Model for AI Copilot analytics."""
    period_start: datetime
    period_end: datetime
    
    # Usage metrics
    total_sessions: int
    total_messages: int
    unique_users: int
    average_session_length_minutes: float
    
    # Performance metrics
    average_response_time_ms: float
    average_tokens_per_response: float
    user_satisfaction_score: float
    
    # Content metrics
    most_asked_topics: List[Dict[str, Any]]
    context_hit_rate: float
    visualization_usage_rate: float
    
    # Cost metrics
    total_tokens_consumed: int
    estimated_cost_usd: float
    
    generated_at: datetime


class CopilotFeedback(BaseModel):
    """Model for user feedback on copilot responses."""
    message_id: int
    session_id: str
    rating: int = Field(..., ge=1, le=5, description="User rating (1-5)")
    feedback_category: str = Field(..., description="Category of feedback")
    feedback_text: Optional[str] = Field(None, max_length=1000, description="Detailed feedback")
    was_helpful: bool
    follow_up_actions: List[str] = Field(default_factory=list)
    
    @validator('feedback_category')
    def validate_feedback_category(cls, v):
        allowed_categories = [
            'accuracy', 'relevance', 'completeness', 'clarity', 
            'timeliness', 'formatting', 'other'
        ]
        if v not in allowed_categories:
            raise ValueError(f'Feedback category must be one of: {allowed_categories}')
        return v


class CopilotKnowledgeBase(BaseModel):
    """Model for knowledge base document."""
    document_id: str
    title: str
    content: str
    source_type: str
    category: str
    tags: List[str]
    last_updated: datetime
    
    # Metadata
    author: Optional[str]
    version: str
    language: str = "en"
    confidence_score: float
    
    # Usage statistics
    access_count: int
    helpful_votes: int
    not_helpful_votes: int
    
    class Config:
        from_attributes = True


class CopilotTrainingData(BaseModel):
    """Model for copilot training data."""
    conversation_id: str
    messages: List[Dict[str, Any]]
    context_documents: List[str]
    outcome_rating: Optional[int] = Field(None, ge=1, le=5)
    improvement_notes: Optional[str]
    created_at: datetime


class CopilotModelConfig(BaseModel):
    """Model for copilot model configuration."""
    model_name: str
    model_version: str
    provider: str  # 'openai', 'anthropic', 'local'
    
    # Model parameters
    temperature: float = Field(0.7, ge=0, le=2)
    max_tokens: int = Field(1000, ge=100, le=4000)
    top_p: float = Field(1.0, ge=0, le=1)
    frequency_penalty: float = Field(0, ge=-2, le=2)
    presence_penalty: float = Field(0, ge=-2, le=2)
    
    # RAG parameters
    max_context_documents: int = Field(5, ge=1, le=20)
    context_similarity_threshold: float = Field(0.7, ge=0, le=1)
    include_system_context: bool = True
    
    # Response formatting
    response_style: str = Field("professional", description="Response style")
    include_confidence: bool = True
    include_sources: bool = True
    
    # Safety parameters
    content_filter_enabled: bool = True
    max_response_length: int = Field(2000, ge=100, le=8000)
    
    updated_at: datetime
    is_active: bool = True


class CopilotError(BaseModel):
    """Model for copilot error reporting."""
    error_id: str
    session_id: str
    error_type: str  # 'api_error', 'context_retrieval', 'model_error', 'validation'
    error_message: str
    user_query: Optional[str]
    stack_trace: Optional[str]
    context_at_error: Optional[Dict[str, Any]]
    
    # Impact assessment
    user_impacted: bool
    recovery_suggested: bool
    follow_up_required: bool
    
    occurred_at: datetime
    resolved_at: Optional[datetime]
    resolution_notes: Optional[str]


class CopilotInsight(BaseModel):
    """Model for AI-generated business insights."""
    insight_id: str
    insight_type: str  # 'trend', 'anomaly', 'opportunity', 'risk'
    title: str
    description: str
    
    # Data backing the insight
    supporting_data: Dict[str, Any]
    confidence_score: float
    time_period: Dict[str, datetime]
    
    # Business impact
    impact_level: str  # 'low', 'medium', 'high', 'critical'
    potential_value: Optional[float] = None
    
    # Recommendations
    recommended_actions: List[str]
    implementation_complexity: str  # 'easy', 'moderate', 'complex'
    
    # Visualization
    chart_config: Optional[Dict[str, Any]] = None
    
    generated_at: datetime
    expires_at: Optional[datetime] = None


# Import Enum for MessageType
from enum import Enum
