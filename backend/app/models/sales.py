"""
Sales-related Pydantic models for API validation.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime, date


class SaleBase(BaseModel):
    """Base sale model with common fields."""
    product_id: int = Field(..., description="Product ID")
    sku: str = Field(..., description="Product SKU")
    date: datetime = Field(..., description="Sale date and time")
    quantity_sold: int = Field(..., gt=0, description="Quantity sold")
    unit_price: float = Field(..., gt=0, description="Unit price")
    promotion_active: bool = Field(False, description="Whether promotion was active")
    promotion_discount: float = Field(0, ge=0, le=1, description="Promotion discount (0-1)")
    
    @validator('unit_price')
    def calculate_total_revenue(cls, v, values):
        if 'quantity_sold' in values:
            return v  # Total revenue will be calculated in the service layer
        return v


class SaleCreate(SaleBase):
    """Model for creating a new sale record."""
    transaction_id: Optional[str] = Field(None, description="Unique transaction ID")
    hour: Optional[int] = Field(None, ge=0, le=23, description="Hour of day (0-23)")


class SaleResponse(SaleBase):
    """Model for sale response with additional fields."""
    id: int
    transaction_id: str
    total_revenue: float
    hour: int
    created_date: datetime
    
    class Config:
        from_attributes = True


class SalesAnalytics(BaseModel):
    """Model for sales analytics data."""
    period: str  # 'daily', 'weekly', 'monthly'
    start_date: date
    end_date: date
    
    # Revenue metrics
    total_revenue: float
    average_daily_revenue: float
    revenue_growth_rate: Optional[float] = None
    
    # Sales volume metrics
    total_units_sold: int
    average_daily_sales: float
    sales_growth_rate: Optional[float] = None
    
    # Transaction metrics
    total_transactions: int
    average_transaction_value: float
    unique_customers: Optional[int] = None
    
    # Product metrics
    top_products: List[Dict[str, Any]] = Field(default_factory=list)
    top_categories: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Promotion metrics
    promotion_revenue: float
    promotion_impact: float  # Percentage of revenue from promotions
    
    # Trend analysis
    revenue_trend: str  # 'increasing', 'decreasing', 'stable'
    sales_trend: str


class SalesForecastRequest(BaseModel):
    """Model for sales forecast request."""
    product_ids: Optional[List[int]] = Field(None, description="Specific product IDs to forecast")
    category: Optional[str] = Field(None, description="Forecast by category")
    forecast_days: int = Field(30, ge=1, le=365, description="Number of days to forecast")
    confidence_level: float = Field(0.95, ge=0.8, le=0.99, description="Confidence interval level")
    include_seasonality: bool = Field(True, description="Include seasonal patterns")
    include_promotions: bool = Field(True, description="Include promotion effects")


class SalesForecastResponse(BaseModel):
    """Model for sales forecast response."""
    product_id: int
    product_name: str
    sku: str
    
    # Forecast data
    forecast_data: List[Dict[str, Any]] = Field(..., description="Daily forecast data")
    
    # Summary metrics
    forecast_period_days: int
    predicted_total_revenue: float
    predicted_total_units: float
    confidence_level: float
    
    # Accuracy metrics
    model_version: str
    historical_accuracy: Optional[float] = None
    mean_absolute_percentage_error: Optional[float] = None


class SalesComparison(BaseModel):
    """Model for sales comparison between periods."""
    current_period: Dict[str, Any]
    previous_period: Dict[str, Any]
    
    # Comparison metrics
    revenue_change: float
    revenue_change_percent: float
    volume_change: float
    volume_change_percent: float
    transactions_change: float
    transactions_change_percent: float
    
    # Insights
    insights: List[str] = Field(default_factory=list)


class SalesSearchRequest(BaseModel):
    """Model for sales search request."""
    product_id: Optional[int] = None
    sku: Optional[str] = None
    category: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    promotion_active: Optional[bool] = None
    min_quantity: Optional[int] = Field(None, ge=0)
    max_quantity: Optional[int] = Field(None, ge=0)
    min_revenue: Optional[float] = Field(None, ge=0)
    max_revenue: Optional[float] = Field(None, ge=0)
    sort_by: Optional[str] = Field("date", description="Sort field")
    sort_order: Optional[str] = Field("desc", description="Sort order: asc or desc")
    page: int = Field(1, ge=1, description="Page number")
    per_page: int = Field(50, ge=1, le=100, description="Items per page")
    
    @validator('sort_by')
    def validate_sort_by(cls, v):
        allowed_fields = ['id', 'date', 'product_id', 'sku', 'quantity_sold', 
                         'total_revenue', 'unit_price', 'promotion_active']
        if v not in allowed_fields:
            raise ValueError(f'Sort field must be one of: {allowed_fields}')
        return v
    
    @validator('sort_order')
    def validate_sort_order(cls, v):
        if v not in ['asc', 'desc']:
            raise ValueError('Sort order must be either "asc" or "desc"')
        return v


class BulkSaleCreate(BaseModel):
    """Model for bulk sale creation."""
    sales: List[SaleCreate] = Field(..., min_items=1, max_items=5000, 
                                   description="List of sales to create")
    
    class Config:
        schema_extra = {
            "example": {
                "sales": [
                    {
                        "product_id": 1,
                        "sku": "ELEC00001",
                        "date": "2024-01-15T14:30:00",
                        "quantity_sold": 2,
                        "unit_price": 299.99,
                        "promotion_active": False,
                        "promotion_discount": 0.0,
                        "transaction_id": "TXN001234"
                    }
                ]
            }
        }


class BulkSaleResponse(BaseModel):
    """Model for bulk sale creation response."""
    success_count: int
    failed_count: int
    total_count: int
    errors: List[dict] = Field(default_factory=list, description="List of creation errors")
    created_sales: List[SaleResponse] = Field(default_factory=list)


class SalesReportRequest(BaseModel):
    """Model for sales report generation request."""
    report_type: str = Field(..., description="Report type: 'summary', 'detailed', 'forecast', 'comparison'")
    start_date: datetime = Field(..., description="Report start date")
    end_date: datetime = Field(..., description="Report end date")
    product_ids: Optional[List[int]] = None
    categories: Optional[List[str]] = None
    include_charts: bool = Field(True, description="Include chart data")
    format: str = Field("json", description="Report format: 'json', 'csv', 'pdf'")
    
    @validator('report_type')
    def validate_report_type(cls, v):
        allowed_types = ['summary', 'detailed', 'forecast', 'comparison']
        if v not in allowed_types:
            raise ValueError(f'Report type must be one of: {allowed_types}')
        return v
    
    @validator('format')
    def validate_format(cls, v):
        allowed_formats = ['json', 'csv', 'pdf']
        if v not in allowed_formats:
            raise ValueError(f'Format must be one of: {allowed_formats}')
        return v


class SalesReportResponse(BaseModel):
    """Model for sales report response."""
    report_id: str
    report_type: str
    generated_at: datetime
    period_covered: Dict[str, datetime]
    
    # Report data
    summary_metrics: Optional[Dict[str, Any]] = None
    detailed_data: Optional[List[Dict[str, Any]]] = None
    forecast_data: Optional[List[Dict[str, Any]]] = None
    comparison_data: Optional[Dict[str, Any]] = None
    
    # Chart data
    chart_data: Optional[Dict[str, Any]] = None
    
    # Metadata
    total_records: int
    file_size_bytes: Optional[int] = None
    download_url: Optional[str] = None
