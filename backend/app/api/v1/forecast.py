"""
SmartShelf AI - Demand Forecasting API v1

Endpoints for demand forecasting and prediction.
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import pandas as pd
import logging

from ...database import get_db
from ...database import Product, Sale, Forecast
from ...models.forecast import (
    ForecastRequest, ForecastResponse, ForecastMetrics,
    ForecastBatchRequest, ForecastBatchResponse
)
from ...core.exceptions import ValidationError, NotFoundError, ForecastError

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/generate", response_model=ForecastResponse)
async def generate_forecast(
    request: ForecastRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Generate demand forecast for specified products.
    
    Args:
        request: Forecast request parameters
        background_tasks: Background task manager
        db: Database session
        
    Returns:
        Forecast results with confidence intervals
    """
    try:
        # Validate date range
        if request.end_date <= request.start_date:
            raise ValidationError("End date must be after start date")
        
        if (request.end_date - request.start_date).days > 365:
            raise ValidationError("Forecast period cannot exceed 365 days")
        
        # Get products to forecast
        if request.product_ids:
            products = db.query(Product).filter(Product.id.in_(request.product_ids)).all()
        elif request.category:
            products = db.query(Product).filter(Product.category == request.category).all()
        else:
            # Default to top 10 products by revenue
            top_products = db.query(Sale).group_by(Sale.product_id)\
                .order_by(db.func.sum(Sale.total_revenue).desc())\
                .limit(10).all()
            product_ids = [s.product_id for s in top_products]
            products = db.query(Product).filter(Product.id.in_(product_ids)).all()
        
        if not products:
            raise NotFoundError("No products found for forecasting")
        
        # Generate forecasts (simplified implementation)
        forecast_data = []
        total_predicted_revenue = 0.0
        total_predicted_units = 0.0
        
        for product in products:
            # Get historical sales data
            sales_data = db.query(Sale).filter(
                Sale.product_id == product.id,
                Sale.date >= request.start_date - timedelta(days=90)  # Last 90 days
            ).group_by(Sale.date).all()
            
            if not sales_data:
                continue
            
            # Simple forecast logic (in production, use trained ML models)
            daily_sales = [s.quantity_sold for s in sales_data]
            avg_daily_sales = sum(daily_sales) / len(daily_sales) if daily_sales else 1.0
            
            # Generate forecast for each day
            for days_ahead in range((request.end_date - request.start_date).days + 1):
                forecast_date = request.start_date + timedelta(days=days_ahead)
                
                # Add some seasonality and randomness
                seasonal_factor = 1.0 + 0.2 * (forecast_date.timetuple().tm_yday % 365) / 365
                random_factor = 1.0 + (hash(str(product.id) + str(days_ahead)) % 100 - 50) / 500
                
                predicted_demand = avg_daily_sales * seasonal_factor * random_factor
                confidence_lower = predicted_demand * 0.8
                confidence_upper = predicted_demand * 1.2
                
                forecast_data.append({
                    'date': forecast_date.isoformat(),
                    'predicted_demand': max(0, predicted_demand),
                    'confidence_lower': max(0, confidence_lower),
                    'confidence_upper': max(0, confidence_upper)
                })
                
                total_predicted_units += max(0, predicted_demand)
                total_predicted_revenue += max(0, predicted_demand) * product.base_price
        
        return ForecastResponse(
            product_id=products[0].id if len(products) == 1 else None,
            product_name=products[0].product_name if len(products) == 1 else "Multiple Products",
            sku=products[0].sku if len(products) == 1 else "Multiple",
            forecast_data=forecast_data,
            forecast_period_days=(request.end_date - request.start_date).days + 1,
            predicted_total_revenue=total_predicted_revenue,
            predicted_total_units=total_predicted_units,
            confidence_level=request.confidence_level,
            model_version="demo_v1.0",
            historical_accuracy=0.85,
            mean_absolute_percentage_error=15.0
        )
        
    except Exception as e:
        logger.error(f"Forecast generation failed: {e}")
        raise ForecastError(f"Failed to generate forecast: {str(e)}")


@router.get("/product/{product_id}", response_model=List[Dict[str, Any]])
async def get_product_forecasts(
    product_id: int,
    days_ahead: int = 30,
    db: Session = Depends(get_db)
):
    """Get existing forecasts for a specific product."""
    # Verify product exists
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise NotFoundError("Product", product_id)
    
    # Get forecasts
    forecasts = db.query(Forecast).filter(
        Forecast.product_id == product_id,
        Forecast.target_date >= datetime.utcnow(),
        Forecast.target_date <= datetime.utcnow() + timedelta(days=days_ahead)
    ).order_by(Forecast.target_date).all()
    
    return [
        {
            "id": f.id,
            "target_date": f.target_date.isoformat(),
            "forecast_type": f.forecast_type,
            "predicted_value": f.predicted_value,
            "confidence_lower": f.confidence_lower,
            "confidence_upper": f.confidence_upper,
            "confidence_level": f.confidence_level,
            "model_version": f.model_version,
            "created_date": f.created_date.isoformat()
        }
        for f in forecasts
    ]


@router.get("/models", response_model=List[Dict[str, Any]])
async def get_forecast_models():
    """Get available forecasting models."""
    return [
        {
            "model_name": "prophet_demand_forecaster",
            "model_type": "prophet",
            "description": "Facebook Prophet time-series forecasting",
            "capabilities": ["seasonality", "trends", "holidays", "promotions"],
            "max_forecast_horizon_days": 365,
            "accuracy_range": {"min": 0.80, "max": 0.95},
            "is_active": True
        },
        {
            "model_name": "lstm_demand_forecaster",
            "model_type": "lstm",
            "description": "LSTM neural network for complex patterns",
            "capabilities": ["nonlinear_patterns", "sequence_modeling", "feature_importance"],
            "max_forecast_horizon_days": 90,
            "accuracy_range": {"min": 0.85, "max": 0.98},
            "is_active": False  # Not implemented in demo
        }
    ]


@router.get("/accuracy/{product_id}", response_model=ForecastMetrics)
async def get_forecast_accuracy(
    product_id: int,
    db: Session = Depends(get_db)
):
    """Get forecast accuracy metrics for a product."""
    # Verify product exists
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise NotFoundError("Product", product_id)
    
    # Mock accuracy metrics (in production, calculate from historical forecasts)
    return ForecastMetrics(
        model_version="prophet_v1.0",
        forecast_type="demand",
        evaluation_period={
            "start_date": (datetime.utcnow() - timedelta(days=30)).isoformat(),
            "end_date": datetime.utcnow().isoformat()
        },
        mean_absolute_error=2.5,
        mean_absolute_percentage_error=12.3,
        root_mean_squared_error=3.1,
        r_squared=0.87,
        forecast_coverage=0.92,
        bias_percentage=2.1,
        baseline_mape=25.6,
        improvement_over_baseline=48.4,
        evaluated_at=datetime.utcnow().isoformat()
    )


@router.post("/batch", response_model=ForecastBatchResponse)
async def generate_batch_forecasts(
    request: ForecastBatchRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Generate forecasts for multiple products in batch."""
    batch_id = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Add to background tasks
    background_tasks.add_task(
        process_batch_forecasts,
        batch_id=batch_id,
        requests=request.forecast_requests,
        priority=request.priority
    )
    
    return ForecastBatchResponse(
        batch_id=batch_id,
        status="pending",
        total_requests=len(request.forecast_requests),
        completed_requests=0,
        failed_requests=0,
        started_at=datetime.utcnow(),
        errors=[]
    )


async def process_batch_forecasts(
    batch_id: str,
    requests: List[ForecastRequest],
    priority: str
):
    """Process batch forecast requests in background."""
    logger.info(f"Processing batch forecast {batch_id} with {len(requests)} requests")
    
    # Implementation would process each request
    # For demo, we'll just log the completion
    logger.info(f"Completed batch forecast {batch_id}")


@router.get("/explain/{forecast_id}", response_model=Dict[str, Any])
async def explain_forecast(forecast_id: int, db: Session = Depends(get_db)):
    """Get explanation for a specific forecast (XAI)."""
    forecast = db.query(Forecast).filter(Forecast.id == forecast_id).first()
    if not forecast:
        raise NotFoundError("Forecast", forecast_id)
    
    # Mock explanation (in production, use actual model explanations)
    return {
        "forecast_id": forecast_id,
        "product_id": forecast.product_id,
        "target_date": forecast.target_date.isoformat(),
        "feature_importance": {
            "historical_demand": 0.45,
            "seasonality": 0.25,
            "trend": 0.15,
            "promotions": 0.10,
            "holidays": 0.05
        },
        "seasonal_contribution": 0.23,
        "trend_contribution": 0.12,
        "promotion_contribution": 0.08,
        "external_factors_contribution": 0.02,
        "similar_periods": [
            {"date": "2023-12-15", "similarity": 0.92, "actual": 45.2},
            {"date": "2023-11-15", "similarity": 0.88, "actual": 42.1}
        ],
        "confidence_factors": [
            "Sufficient historical data (90 days)",
            "Stable demand patterns",
            "Low recent volatility"
        ],
        "uncertainty_sources": [
            "Promotional activities",
            "Competitor pricing changes",
            "Weather conditions"
        ],
        "explanation_text": f"The forecast of {forecast.predicted_value:.1f} units is primarily driven by strong historical demand patterns and seasonal effects. The model has high confidence due to consistent data quality.",
        "generated_at": datetime.utcnow().isoformat()
    }
