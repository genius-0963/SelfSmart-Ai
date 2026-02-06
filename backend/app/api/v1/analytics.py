"""
SmartShelf AI - Analytics Dashboard API v1

Endpoints for dashboard analytics and business intelligence.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import logging

from ...database import get_db
from ...database import Product, Sale, InventoryRecord
from ...core.exceptions import ValidationError

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/dashboard", response_model=Dict[str, Any])
async def get_dashboard_analytics(
    period_days: int = 30,
    db: Session = Depends(get_db)
):
    """Get comprehensive dashboard analytics."""
    if period_days not in [7, 30, 90, 365]:
        raise ValidationError("Period must be one of: 7, 30, 90, 365")
    
    start_date = datetime.utcnow() - timedelta(days=period_days)
    
    # Revenue metrics
    revenue_data = db.query(
        func.sum(Sale.total_revenue).label('total_revenue'),
        func.avg(Sale.total_revenue).label('avg_transaction_value'),
        func.count(Sale.id).label('total_transactions')
    ).filter(Sale.date >= start_date).first()
    
    # Sales metrics
    sales_data = db.query(
        func.sum(Sale.quantity_sold).label('total_units_sold'),
        func.count(Sale.id).label('total_sales')
    ).filter(Sale.date >= start_date).first()
    
    # Product metrics
    product_metrics = db.query(
        func.count(Product.id).label('total_products'),
        func.count(func.distinct(Sale.product_id)).label('active_products')
    ).join(Sale, Product.id == Sale.product_id, isouter=True).filter(
        Sale.date >= start_date
    ).first()
    
    # Top products
    top_products = db.query(
        Product.id,
        Product.product_name,
        Product.sku,
        func.sum(Sale.total_revenue).label('revenue'),
        func.sum(Sale.quantity_sold).label('quantity')
    ).join(Sale, Product.id == Sale.product_id).filter(
        Sale.date >= start_date
    ).group_by(Product.id).order_by(
        func.sum(Sale.total_revenue).desc()
    ).limit(5).all()
    
    # Daily sales trend
    daily_sales = db.query(
        Sale.date,
        func.sum(Sale.total_revenue).label('revenue'),
        func.sum(Sale.quantity_sold).label('quantity')
    ).filter(Sale.date >= start_date).group_by(Sale.date).order_by(Sale.date).all()
    
    # Category performance
    category_performance = db.query(
        Product.category,
        func.sum(Sale.total_revenue).label('revenue'),
        func.sum(Sale.quantity_sold).label('quantity'),
        func.count(func.distinct(Product.id)).label('product_count')
    ).join(Sale, Product.id == Sale.product_id).filter(
        Sale.date >= start_date
    ).group_by(Product.category).order_by(
        func.sum(Sale.total_revenue).desc()
    ).all()
    
    return {
        "period": {
            "days": period_days,
            "start_date": start_date.isoformat(),
            "end_date": datetime.utcnow().isoformat()
        },
        "revenue_metrics": {
            "total_revenue": float(revenue_data.total_revenue or 0),
            "average_daily_revenue": float((revenue_data.total_revenue or 0) / period_days),
            "average_transaction_value": float(revenue_data.avg_transaction_value or 0),
            "total_transactions": int(revenue_data.total_transactions or 0)
        },
        "sales_metrics": {
            "total_units_sold": int(sales_data.total_units_sold or 0),
            "average_daily_sales": float((sales_data.total_units_sold or 0) / period_days),
            "total_sales_transactions": int(sales_data.total_sales or 0)
        },
        "product_metrics": {
            "total_products": int(product_metrics.total_products or 0),
            "active_products": int(product_metrics.active_products or 0),
            "product_activation_rate": float((product_metrics.active_products or 0) / (product_metrics.total_products or 1) * 100)
        },
        "top_products": [
            {
                "product_id": p.id,
                "product_name": p.product_name,
                "sku": p.sku,
                "revenue": float(p.revenue),
                "quantity_sold": int(p.quantity)
            }
            for p in top_products
        ],
        "daily_trend": [
            {
                "date": ds.date.isoformat(),
                "revenue": float(ds.revenue),
                "quantity": int(ds.quantity)
            }
            for ds in daily_sales
        ],
        "category_performance": [
            {
                "category": cp.category,
                "revenue": float(cp.revenue),
                "quantity": int(cp.quantity),
                "product_count": int(cp.product_count),
                "revenue_per_product": float(cp.revenue / cp.product_count) if cp.product_count > 0 else 0
            }
            for cp in category_performance
        ],
        "insights": [
            f"Top performing product: {top_products[0].product_name if top_products else 'N/A'}",
            f"Average daily revenue: ${float((revenue_data.total_revenue or 0) / period_days):.2f}",
            f"Product activation rate: {float((product_metrics.active_products or 0) / (product_metrics.total_products or 1) * 100):.1f}%"
        ],
        "generated_at": datetime.utcnow().isoformat()
    }


@router.get("/revenue-trend", response_model=Dict[str, Any])
async def get_revenue_trend(
    period_days: int = 30,
    granularity: str = "daily",
    db: Session = Depends(get_db)
):
    """Get revenue trend data."""
    if granularity not in ["daily", "weekly", "monthly"]:
        raise ValidationError("Granularity must be one of: daily, weekly, monthly")
    
    start_date = datetime.utcnow() - timedelta(days=period_days)
    
    # Query based on granularity
    if granularity == "daily":
        date_format = func.date(Sale.date)
        date_label = "date"
    elif granularity == "weekly":
        date_format = func.date_trunc('week', Sale.date)
        date_label = "week"
    else:  # monthly
        date_format = func.date_trunc('month', Sale.date)
        date_label = "month"
    
    trend_data = db.query(
        date_format.label(date_label),
        func.sum(Sale.total_revenue).label('revenue'),
        func.count(Sale.id).label('transactions'),
        func.sum(Sale.quantity_sold).label('quantity')
    ).filter(Sale.date >= start_date).group_by(date_format).order_by(date_format).all()
    
    # Calculate growth rates
    trend_list = []
    for i, data in enumerate(trend_data):
        revenue = float(data.revenue)
        revenue_growth = None
        
        if i > 0:
            prev_revenue = float(trend_data[i-1].revenue)
            revenue_growth = ((revenue - prev_revenue) / prev_revenue * 100) if prev_revenue > 0 else None
        
        trend_list.append({
            "period": str(getattr(data, date_label)),
            "revenue": revenue,
            "transactions": int(data.transactions),
            "quantity": int(data.quantity),
            "revenue_growth_percent": revenue_growth
        })
    
    return {
        "period": f"Last {period_days} days",
        "granularity": granularity,
        "trend_data": trend_list,
        "summary": {
            "total_revenue": sum(float(d.revenue) for d in trend_data),
            "average_revenue": sum(float(d.revenue) for d in trend_data) / len(trend_data) if trend_data else 0,
            "growth_rate": trend_list[-1]["revenue_growth_percent"] if trend_list and trend_list[-1]["revenue_growth_percent"] else 0
        },
        "generated_at": datetime.utcnow().isoformat()
    }


@router.get("/product-performance/{product_id}", response_model=Dict[str, Any])
async def get_product_performance(
    product_id: int,
    period_days: int = 30,
    db: Session = Depends(get_db)
):
    """Get detailed performance metrics for a specific product."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise ValidationError("Product not found")
    
    start_date = datetime.utcnow() - timedelta(days=period_days)
    
    # Sales performance
    sales_performance = db.query(
        func.sum(Sale.total_revenue).label('revenue'),
        func.sum(Sale.quantity_sold).label('quantity'),
        func.count(Sale.id).label('transactions'),
        func.avg(Sale.unit_price).label('avg_price')
    ).filter(
        Sale.product_id == product_id,
        Sale.date >= start_date
    ).first()
    
    # Previous period comparison
    prev_start = start_date - timedelta(days=period_days)
    prev_performance = db.query(
        func.sum(Sale.total_revenue).label('revenue'),
        func.sum(Sale.quantity_sold).label('quantity')
    ).filter(
        Sale.product_id == product_id,
        Sale.date >= prev_start,
        Sale.date < start_date
    ).first()
    
    # Calculate growth
    current_revenue = float(sales_performance.revenue or 0)
    prev_revenue = float(prev_performance.revenue or 0)
    revenue_growth = ((current_revenue - prev_revenue) / prev_revenue * 100) if prev_revenue > 0 else None
    
    current_quantity = int(sales_performance.quantity or 0)
    prev_quantity = int(prev_performance.quantity or 0)
    quantity_growth = ((current_quantity - prev_quantity) / prev_quantity * 100) if prev_quantity > 0 else None
    
    # Daily performance
    daily_performance = db.query(
        Sale.date,
        func.sum(Sale.total_revenue).label('revenue'),
        func.sum(Sale.quantity_sold).label('quantity')
    ).filter(
        Sale.product_id == product_id,
        Sale.date >= start_date
    ).group_by(Sale.date).order_by(Sale.date).all()
    
    return {
        "product": {
            "id": product.id,
            "name": product.product_name,
            "sku": product.sku,
            "category": product.category,
            "base_price": product.base_price,
            "cost_price": product.cost_price
        },
        "period": {
            "days": period_days,
            "start_date": start_date.isoformat(),
            "end_date": datetime.utcnow().isoformat()
        },
        "performance_metrics": {
            "revenue": current_revenue,
            "quantity_sold": current_quantity,
            "transactions": int(sales_performance.transactions or 0),
            "average_price": float(sales_performance.avg_price or 0),
            "profit_margin": ((product.base_price - product.cost_price) / product.base_price * 100) if product.base_price > 0 else 0
        },
        "growth_metrics": {
            "revenue_growth_percent": revenue_growth,
            "quantity_growth_percent": quantity_growth
        },
        "daily_performance": [
            {
                "date": dp.date.isoformat(),
                "revenue": float(dp.revenue),
                "quantity": int(dp.quantity)
            }
            for dp in daily_performance
        ],
        "insights": [
            f"Average daily revenue: ${current_revenue / period_days:.2f}",
            f"Average daily sales: {current_quantity / period_days:.1f} units",
            f"Profit margin: {((product.base_price - product.cost_price) / product.base_price * 100) if product.base_price > 0 else 0:.1f}%"
        ],
        "generated_at": datetime.utcnow().isoformat()
    }


@router.get("/category-summary", response_model=Dict[str, Any])
async def get_category_summary(
    period_days: int = 30,
    db: Session = Depends(get_db)
):
    """Get category-wise performance summary."""
    start_date = datetime.utcnow() - timedelta(days=period_days)
    
    category_data = db.query(
        Product.category,
        func.count(func.distinct(Product.id)).label('total_products'),
        func.count(func.distinct(Sale.product_id)).label('active_products'),
        func.sum(Sale.total_revenue).label('revenue'),
        func.sum(Sale.quantity_sold).label('quantity'),
        func.avg(Sale.unit_price).label('avg_price')
    ).join(Sale, Product.id == Sale.product_id).filter(
        Sale.date >= start_date
    ).group_by(Product.category).order_by(
        func.sum(Sale.total_revenue).desc()
    ).all()
    
    categories = []
    for cat in category_data:
        categories.append({
            "category": cat.category,
            "total_products": int(cat.total_products),
            "active_products": int(cat.active_products),
            "revenue": float(cat.revenue or 0),
            "quantity": int(cat.quantity or 0),
            "average_price": float(cat.avg_price or 0),
            "revenue_per_product": float((cat.revenue or 0) / cat.active_products) if cat.active_products > 0 else 0,
            "activation_rate": float((cat.active_products / cat.total_products * 100)) if cat.total_products > 0 else 0
        })
    
    return {
        "period": f"Last {period_days} days",
        "categories": categories,
        "summary": {
            "total_categories": len(categories),
            "total_revenue": sum(c["revenue"] for c in categories),
            "top_category": categories[0]["category"] if categories else None
        },
        "generated_at": datetime.utcnow().isoformat()
    }
