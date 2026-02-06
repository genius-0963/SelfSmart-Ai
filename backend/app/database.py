"""
SmartShelf AI - Database Configuration

SQLite database setup with SQLAlchemy for hackathon deployment.
Includes optimized indexing for retail analytics queries.
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func
from datetime import datetime, timedelta
import os

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/database/smartshelf.db")

# Create database engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    echo=False  # Set to True for SQL debugging
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all models
Base = declarative_base()


# Dependency to get database session
def get_db():
    """Get database session for FastAPI dependency injection."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """Create all database tables."""
    Base.metadata.create_all(bind=engine)


def drop_tables():
    """Drop all database tables (for testing)."""
    Base.metadata.drop_all(bind=engine)


# Database Models

class Product(Base):
    """Product catalog table."""
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String(50), unique=True, index=True, nullable=False)
    product_name = Column(String(200), nullable=False)
    category = Column(String(100), index=True, nullable=False)
    brand = Column(String(100), index=True)
    base_price = Column(Float, nullable=False)
    cost_price = Column(Float, nullable=False)
    weight_kg = Column(Float)
    dimensions_cm = Column(String(50))
    supplier = Column(String(100), index=True)
    status = Column(String(20), default="active", index=True)
    created_date = Column(DateTime, default=datetime.utcnow)
    updated_date = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    sales = relationship("Sale", back_populates="product")
    inventory_records = relationship("InventoryRecord", back_populates="product")
    forecasts = relationship("Forecast", back_populates="product")
    competitor_prices = relationship("CompetitorPrice", back_populates="product")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_product_category_status', 'category', 'status'),
        Index('idx_product_supplier_brand', 'supplier', 'brand'),
    )


class Sale(Base):
    """Sales transactions table."""
    __tablename__ = "sales"
    
    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(String(50), unique=True, index=True, nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    sku = Column(String(50), index=True, nullable=False)
    date = Column(DateTime, index=True, nullable=False)
    hour = Column(Integer, index=True)  # Hour of day (0-23)
    quantity_sold = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    total_revenue = Column(Float, nullable=False)
    promotion_active = Column(Boolean, default=False, index=True)
    promotion_discount = Column(Float, default=0.0)
    created_date = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    product = relationship("Product", back_populates="sales")
    
    # Performance indexes
    __table_args__ = (
        Index('idx_sale_date_product', 'date', 'product_id'),
        Index('idx_sale_date_category', 'date', 'sku'),  # Will join with products
        Index('idx_sale_promotion_date', 'promotion_active', 'date'),
        Index('idx_sale_revenue_date', 'total_revenue', 'date'),
    )


class InventoryRecord(Base):
    """Inventory movements and levels table."""
    __tablename__ = "inventory"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    sku = Column(String(50), index=True, nullable=False)
    date = Column(DateTime, index=True, nullable=False)
    transaction_type = Column(String(50), index=True, nullable=False)  # 'sale', 'restock', 'adjustment', 'stockout'
    quantity_change = Column(Integer, nullable=False)  # Negative for sales, positive for restock
    stock_level_after = Column(Integer, nullable=False)
    optimal_stock_level = Column(Integer)
    days_of_supply = Column(Float)  # Current stock / average daily sales
    inventory_value = Column(Float)  # Stock level * cost price
    supplier = Column(String(100))
    cost_per_unit = Column(Float)
    lost_sales = Column(Integer, default=0)  # For stockouts
    stockout_reason = Column(String(100))
    created_date = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    product = relationship("Product", back_populates="inventory_records")
    
    # Performance indexes
    __table_args__ = (
        Index('idx_inventory_date_product', 'date', 'product_id'),
        Index('idx_inventory_type_date', 'transaction_type', 'date'),
        Index('idx_inventory_stock_level', 'stock_level_after', 'date'),
        Index('idx_inventory_days_supply', 'days_of_supply'),
    )


class Forecast(Base):
    """ML forecasting results table."""
    __tablename__ = "forecasts"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    sku = Column(String(50), index=True, nullable=False)
    forecast_date = Column(DateTime, index=True, nullable=False)  # Date being forecasted
    target_date = Column(DateTime, index=True, nullable=False)  # Date forecast is for
    forecast_type = Column(String(50), index=True, nullable=False)  # 'demand', 'revenue', 'price'
    predicted_value = Column(Float, nullable=False)
    confidence_lower = Column(Float)  # Lower bound of confidence interval
    confidence_upper = Column(Float)  # Upper bound of confidence interval
    confidence_level = Column(Float, default=0.95)  # Confidence interval level
    model_version = Column(String(50), index=True)
    model_accuracy = Column(Float)  # Historical accuracy metric
    features_used = Column(Text)  # JSON string of features
    created_date = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    product = relationship("Product", back_populates="forecasts")
    
    # Performance indexes
    __table_args__ = (
        Index('idx_forecast_product_target', 'product_id', 'target_date'),
        Index('idx_forecast_type_date', 'forecast_type', 'target_date'),
        Index('idx_forecast_model_version', 'model_version', 'created_date'),
    )


class CompetitorPrice(Base):
    """Competitor pricing data table."""
    __tablename__ = "competitor_prices"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    sku = Column(String(50), index=True, nullable=False)
    competitor = Column(String(100), index=True, nullable=False)
    competitor_price = Column(Float, nullable=False)
    price_difference_percent = Column(Float, index=True)
    in_stock = Column(Boolean, default=True, index=True)
    last_updated = Column(DateTime, index=True, default=datetime.utcnow)
    created_date = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    product = relationship("Product", back_populates="competitor_prices")
    
    # Performance indexes
    __table_args__ = (
        Index('idx_competitor_product', 'product_id', 'competitor'),
        Index('idx_competitor_price_diff', 'price_difference_percent'),
        Index('idx_competitor_updated', 'last_updated'),
    )


class PricingOptimization(Base):
    """Pricing optimization recommendations table."""
    __tablename__ = "pricing_optimizations"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    sku = Column(String(50), index=True, nullable=False)
    current_price = Column(Float, nullable=False)
    recommended_price = Column(Float, nullable=False)
    price_change_percent = Column(Float, index=True)
    expected_demand_change = Column(Float)  # Percentage change in demand
    expected_revenue_impact = Column(Float)  # Expected change in daily revenue
    optimization_type = Column(String(50), index=True)  # 'increase', 'decrease', 'maintain'
    confidence_score = Column(Float, index=True)  # Confidence in recommendation (0-1)
    elasticity_used = Column(Float)  # Price elasticity value used
    competitor_consideration = Column(Text)  # JSON of competitor data used
    recommendation_reason = Column(Text)  # Explanation of recommendation
    valid_until = Column(DateTime, index=True)
    implemented = Column(Boolean, default=False, index=True)
    created_date = Column(DateTime, default=datetime.utcnow)
    
    # Performance indexes
    __table_args__ = (
        Index('idx_pricing_product_valid', 'product_id', 'valid_until'),
        Index('idx_pricing_confidence', 'confidence_score', 'optimization_type'),
        Index('idx_pricing_implemented', 'implemented', 'created_date'),
    )


class InventoryAlert(Base):
    """Inventory alerts and notifications table."""
    __tablename__ = "inventory_alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    sku = Column(String(50), index=True, nullable=False)
    alert_type = Column(String(50), index=True, nullable=False)  # 'stockout_risk', 'overstock', 'reorder'
    severity = Column(String(20), index=True, nullable=False)  # 'low', 'medium', 'high', 'critical'
    current_stock = Column(Integer, nullable=False)
    optimal_stock = Column(Integer)
    days_of_supply = Column(Float)
    recommended_action = Column(String(200))
    recommended_quantity = Column(Integer)
    urgency_score = Column(Float, index=True)  # 0-1 urgency score
    estimated_stockout_date = Column(DateTime, index=True)
    financial_impact = Column(Float)  # Potential revenue loss or cost
    alert_message = Column(Text)
    acknowledged = Column(Boolean, default=False, index=True)
    resolved = Column(Boolean, default=False, index=True)
    created_date = Column(DateTime, default=datetime.utcnow, index=True)
    resolved_date = Column(DateTime)
    
    # Performance indexes
    __table_args__ = (
        Index('idx_alert_type_severity', 'alert_type', 'severity'),
        Index('idx_alert_urgency', 'urgency_score', 'created_date'),
        Index('idx_alert_unresolved', 'resolved', 'created_date'),
    )


class ChatSession(Base):
    """AI Copilot chat sessions table."""
    __tablename__ = "chat_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), unique=True, index=True, nullable=False)
    user_id = Column(String(100), index=True)  # For future multi-user support
    created_date = Column(DateTime, default=datetime.utcnow, index=True)
    last_activity = Column(DateTime, default=datetime.utcnow, index=True)
    session_metadata = Column(Text)  # JSON of session context
    is_active = Column(Boolean, default=True, index=True)


class ChatMessage(Base):
    """AI Copilot chat messages table."""
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), ForeignKey("chat_sessions.session_id"), index=True, nullable=False)
    message_type = Column(String(20), index=True, nullable=False)  # 'user', 'assistant', 'system'
    message_content = Column(Text, nullable=False)
    message_data = Column(Text)  # JSON of structured data, charts, etc.
    context_used = Column(Text)  # JSON of retrieved context documents
    model_used = Column(String(50))
    tokens_used = Column(Integer)
    response_time_ms = Column(Integer)
    user_feedback = Column(Integer)  # 1-5 rating
    created_date = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Performance indexes
    __table_args__ = (
        Index('idx_message_session_time', 'session_id', 'created_date'),
        Index('idx_message_type_time', 'message_type', 'created_date'),
    )


class SystemMetrics(Base):
    """System performance and usage metrics table."""
    __tablename__ = "system_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    metric_name = Column(String(100), index=True, nullable=False)
    metric_value = Column(Float, nullable=False)
    metric_unit = Column(String(20))
    metric_category = Column(String(50), index=True)  # 'ml', 'api', 'copilot', 'system'
    tags = Column(Text)  # JSON of additional tags
    recorded_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Performance indexes
    __table_args__ = (
        Index('idx_metrics_name_time', 'metric_name', 'recorded_at'),
        Index('idx_metrics_category_time', 'metric_category', 'recorded_at'),
    )


# Database utility functions

def get_database_stats():
    """Get basic database statistics for monitoring."""
    db = SessionLocal()
    try:
        stats = {
            'products': db.query(Product).count(),
            'sales': db.query(Sale).count(),
            'inventory_records': db.query(InventoryRecord).count(),
            'forecasts': db.query(Forecast).count(),
            'alerts': db.query(InventoryAlert).filter(InventoryAlert.resolved == False).count(),
            'chat_sessions': db.query(ChatSession).filter(ChatSession.is_active == True).count(),
            'total_revenue': db.query(func.sum(Sale.total_revenue)).scalar() or 0,
            'last_sale_date': db.query(func.max(Sale.date)).scalar(),
            'database_size_mb': os.path.getsize(DATABASE_URL.replace('sqlite:///', '')) / (1024 * 1024) if 'sqlite' in DATABASE_URL else 0
        }
        return stats
    finally:
        db.close()


def cleanup_old_data(days_to_keep=90):
    """Clean up old data to manage database size."""
    db = SessionLocal()
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        # Clean up old chat messages
        deleted_messages = db.query(ChatMessage).filter(
            ChatMessage.created_date < cutoff_date
        ).delete()
        
        # Clean up old system metrics
        deleted_metrics = db.query(SystemMetrics).filter(
            SystemMetrics.recorded_at < cutoff_date
        ).delete()
        
        # Clean up resolved alerts older than cutoff
        deleted_alerts = db.query(InventoryAlert).filter(
            InventoryAlert.resolved == True,
            InventoryAlert.resolved_date < cutoff_date
        ).delete()
        
        db.commit()
        
        return {
            'deleted_messages': deleted_messages,
            'deleted_metrics': deleted_metrics,
            'deleted_alerts': deleted_alerts
        }
    finally:
        db.close()


if __name__ == "__main__":
    # Create database tables
    create_tables()
    print("✅ Database tables created successfully!")
    
    # Print database stats
    stats = get_database_stats()
    print(f"\n📊 Database Statistics:")
    for key, value in stats.items():
        print(f"   {key}: {value}")
