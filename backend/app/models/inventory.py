"""
Inventory-related Pydantic models for API validation.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from enum import Enum


class TransactionType(str, Enum):
    """Inventory transaction type enumeration."""
    SALE = "sale"
    RESTOCK = "restock"
    ADJUSTMENT = "adjustment"
    STOCKOUT = "stockout"
    DAILY_SNAPSHOT = "daily_snapshot"


class AlertType(str, Enum):
    """Inventory alert type enumeration."""
    STOCKOUT_RISK = "stockout_risk"
    OVERSTOCK = "overstock"
    REORDER = "reorder"
    SLOW_MOVING = "slow_moving"
    EXPIRY_RISK = "expiry_risk"


class Severity(str, Enum):
    """Alert severity enumeration."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class InventoryRecordBase(BaseModel):
    """Base inventory record model."""
    product_id: int = Field(..., description="Product ID")
    sku: str = Field(..., description="Product SKU")
    date: datetime = Field(..., description="Transaction date")
    transaction_type: TransactionType = Field(..., description="Type of transaction")
    quantity_change: int = Field(..., description="Change in quantity (negative for sales)")
    stock_level_after: int = Field(..., ge=0, description="Stock level after transaction")


class InventoryRecordCreate(InventoryRecordBase):
    """Model for creating inventory record."""
    optimal_stock_level: Optional[int] = Field(None, ge=0)
    days_of_supply: Optional[float] = Field(None, ge=0)
    inventory_value: Optional[float] = Field(None, ge=0)
    supplier: Optional[str] = Field(None, max_length=100)
    cost_per_unit: Optional[float] = Field(None, ge=0)
    lost_sales: Optional[int] = Field(None, ge=0)
    stockout_reason: Optional[str] = Field(None, max_length=100)


class InventoryRecordResponse(InventoryRecordBase):
    """Model for inventory record response."""
    id: int
    optimal_stock_level: Optional[int]
    days_of_supply: Optional[float]
    inventory_value: Optional[float]
    supplier: Optional[str]
    cost_per_unit: Optional[float]
    lost_sales: Optional[int]
    stockout_reason: Optional[str]
    created_date: datetime
    
    class Config:
        from_attributes = True


class InventoryAlertBase(BaseModel):
    """Base inventory alert model."""
    product_id: int = Field(..., description="Product ID")
    sku: str = Field(..., description="Product SKU")
    alert_type: AlertType = Field(..., description="Type of alert")
    severity: Severity = Field(..., description="Alert severity")
    current_stock: int = Field(..., ge=0, description="Current stock level")
    recommended_action: str = Field(..., description="Recommended action")


class InventoryAlertCreate(InventoryAlertBase):
    """Model for creating inventory alert."""
    optimal_stock: Optional[int] = Field(None, ge=0)
    days_of_supply: Optional[float] = Field(None, ge=0)
    recommended_quantity: Optional[int] = Field(None, ge=0)
    urgency_score: Optional[float] = Field(None, ge=0, le=1)
    estimated_stockout_date: Optional[datetime] = None
    financial_impact: Optional[float] = Field(None)
    alert_message: Optional[str] = None


class InventoryAlertResponse(InventoryAlertBase):
    """Model for inventory alert response."""
    id: int
    optimal_stock: Optional[int]
    days_of_supply: Optional[float]
    recommended_quantity: Optional[int]
    urgency_score: Optional[float]
    estimated_stockout_date: Optional[datetime]
    financial_impact: Optional[float]
    alert_message: Optional[str]
    acknowledged: bool
    resolved: bool
    created_date: datetime
    resolved_date: Optional[datetime]
    
    class Config:
        from_attributes = True


class InventoryStats(BaseModel):
    """Model for inventory statistics."""
    total_products: int
    total_inventory_value: float
    total_stock_units: int
    
    # Stock levels
    products_in_stock: int
    products_out_of_stock: int
    products_low_stock: int
    products_overstocked: int
    
    # Metrics
    average_days_of_supply: float
    inventory_turnover_ratio: float
    stockout_rate: float
    overstock_rate: float
    
    # Financial metrics
    carrying_cost_annual: float
    potential_stockout_loss: float
    overstock_value: float
    
    # Alerts
    active_alerts: int
    critical_alerts: int
    high_priority_alerts: int
    
    calculated_at: datetime


class ReorderRecommendation(BaseModel):
    """Model for reorder recommendations."""
    product_id: int
    product_name: str
    sku: str
    category: str
    
    # Current status
    current_stock: int
    daily_usage_rate: float
    days_of_supply: float
    
    # Recommendation
    recommended_order_quantity: int
    reorder_point: int
    economic_order_quantity: int
    
    # Timing
    order_by_date: date
    estimated_delivery_date: date
    
    # Financial analysis
    order_cost: float
    carrying_cost: float
    stockout_risk: float
    
    # Supplier info
    supplier: str
    lead_time_days: int
    
    priority: str  # 'low', 'medium', 'high', 'urgent'
    confidence_score: float  # 0-1
    
    generated_at: datetime


class InventoryForecast(BaseModel):
    """Model for inventory level forecasting."""
    product_id: int
    product_name: str
    sku: str
    
    # Forecast data
    forecast_data: List[Dict[str, Any]] = Field(..., description="Daily inventory forecast")
    
    # Key predictions
    predicted_stockout_date: Optional[date] = None
    predicted_reorder_date: date
    minimum_predicted_stock: int
    
    # Risk assessment
    stockout_probability: float  # 0-1
    overstock_probability: float  # 0-1
    
    # Recommendations
    recommended_actions: List[str] = Field(default_factory=list)
    
    forecast_metadata: Dict[str, Any] = Field(default_factory=list)


class InventoryOptimization(BaseModel):
    """Model for inventory optimization recommendations."""
    product_id: int
    product_name: str
    sku: str
    
    # Current performance
    current_turnover: float
    current_service_level: float
    current_carrying_cost: float
    
    # Optimized parameters
    optimal_safety_stock: int
    optimal_reorder_point: int
    optimal_order_quantity: int
    
    # Expected improvements
    projected_turnover: float
    projected_service_level: float
    projected_cost_savings: float
    cost_savings_percentage: float
    
    # Implementation plan
    implementation_steps: List[str]
    expected_investment: Optional[float] = None
    payback_period_days: Optional[int] = None
    
    # Risk factors
    implementation_risks: List[str]
    mitigation_strategies: List[str]
    
    generated_at: datetime


class ABCAnalysis(BaseModel):
    """Model for ABC inventory analysis."""
    category: str  # 'A', 'B', or 'C'
    
    # Category metrics
    product_count: int
    revenue_percentage: float
    inventory_percentage: float
    
    # Products in category
    products: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Recommendations
    management_strategy: str
    review_frequency: str  # 'daily', 'weekly', 'monthly', 'quarterly'
    service_level_target: float
    
    analysis_period: Dict[str, date]
    generated_at: datetime


class InventorySearchRequest(BaseModel):
    """Model for inventory search request."""
    product_id: Optional[int] = None
    sku: Optional[str] = None
    category: Optional[str] = None
    transaction_type: Optional[TransactionType] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    min_stock_level: Optional[int] = Field(None, ge=0)
    max_stock_level: Optional[int] = Field(None, ge=0)
    supplier: Optional[str] = None
    sort_by: Optional[str] = Field("date", description="Sort field")
    sort_order: Optional[str] = Field("desc", description="Sort order: asc or desc")
    page: int = Field(1, ge=1, description="Page number")
    per_page: int = Field(50, ge=1, le=100, description="Items per page")
    
    @validator('sort_by')
    def validate_sort_by(cls, v):
        allowed_fields = ['id', 'date', 'product_id', 'sku', 'transaction_type', 
                         'stock_level_after', 'days_of_supply', 'inventory_value']
        if v not in allowed_fields:
            raise ValueError(f'Sort field must be one of: {allowed_fields}')
        return v
    
    @validator('sort_order')
    def validate_sort_order(cls, v):
        if v not in ['asc', 'desc']:
            raise ValueError('Sort order must be either "asc" or "desc"')
        return v


class BulkInventoryUpdate(BaseModel):
    """Model for bulk inventory updates."""
    updates: List[InventoryRecordCreate] = Field(..., min_items=1, max_items=1000)
    validate_stock_levels: bool = Field(True, description="Validate stock levels don't go negative")
    create_alerts: bool = Field(True, description="Create alerts for critical stock levels")


class InventoryHealthScore(BaseModel):
    """Model for overall inventory health assessment."""
    overall_score: float  # 0-100
    score_category: str  # 'excellent', 'good', 'fair', 'poor', 'critical'
    
    # Component scores
    stockout_risk_score: float
    overstock_risk_score: float
    turnover_score: float
    accuracy_score: float
    
    # Key metrics
    service_level: float
    inventory_accuracy: float
    turnover_ratio: float
    carrying_cost_percentage: float
    
    # Trends
    stockout_trend: str  # 'improving', 'stable', 'declining'
    turnover_trend: str
    accuracy_trend: str
    
    # Recommendations
    top_priorities: List[str]
    improvement_opportunities: List[str]
    
    calculated_at: datetime


class SupplierPerformance(BaseModel):
    """Model for supplier performance analysis."""
    supplier_name: str
    
    # Performance metrics
    on_time_delivery_rate: float
    order_accuracy_rate: float
    average_lead_time_days: float
    quality_score: float
    
    # Financial metrics
    total_spend: float
    average_order_value: float
    cost_per_unit_trend: str
    
    # Relationship metrics
    total_orders: int
    products_supplied: int
    return_rate: float
    
    # Assessment
    performance_rating: str  # 'excellent', 'good', 'average', 'poor'
    risk_level: str  # 'low', 'medium', 'high'
    
    # Recommendations
    recommendations: List[str]
    
    analysis_period: Dict[str, date]
    generated_at: datetime
