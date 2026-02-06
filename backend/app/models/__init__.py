"""
SmartShelf AI - Pydantic Models

API request/response models for data validation and serialization.
"""

from .product import *
from .sales import *
from .forecast import *
from .inventory import *
from .copilot import *

__all__ = [
    # Product models
    'Product', 'ProductCreate', 'ProductUpdate', 'ProductResponse',
    
    # Sales models
    'Sale', 'SaleCreate', 'SaleResponse', 'SalesAnalytics',
    
    # Forecast models
    'Forecast', 'ForecastRequest', 'ForecastResponse', 'ForecastMetrics',
    
    # Inventory models
    'InventoryRecord', 'InventoryAlert', 'InventoryAlertResponse', 'InventoryStats',
    
    # Copilot models
    'ChatMessage', 'ChatRequest', 'ChatResponse', 'ChatSession',
]
