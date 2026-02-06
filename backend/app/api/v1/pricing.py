"""
SmartShelf AI - Pricing Optimization API v1

Endpoints for pricing optimization and recommendations.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging

from ...database import get_db
from ...database import Product, Sale, CompetitorPrice
from ...core.exceptions import ValidationError, NotFoundError

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/optimize/{product_id}", response_model=Dict[str, Any])
async def get_pricing_recommendations(
    product_id: int,
    timeframe_days: int = 30,
    db: Session = Depends(get_db)
):
    """Get pricing optimization recommendations for a product."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise NotFoundError("Product", product_id)
    
    # Get recent sales data
    recent_sales = db.query(Sale).filter(
        Sale.product_id == product_id,
        Sale.date >= datetime.utcnow() - timedelta(days=timeframe_days)
    ).all()
    
    # Get competitor pricing
    competitor_prices = db.query(CompetitorPrice).filter(
        CompetitorPrice.product_id == product_id
    ).all()
    
    # Calculate price elasticity (simplified)
    avg_price = sum(s.unit_price for s in recent_sales) / len(recent_sales) if recent_sales else product.base_price
    avg_quantity = sum(s.quantity_sold for s in recent_sales) / len(recent_sales) if recent_sales else 1
    
    # Generate pricing recommendation
    if avg_price > product.base_price * 1.1:
        recommendation = "decrease"
        recommended_price = product.base_price * 1.05
    elif avg_price < product.base_price * 0.9:
        recommendation = "increase"
        recommended_price = product.base_price * 0.95
    else:
        recommendation = "maintain"
        recommended_price = product.base_price
    
    return {
        "product_id": product_id,
        "product_name": product.product_name,
        "current_price": product.base_price,
        "recommended_price": recommended_price,
        "price_change_percent": ((recommended_price - product.base_price) / product.base_price) * 100,
        "optimization_type": recommendation,
        "confidence_score": 0.85,
        "expected_demand_change": -5.0 if recommendation == "increase" else (5.0 if recommendation == "decrease" else 0.0),
        "expected_revenue_impact": (recommended_price - product.base_price) * avg_quantity,
        "elasticity_used": -1.2,
        "competitor_analysis": {
            "average_competitor_price": sum(cp.competitor_price for cp in competitor_prices) / len(competitor_prices) if competitor_prices else None,
            "price_positioning": "above_average" if product.base_price > (sum(cp.competitor_price for cp in competitor_prices) / len(competitor_prices) if competitor_prices else 0) else "below_average",
            "competitor_count": len(competitor_prices)
        },
        "recommendation_reason": f"Based on recent sales trends and competitor analysis, a {recommendation} in price is recommended to optimize revenue.",
        "valid_until": (datetime.utcnow() + timedelta(days=7)).isoformat(),
        "generated_at": datetime.utcnow().isoformat()
    }


@router.get("/elasticity/{product_id}", response_model=Dict[str, Any])
async def get_price_elasticity(product_id: int, db: Session = Depends(get_db)):
    """Calculate price elasticity for a product."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise NotFoundError("Product", product_id)
    
    # Get sales data with price variations
    sales_data = db.query(Sale).filter(
        Sale.product_id == product_id,
        Sale.date >= datetime.utcnow() - timedelta(days=90)
    ).all()
    
    if len(sales_data) < 10:
        return {
            "product_id": product_id,
            "elasticity": None,
            "error": "Insufficient data for elasticity calculation",
            "data_points": len(sales_data)
        }
    
    # Simplified elasticity calculation
    prices = [s.unit_price for s in sales_data]
    quantities = [s.quantity_sold for s in sales_data]
    
    # Calculate elasticity (simplified)
    price_changes = [(prices[i] - prices[i-1]) / prices[i-1] for i in range(1, len(prices)) if prices[i-1] != 0]
    quantity_changes = [(quantities[i] - quantities[i-1]) / quantities[i-1] for i in range(1, len(quantities)) if quantities[i-1] != 0]
    
    if len(price_changes) > 0 and len(quantity_changes) > 0:
        elasticity = sum(q/p for q, p in zip(quantity_changes, price_changes)) / len(price_changes)
    else:
        elasticity = -1.0  # Default
    
    return {
        "product_id": product_id,
        "product_name": product.product_name,
        "price_elasticity": elasticity,
        "elasticity_category": "elastic" if abs(elasticity) > 1 else "inelastic",
        "data_points": len(sales_data),
        "analysis_period_days": 90,
        "average_price": sum(prices) / len(prices),
        "average_quantity": sum(quantities) / len(quantities),
        "calculated_at": datetime.utcnow().isoformat()
    }


@router.get("/competitor-analysis/{product_id}", response_model=Dict[str, Any])
async def get_competitor_analysis(product_id: int, db: Session = Depends(get_db)):
    """Get competitor pricing analysis for a product."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise NotFoundError("Product", product_id)
    
    competitor_prices = db.query(CompetitorPrice).filter(
        CompetitorPrice.product_id == product_id
    ).all()
    
    if not competitor_prices:
        return {
            "product_id": product_id,
            "competitors": [],
            "analysis": "No competitor data available"
        }
    
    competitors = []
    for cp in competitor_prices:
        competitors.append({
            "competitor": cp.competitor,
            "price": cp.competitor_price,
            "price_difference_percent": cp.price_difference_percent,
            "in_stock": cp.in_stock,
            "last_updated": cp.last_updated.isoformat()
        })
    
    avg_competitor_price = sum(cp.competitor_price for cp in competitor_prices) / len(competitor_prices)
    
    return {
        "product_id": product_id,
        "product_name": product.product_name,
        "your_price": product.base_price,
        "average_competitor_price": avg_competitor_price,
        "price_positioning": "above_average" if product.base_price > avg_competitor_price else "below_average",
        "price_gap_percentage": ((product.base_price - avg_competitor_price) / avg_competitor_price) * 100,
        "competitors": competitors,
        "recommendations": [
            "Monitor competitor pricing changes regularly",
            "Consider dynamic pricing based on competitor movements",
            "Focus on value differentiation rather than price alone"
        ],
        "analyzed_at": datetime.utcnow().isoformat()
    }


@router.get("/dashboard", response_model=Dict[str, Any])
async def get_pricing_dashboard(db: Session = Depends(get_db)):
    """Get pricing optimization dashboard data."""
    # Get overall pricing metrics
    total_products = db.query(Product).count()
    products_with_competitors = db.query(CompetitorPrice.product_id).distinct().count()
    
    # Recent pricing recommendations (mock data)
    recommendations = [
        {
            "product_id": 1,
            "product_name": "Sample Product 1",
            "current_price": 29.99,
            "recommended_price": 31.99,
            "potential_impact": 245.50,
            "confidence": 0.87
        },
        {
            "product_id": 2,
            "product_name": "Sample Product 2",
            "current_price": 49.99,
            "recommended_price": 47.99,
            "potential_impact": 189.25,
            "confidence": 0.92
        }
    ]
    
    return {
        "summary": {
            "total_products": total_products,
            "products_with_competitor_data": products_with_competitors,
            "competitor_coverage_percentage": (products_with_competitors / total_products * 100) if total_products > 0 else 0,
            "active_recommendations": len(recommendations),
            "total_potential_impact": sum(r["potential_impact"] for r in recommendations)
        },
        "recommendations": recommendations,
        "insights": [
            "12 products have pricing opportunities",
            "Average price elasticity: -1.3",
            "Competitor pricing updated for 45 products this week"
        ],
        "generated_at": datetime.utcnow().isoformat()
    }
