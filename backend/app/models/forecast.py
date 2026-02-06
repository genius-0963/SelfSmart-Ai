"""
Forecast-related Pydantic models for API validation.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from enum import Enum


class ForecastType(str, Enum):
    """Forecast type enumeration."""
    DEMAND = "demand"
    REVENUE = "revenue"
    PRICE = "price"
    INVENTORY = "inventory"


class ForecastBase(BaseModel):
    """Base forecast model with common fields."""
    product_id: int = Field(..., description="Product ID")
    sku: str = Field(..., description="Product SKU")
    forecast_type: ForecastType = Field(..., description="Type of forecast")
    target_date: datetime = Field(..., description="Date being forecasted")
    predicted_value: float = Field(..., description="Predicted value")
    confidence_lower: Optional[float] = Field(None, description="Lower confidence bound")
    confidence_upper: Optional[float] = Field(None, description="Upper confidence bound")
    confidence_level: float = Field(0.95, ge=0.8, le=0.99, description="Confidence level")


class ForecastCreate(ForecastBase):
    """Model for creating a new forecast."""
    model_version: str = Field(..., description="ML model version")
    model_accuracy: Optional[float] = Field(None, ge=0, le=1, description="Model accuracy")
    features_used: Optional[str] = Field(None, description="JSON string of features used")


class ForecastResponse(ForecastBase):
    """Model for forecast response with additional fields."""
    id: int
    forecast_date: datetime
    model_version: str
    model_accuracy: Optional[float]
    features_used: Optional[str]
    created_date: datetime
    
    # Computed fields
    prediction_interval_width: Optional[float] = Field(None, description="Width of confidence interval")
    relative_uncertainty: Optional[float] = Field(None, description="Relative uncertainty as percentage")
    
    class Config:
        from_attributes = True


class ForecastRequest(BaseModel):
    """Model for forecast generation request."""
    product_ids: Optional[List[int]] = Field(None, description="Specific product IDs")
    category: Optional[str] = Field(None, description="Forecast by category")
    forecast_type: ForecastType = Field(ForecastType.DEMAND, description="Type of forecast")
    start_date: date = Field(..., description="Forecast start date")
    end_date: date = Field(..., description="Forecast end date")
    confidence_level: float = Field(0.95, ge=0.8, le=0.99, description="Confidence interval level")
    include_seasonality: bool = Field(True, description="Include seasonal patterns")
    include_promotions: bool = Field(True, description="Include promotion effects")
    model_version: Optional[str] = Field(None, description="Specific model version to use")
    
    @validator('end_date')
    def validate_date_range(cls, v, values):
        if 'start_date' in values:
            if v <= values['start_date']:
                raise ValueError('End date must be after start date')
            if (v - values['start_date']).days > 365:
                raise ValueError('Forecast period cannot exceed 365 days')
        return v


class ForecastMetrics(BaseModel):
    """Model for forecast accuracy metrics."""
    model_version: str
    forecast_type: ForecastType
    evaluation_period: Dict[str, date]
    
    # Accuracy metrics
    mean_absolute_error: float
    mean_absolute_percentage_error: float
    root_mean_squared_error: float
    r_squared: float
    
    # Business metrics
    forecast_coverage: float  # Percentage of actuals within confidence interval
    bias_percentage: float  # Systematic over/under forecasting
    
    # Comparison metrics
    baseline_mape: Optional[float] = None  # Simple baseline model MAPE
    improvement_over_baseline: Optional[float] = None
    
    evaluated_at: datetime


class ForecastComparison(BaseModel):
    """Model for comparing different forecast models."""
    product_id: int
    product_name: str
    comparison_period: Dict[str, date]
    
    # Model comparisons
    models: List[Dict[str, Any]] = Field(..., description="Different model performances")
    
    # Best model recommendation
    recommended_model: str
    recommendation_reason: str
    
    # Visual comparison data
    actual_vs_predicted: List[Dict[str, Any]] = Field(default_factory=list)


class ForecastBatchRequest(BaseModel):
    """Model for batch forecast generation."""
    forecast_requests: List[ForecastRequest] = Field(..., min_items=1, max_items=100)
    priority: str = Field("normal", description="Processing priority: 'low', 'normal', 'high'")
    notify_on_completion: bool = Field(False, description="Send notification when complete")
    
    @validator('priority')
    def validate_priority(cls, v):
        allowed_priorities = ['low', 'normal', 'high']
        if v not in allowed_priorities:
            raise ValueError(f'Priority must be one of: {allowed_priorities}')
        return v


class ForecastBatchResponse(BaseModel):
    """Model for batch forecast response."""
    batch_id: str
    status: str  # 'pending', 'processing', 'completed', 'failed'
    total_requests: int
    completed_requests: int
    failed_requests: int
    started_at: datetime
    estimated_completion: Optional[datetime] = None
    results: Optional[List[ForecastResponse]] = None
    errors: List[str] = Field(default_factory=list)


class ForecastExplanation(BaseModel):
    """Model for ML model explanation (XAI)."""
    forecast_id: int
    product_id: int
    target_date: datetime
    
    # Feature importance
    feature_importance: List[Dict[str, Any]] = Field(..., description="Feature importance scores")
    
    # Explanation components
    seasonal_contribution: float
    trend_contribution: float
    promotion_contribution: float
    external_factors_contribution: float
    
    # Similar historical patterns
    similar_periods: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Confidence explanation
    confidence_factors: List[str] = Field(default_factory=list)
    uncertainty_sources: List[str] = Field(default_factory=list)
    
    # Natural language explanation
    explanation_text: str
    
    generated_at: datetime


class ForecastAlert(BaseModel):
    """Model for forecast-related alerts."""
    alert_id: str
    product_id: int
    product_name: str
    alert_type: str  # 'accuracy_drop', 'anomaly_detected', 'confidence_low'
    severity: str  # 'low', 'medium', 'high', 'critical'
    
    # Alert details
    description: str
    forecast_value: float
    expected_range: Optional[Dict[str, float]] = None
    actual_value: Optional[float] = None
    
    # Impact assessment
    business_impact: str
    recommended_action: str
    
    # Metadata
    detected_at: datetime
    acknowledged: bool = False
    resolved: bool = False


class ForecastModelInfo(BaseModel):
    """Model information and capabilities."""
    model_name: str
    model_version: str
    model_type: str  # 'prophet', 'lstm', 'arima', 'ensemble'
    
    # Capabilities
    supported_forecast_types: List[ForecastType]
    max_forecast_horizon_days: int
    supports_seasonality: bool
    supports_promotions: bool
    supports_exogenous_variables: bool
    
    # Performance characteristics
    typical_accuracy_range: Dict[str, float]
    training_time_minutes: int
    inference_time_ms: int
    
    # Data requirements
    min_historical_days: int
    preferred_historical_days: int
    required_features: List[str]
    
    # Version info
    created_at: datetime
    last_trained: Optional[datetime] = None
    is_active: bool = True


class ForecastScenario(BaseModel):
    """What-if scenario analysis."""
    scenario_id: str
    scenario_name: str
    description: str
    
    # Base forecast
    base_forecast: List[Dict[str, Any]]
    
    # Scenario parameters
    price_change: Optional[float] = None  # Percentage price change
    promotion_intensity: Optional[float] = None  # Promotion intensity (0-1)
    external_factor: Optional[Dict[str, Any]] = None
    
    # Scenario results
    scenario_forecast: List[Dict[str, Any]]
    impact_analysis: Dict[str, Any]
    
    # Recommendations
    recommendations: List[str]
    
    created_at: datetime
