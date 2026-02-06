"""
Product-related Pydantic models for API validation.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime


class ProductBase(BaseModel):
    """Base product model with common fields."""
    sku: str = Field(..., min_length=3, max_length=50, description="Unique product SKU")
    product_name: str = Field(..., min_length=1, max_length=200, description="Product name")
    category: str = Field(..., description="Product category")
    brand: Optional[str] = Field(None, max_length=100, description="Product brand")
    base_price: float = Field(..., gt=0, description="Base selling price")
    cost_price: float = Field(..., gt=0, description="Cost price")
    weight_kg: Optional[float] = Field(None, ge=0, description="Product weight in kg")
    dimensions_cm: Optional[str] = Field(None, max_length=50, description="Product dimensions (LxWxH)")
    supplier: Optional[str] = Field(None, max_length=100, description="Supplier name")
    status: str = Field("active", description="Product status")
    
    @validator('status')
    def validate_status(cls, v):
        allowed_statuses = ['active', 'discontinued', 'out_of_stock', 'coming_soon']
        if v not in allowed_statuses:
            raise ValueError(f'Status must be one of: {allowed_statuses}')
        return v
    
    @validator('base_price')
    def validate_prices(cls, v, values):
        if 'cost_price' in values and v <= values['cost_price']:
            raise ValueError('Base price must be greater than cost price')
        return v


class ProductCreate(ProductBase):
    """Model for creating a new product."""
    pass


class ProductUpdate(BaseModel):
    """Model for updating an existing product."""
    product_name: Optional[str] = Field(None, min_length=1, max_length=200)
    category: Optional[str] = None
    brand: Optional[str] = Field(None, max_length=100)
    base_price: Optional[float] = Field(None, gt=0)
    cost_price: Optional[float] = Field(None, gt=0)
    weight_kg: Optional[float] = Field(None, ge=0)
    dimensions_cm: Optional[str] = Field(None, max_length=50)
    supplier: Optional[str] = Field(None, max_length=100)
    status: Optional[str] = None
    
    @validator('status')
    def validate_status(cls, v):
        if v is not None:
            allowed_statuses = ['active', 'discontinued', 'out_of_stock', 'coming_soon']
            if v not in allowed_statuses:
                raise ValueError(f'Status must be one of: {allowed_statuses}')
        return v


class ProductResponse(ProductBase):
    """Model for product response with additional fields."""
    id: int
    created_date: datetime
    updated_date: datetime
    
    # Computed fields
    profit_margin: Optional[float] = Field(None, description="Profit margin percentage")
    days_of_supply: Optional[float] = Field(None, description="Current days of supply")
    total_revenue: Optional[float] = Field(None, description="Total revenue to date")
    
    class Config:
        from_attributes = True


class ProductListResponse(BaseModel):
    """Model for paginated product list response."""
    products: List[ProductResponse]
    total: int
    page: int
    per_page: int
    total_pages: int


class ProductAnalytics(BaseModel):
    """Model for product analytics data."""
    product_id: int
    product_name: str
    category: str
    total_revenue: float
    total_units_sold: int
    average_daily_sales: float
    revenue_trend: str  # 'increasing', 'decreasing', 'stable'
    profit_margin: float
    inventory_turnover: float
    days_of_supply: float
    stockout_risk: str  # 'low', 'medium', 'high'
    price_elasticity: Optional[float] = None


class ProductSearchRequest(BaseModel):
    """Model for product search request."""
    query: Optional[str] = Field(None, description="Search query for product name or SKU")
    category: Optional[str] = Field(None, description="Filter by category")
    brand: Optional[str] = Field(None, description="Filter by brand")
    supplier: Optional[str] = Field(None, description="Filter by supplier")
    status: Optional[str] = Field(None, description="Filter by status")
    min_price: Optional[float] = Field(None, ge=0, description="Minimum price filter")
    max_price: Optional[float] = Field(None, ge=0, description="Maximum price filter")
    sort_by: Optional[str] = Field("created_date", description="Sort field")
    sort_order: Optional[str] = Field("desc", description="Sort order: asc or desc")
    page: int = Field(1, ge=1, description="Page number")
    per_page: int = Field(50, ge=1, le=100, description="Items per page")
    
    @validator('sort_by')
    def validate_sort_by(cls, v):
        allowed_fields = ['id', 'sku', 'product_name', 'category', 'brand', 'base_price', 
                         'created_date', 'updated_date', 'total_revenue', 'days_of_supply']
        if v not in allowed_fields:
            raise ValueError(f'Sort field must be one of: {allowed_fields}')
        return v
    
    @validator('sort_order')
    def validate_sort_order(cls, v):
        if v not in ['asc', 'desc']:
            raise ValueError('Sort order must be either "asc" or "desc"')
        return v


class BulkProductCreate(BaseModel):
    """Model for bulk product creation."""
    products: List[ProductCreate] = Field(..., min_items=1, max_items=1000, 
                                         description="List of products to create")
    
    class Config:
        schema_extra = {
            "example": {
                "products": [
                    {
                        "sku": "ELEC00001",
                        "product_name": "TechPro Phone 001",
                        "category": "Electronics",
                        "brand": "TechPro",
                        "base_price": 299.99,
                        "cost_price": 150.00,
                        "weight_kg": 0.5,
                        "dimensions_cm": "15.0x7.5x0.8",
                        "supplier": "Global Supplies Inc",
                        "status": "active"
                    }
                ]
            }
        }


class BulkProductResponse(BaseModel):
    """Model for bulk product creation response."""
    success_count: int
    failed_count: int
    total_count: int
    errors: List[dict] = Field(default_factory=list, description="List of creation errors")
    created_products: List[ProductResponse] = Field(default_factory=list)
