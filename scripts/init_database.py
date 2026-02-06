#!/usr/bin/env python3
"""
SmartShelf AI - Database Initialization Script

Creates database tables and loads initial data from CSV files.
"""

import sys
import os
from pathlib import Path

# Add backend to path for imports
sys.path.append(str(Path(__file__).parent.parent / "backend"))

import pandas as pd
from sqlalchemy.orm import Session
from backend.app.database import engine, SessionLocal, create_tables, get_database_stats
from backend.app.database import Product, Sale, InventoryRecord, CompetitorPrice
from datetime import datetime, timedelta


def load_products_from_csv(db: Session, csv_path: str) -> int:
    """Load products from CSV file into database."""
    print("📦 Loading products...")
    
    df = pd.read_csv(csv_path)
    
    loaded_count = 0
    for _, row in df.iterrows():
        product = Product(
            sku=row['sku'],
            product_name=row['product_name'],
            category=row['category'],
            brand=row['brand'],
            base_price=row['base_price'],
            cost_price=row['cost_price'],
            weight_kg=row['weight_kg'],
            dimensions_cm=row['dimensions_cm'],
            supplier=row['supplier'],
            status=row['status'],
            created_date=pd.to_datetime(row['created_date']) if pd.notna(row.get('created_date')) else datetime.utcnow()
        )
        db.add(product)
        loaded_count += 1
    
    db.commit()
    print(f"✅ Loaded {loaded_count} products")
    return loaded_count


def load_sales_from_csv(db: Session, csv_path: str) -> int:
    """Load sales from CSV file into database."""
    print("💰 Loading sales...")
    
    df = pd.read_csv(csv_path)
    df['date'] = pd.to_datetime(df['date'])
    
    loaded_count = 0
    for _, row in df.iterrows():
        sale = Sale(
            transaction_id=row['transaction_id'],
            product_id=row['product_id'],
            sku=row['sku'],
            date=row['date'],
            hour=row['hour'],
            quantity_sold=row['quantity_sold'],
            unit_price=row['unit_price'],
            total_revenue=row['total_revenue'],
            promotion_active=row['promotion_active'],
            promotion_discount=row['promotion_discount']
        )
        db.add(sale)
        loaded_count += 1
        
        # Batch commit every 1000 records
        if loaded_count % 1000 == 0:
            db.commit()
    
    db.commit()
    print(f"✅ Loaded {loaded_count} sales records")
    return loaded_count


def load_inventory_from_csv(db: Session, csv_path: str) -> int:
    """Load inventory records from CSV file into database."""
    print("📦 Loading inventory records...")
    
    df = pd.read_csv(csv_path)
    df['date'] = pd.to_datetime(df['date'])
    
    loaded_count = 0
    for _, row in df.iterrows():
        inventory = InventoryRecord(
            product_id=row['product_id'],
            sku=row['sku'],
            date=row['date'],
            transaction_type=row['transaction_type'],
            quantity_change=row['quantity_change'],
            stock_level_after=row['stock_level_after'],
            optimal_stock_level=row.get('optimal_stock_level'),
            days_of_supply=row.get('days_of_supply'),
            inventory_value=row.get('inventory_value'),
            supplier=row.get('supplier'),
            cost_per_unit=row.get('cost_per_unit'),
            lost_sales=row.get('lost_sales', 0),
            stockout_reason=row.get('stockout_reason')
        )
        db.add(inventory)
        loaded_count += 1
        
        # Batch commit every 1000 records
        if loaded_count % 1000 == 0:
            db.commit()
    
    db.commit()
    print(f"✅ Loaded {loaded_count} inventory records")
    return loaded_count


def load_competitor_pricing_from_csv(db: Session, csv_path: str) -> int:
    """Load competitor pricing from CSV file into database."""
    print("🏪 Loading competitor pricing...")
    
    df = pd.read_csv(csv_path)
    df['last_updated'] = pd.to_datetime(df['last_updated'])
    
    loaded_count = 0
    for _, row in df.iterrows():
        pricing = CompetitorPrice(
            product_id=row['product_id'],
            sku=row['sku'],
            competitor=row['competitor'],
            competitor_price=row['competitor_price'],
            price_difference_percent=row['price_difference_percent'],
            in_stock=row['in_stock'],
            last_updated=row['last_updated']
        )
        db.add(pricing)
        loaded_count += 1
    
    db.commit()
    print(f"✅ Loaded {loaded_count} competitor pricing records")
    return loaded_count


def create_sample_forecasts(db: Session) -> int:
    """Create sample forecast records for demo purposes."""
    print("🔮 Creating sample forecasts...")
    
    # Get some products to forecast
    products = db.query(Product).limit(10).all()
    
    forecast_count = 0
    for product in products:
        # Create 30-day forecast for each product
        for days_ahead in range(1, 31):
            forecast_date = datetime.utcnow() + timedelta(days=days_ahead)
            
            # Simple forecast logic (in real implementation, use ML models)
            base_demand = 5.0  # Base daily demand
            predicted_demand = base_demand * (1 + 0.1 * (days_ahead % 7))  # Weekly pattern
            confidence = 0.85 + 0.1 * (1 - days_ahead / 30)  # Confidence decreases over time
            
            from backend.app.database import Forecast
            forecast = Forecast(
                product_id=product.id,
                sku=product.sku,
                forecast_date=datetime.utcnow(),
                target_date=forecast_date,
                forecast_type='demand',
                predicted_value=predicted_demand,
                confidence_lower=predicted_demand * 0.8,
                confidence_upper=predicted_demand * 1.2,
                confidence_level=0.95,
                model_version='demo_v1.0',
                model_accuracy=confidence
            )
            db.add(forecast)
            forecast_count += 1
    
    db.commit()
    print(f"✅ Created {forecast_count} sample forecasts")
    return forecast_count


def create_sample_alerts(db: Session) -> int:
    """Create sample inventory alerts for demo purposes."""
    print("🚨 Creating sample alerts...")
    
    # Get products with low stock
    from backend.app.database import InventoryRecord, InventoryAlert
    
    low_stock_products = db.query(InventoryRecord).filter(
        InventoryRecord.stock_level_after < 10,
        InventoryRecord.transaction_type == 'daily_snapshot'
    ).limit(5).all()
    
    alert_count = 0
    for record in low_stock_products:
        alert = InventoryAlert(
            product_id=record.product_id,
            sku=record.sku,
            alert_type='stockout_risk',
            severity='high' if record.stock_level_after < 5 else 'medium',
            current_stock=record.stock_level_after,
            optimal_stock=record.optimal_stock_level or 50,
            days_of_supply=record.days_of_supply or 0,
            recommended_action='Reorder immediately',
            recommended_quantity=50,
            urgency_score=0.8,
            estimated_stockout_date=datetime.utcnow() + timedelta(days=3),
            financial_impact=record.stock_level_after * 100,  # Estimated lost revenue
            alert_message=f'Product {record.sku} has low stock: {record.stock_level_after} units remaining'
        )
        db.add(alert)
        alert_count += 1
    
    db.commit()
    print(f"✅ Created {alert_count} sample alerts")
    return alert_count


def main():
    """Main database initialization function."""
    print("🚀 Initializing SmartShelf AI database...")
    
    # Create database directory if it doesn't exist
    db_dir = Path("data/database")
    db_dir.mkdir(parents=True, exist_ok=True)
    
    # Create database tables
    print("📋 Creating database tables...")
    create_tables()
    
    # Start database session
    db = SessionLocal()
    
    try:
        # Load data from CSV files
        data_dir = Path("data/raw")
        
        if (data_dir / "products.csv").exists():
            load_products_from_csv(db, data_dir / "products.csv")
        
        if (data_dir / "sales.csv").exists():
            load_sales_from_csv(db, data_dir / "sales.csv")
        
        if (data_dir / "inventory.csv").exists():
            load_inventory_from_csv(db, data_dir / "inventory.csv")
        
        if (data_dir / "competitor_pricing.csv").exists():
            load_competitor_pricing_from_csv(db, data_dir / "competitor_pricing.csv")
        
        # Create sample data for demo
        create_sample_forecasts(db)
        create_sample_alerts(db)
        
        # Print database statistics
        print("\n📊 Database Statistics:")
        stats = get_database_stats()
        for key, value in stats.items():
            if isinstance(value, float):
                print(f"   {key}: ${value:,.2f}" if 'revenue' in key else f"   {key}: {value:.2f}")
            else:
                print(f"   {key}: {value}")
        
        print("\n🎉 Database initialization complete!")
        
    except Exception as e:
        print(f"❌ Error during database initialization: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
