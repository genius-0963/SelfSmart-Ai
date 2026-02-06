"""
SmartShelf AI - Inventory Intelligence API v1

Endpoints for inventory management, alerts, and optimization.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging

from ...database import get_db
from ...database import Product, InventoryRecord, InventoryAlert
from ...core.exceptions import NotFoundError

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/alerts", response_model=List[Dict[str, Any]])
async def get_inventory_alerts(
    severity: Optional[str] = None,
    alert_type: Optional[str] = None,
    acknowledged: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """Get inventory alerts with filtering."""
    query = db.query(InventoryAlert)
    
    if severity:
        query = query.filter(InventoryAlert.severity == severity)
    if alert_type:
        query = query.filter(InventoryAlert.alert_type == alert_type)
    if acknowledged is not None:
        query = query.filter(InventoryAlert.acknowledged == acknowledged)
    
    alerts = query.order_by(InventoryAlert.created_date.desc()).limit(50).all()
    
    return [
        {
            "id": alert.id,
            "product_id": alert.product_id,
            "sku": alert.sku,
            "alert_type": alert.alert_type,
            "severity": alert.severity,
            "current_stock": alert.current_stock,
            "recommended_action": alert.recommended_action,
            "urgency_score": alert.urgency_score,
            "estimated_stockout_date": alert.estimated_stockout_date.isoformat() if alert.estimated_stockout_date else None,
            "financial_impact": alert.financial_impact,
            "alert_message": alert.alert_message,
            "acknowledged": alert.acknowledged,
            "created_date": alert.created_date.isoformat()
        }
        for alert in alerts
    ]


@router.get("/levels/{product_id}", response_model=Dict[str, Any])
async def get_inventory_levels(
    product_id: int,
    days_back: int = 30,
    db: Session = Depends(get_db)
):
    """Get inventory levels and trends for a product."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise NotFoundError("Product", product_id)
    
    # Get recent inventory records
    inventory_records = db.query(InventoryRecord).filter(
        InventoryRecord.product_id == product_id,
        InventoryRecord.date >= datetime.utcnow() - timedelta(days=days_back),
        InventoryRecord.transaction_type == 'daily_snapshot'
    ).order_by(InventoryRecord.date).all()
    
    if not inventory_records:
        return {
            "product_id": product_id,
            "product_name": product.product_name,
            "current_stock": 0,
            "trend": "no_data",
            "days_of_supply": 0,
            "optimal_stock": 50,
            "stock_status": "unknown",
            "history": []
        }
    
    # Calculate metrics
    current_stock = inventory_records[-1].stock_level_after
    avg_daily_usage = sum(r.quantity_change for r in inventory_records if r.quantity_change < 0) / len(inventory_records) if inventory_records else 1
    days_of_supply = current_stock / abs(avg_daily_usage) if avg_daily_usage != 0 else 0
    
    # Determine trend
    if len(inventory_records) >= 7:
        recent_avg = sum(r.stock_level_after for r in inventory_records[-7:]) / 7
        earlier_avg = sum(r.stock_level_after for r in inventory_records[-14:-7]) / 7 if len(inventory_records) >= 14 else recent_avg
        
        if recent_avg > earlier_avg * 1.1:
            trend = "increasing"
        elif recent_avg < earlier_avg * 0.9:
            trend = "decreasing"
        else:
            trend = "stable"
    else:
        trend = "insufficient_data"
    
    # Stock status
    if days_of_supply < 3:
        stock_status = "critical"
    elif days_of_supply < 7:
        stock_status = "low"
    elif days_of_supply > 30:
        stock_status = "overstock"
    else:
        stock_status = "optimal"
    
    return {
        "product_id": product_id,
        "product_name": product.product_name,
        "sku": product.sku,
        "current_stock": current_stock,
        "optimal_stock": inventory_records[-1].optimal_stock_level or 50,
        "days_of_supply": days_of_supply,
        "stock_status": stock_status,
        "trend": trend,
        "avg_daily_usage": abs(avg_daily_usage),
        "inventory_value": current_stock * product.cost_price,
        "history": [
            {
                "date": record.date.isoformat(),
                "stock_level": record.stock_level_after,
                "transaction_type": record.transaction_type
            }
            for record in inventory_records[-30:]  # Last 30 records
        ],
        "last_updated": inventory_records[-1].date.isoformat()
    }


@router.get("/reorder-recommendations", response_model=List[Dict[str, Any]])
async def get_reorder_recommendations(db: Session = Depends(get_db)):
    """Get reorder recommendations for products needing restock."""
    # Get products with low stock
    low_stock_products = db.query(InventoryRecord).filter(
        InventoryRecord.transaction_type == 'daily_snapshot',
        InventoryRecord.stock_level_after < 20
    ).order_by(InventoryRecord.stock_level_after).limit(20).all()
    
    recommendations = []
    for record in low_stock_products:
        product = db.query(Product).filter(Product.id == record.product_id).first()
        if not product:
            continue
        
        # Calculate recommended order quantity
        optimal_stock = record.optimal_stock_level or 50
        recommended_quantity = optimal_stock - record.stock_level_after
        
        recommendations.append({
            "product_id": record.product_id,
            "product_name": product.product_name,
            "sku": product.sku,
            "current_stock": record.stock_level_after,
            "recommended_quantity": max(0, recommended_quantity),
            "priority": "urgent" if record.stock_level_after < 5 else "high",
            "supplier": product.supplier,
            "estimated_cost": recommended_quantity * product.cost_price,
            "days_of_supply": record.days_of_supply or 0,
            "order_by_date": (datetime.utcnow() + timedelta(days=1)).isoformat()
        })
    
    return recommendations


@router.get("/dashboard", response_model=Dict[str, Any])
async def get_inventory_dashboard(db: Session = Depends(get_db)):
    """Get inventory intelligence dashboard data."""
    # Get summary statistics
    total_products = db.query(Product).count()
    
    # Get current inventory levels
    latest_inventory = db.query(InventoryRecord).filter(
        InventoryRecord.transaction_type == 'daily_snapshot'
    ).group_by(InventoryRecord.product_id).having(
        InventoryRecord.date == db.func.max(InventoryRecord.date)
    ).all()
    
    # Calculate metrics
    in_stock = sum(1 for r in latest_inventory if r.stock_level_after > 0)
    out_of_stock = sum(1 for r in latest_inventory if r.stock_level_after == 0)
    low_stock = sum(1 for r in latest_inventory if 0 < r.stock_level_after < 10)
    
    # Get active alerts
    active_alerts = db.query(InventoryAlert).filter(
        InventoryAlert.resolved == False
    ).count()
    
    critical_alerts = db.query(InventoryAlert).filter(
        InventoryAlert.resolved == False,
        InventoryAlert.severity == 'critical'
    ).count()
    
    return {
        "summary": {
            "total_products": total_products,
            "products_in_stock": in_stock,
            "products_out_of_stock": out_of_stock,
            "products_low_stock": low_stock,
            "stock_availability_percentage": (in_stock / total_products * 100) if total_products > 0 else 0,
            "active_alerts": active_alerts,
            "critical_alerts": critical_alerts
        },
        "metrics": {
            "total_inventory_value": sum(r.inventory_value or 0 for r in latest_inventory),
            "average_days_of_supply": sum(r.days_of_supply or 0 for r in latest_inventory) / len(latest_inventory) if latest_inventory else 0,
            "stockout_rate": (out_of_stock / total_products * 100) if total_products > 0 else 0
        },
        "insights": [
            f"{out_of_stock} products are currently out of stock",
            f"{low_stock} products need immediate attention",
            f"Average days of supply across all products: {sum(r.days_of_supply or 0 for r in latest_inventory) / len(latest_inventory) if latest_inventory else 0:.1f} days"
        ],
        "generated_at": datetime.utcnow().isoformat()
    }


@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: int, db: Session = Depends(get_db)):
    """Acknowledge an inventory alert."""
    alert = db.query(InventoryAlert).filter(InventoryAlert.id == alert_id).first()
    if not alert:
        raise NotFoundError("Alert", alert_id)
    
    alert.acknowledged = True
    db.commit()
    
    return {"message": f"Alert {alert_id} acknowledged successfully"}


@router.post("/alerts/{alert_id}/resolve")
async def resolve_alert(alert_id: int, db: Session = Depends(get_db)):
    """Resolve an inventory alert."""
    alert = db.query(InventoryAlert).filter(InventoryAlert.id == alert_id).first()
    if not alert:
        raise NotFoundError("Alert", alert_id)
    
    alert.resolved = True
    alert.resolved_date = datetime.utcnow()
    db.commit()
    
    return {"message": f"Alert {alert_id} resolved successfully"}
