#!/usr/bin/env python3
"""
SmartShelf AI - Synthetic Retail Data Generator

Generates realistic retail data for hackathon demo including:
- Daily sales with seasonal patterns
- Product catalog with categories
- Inventory levels and movements
- Price elasticity and promotional effects
- 6 months of historical data

Usage:
    python generate_data.py --months 6 --products 100 --output_dir data/raw/
"""

import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import argparse
import os
from pathlib import Path


class RetailDataGenerator:
    """Generate realistic synthetic retail data for ML model training and demo."""
    
    def __init__(self, random_seed: int = 42):
        """Initialize generator with random seed for reproducibility."""
        np.random.seed(random_seed)
        
        # Retail business parameters
        self.product_categories = [
            'Electronics', 'Clothing', 'Food & Beverages', 'Home & Garden',
            'Sports & Outdoors', 'Books & Media', 'Health & Beauty', 'Toys & Games'
        ]
        
        self.seasonal_patterns = {
            'Electronics': [0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.3, 1.2, 1.1, 1.5, 1.8],  # Holiday spike
            'Clothing': [0.7, 0.8, 1.0, 1.2, 1.3, 1.4, 1.2, 1.1, 1.3, 1.4, 1.6, 1.8],     # Seasonal changes
            'Food & Beverages': [1.0, 1.0, 1.0, 1.0, 1.1, 1.2, 1.3, 1.2, 1.1, 1.0, 1.2, 1.4], # Summer/holiday
            'Home & Garden': [0.6, 0.7, 0.9, 1.2, 1.5, 1.8, 1.6, 1.4, 1.2, 1.0, 0.8, 0.7], # Spring/summer peak
            'Sports & Outdoors': [0.8, 0.9, 1.1, 1.3, 1.6, 1.8, 1.7, 1.5, 1.3, 1.1, 0.9, 0.8], # Outdoor season
            'Books & Media': [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.2, 1.1, 1.0, 1.0, 1.3, 1.5],  # Back to school/holiday
            'Health & Beauty': [0.9, 0.9, 1.0, 1.0, 1.1, 1.1, 1.1, 1.0, 1.0, 1.0, 1.1, 1.2], # Stable with holiday bump
            'Toys & Games': [0.8, 0.8, 0.9, 1.0, 1.0, 1.1, 1.2, 1.1, 1.0, 1.1, 1.5, 2.0]  # Massive holiday spike
        }
        
        # Price elasticity by category (negative = demand decreases when price increases)
        self.price_elasticity = {
            'Electronics': -1.5,
            'Clothing': -1.2,
            'Food & Beverages': -0.8,
            'Home & Garden': -1.0,
            'Sports & Outdoors': -1.3,
            'Books & Media': -1.8,
            'Health & Beauty': -0.9,
            'Toys & Games': -1.4
        }
        
        # Base inventory parameters
        self.inventory_turnover = {
            'Electronics': 4,      # Turns per year
            'Clothing': 6,
            'Food & Beverages': 12,
            'Home & Garden': 3,
            'Sports & Outdoors': 5,
            'Books & Media': 8,
            'Health & Beauty': 10,
            'Toys & Games': 4
        }

    def generate_products(self, num_products: int) -> pd.DataFrame:
        """Generate product catalog with realistic attributes."""
        
        products = []
        
        for i in range(1, num_products + 1):
            category = np.random.choice(self.product_categories)
            
            # Generate product name
            brand_names = ['TechPro', 'StyleCo', 'FreshMart', 'HomeBase', 'SportMax', 
                          'BookWorld', 'HealthPlus', 'PlayFun']
            brand = np.random.choice(brand_names)
            
            product_types = {
                'Electronics': ['Phone', 'Laptop', 'Tablet', 'Headphones', 'Speaker'],
                'Clothing': ['Shirt', 'Pants', 'Dress', 'Jacket', 'Shoes'],
                'Food & Beverages': ['Snack', 'Drink', 'Fresh Food', 'Frozen Food', 'Bakery'],
                'Home & Garden': ['Furniture', 'Decor', 'Tool', 'Plant', 'Kitchen'],
                'Sports & Outdoors': ['Equipment', 'Apparel', 'Footwear', 'Accessory', 'Gear'],
                'Books & Media': ['Book', 'Movie', 'Music', 'Game', 'Magazine'],
                'Health & Beauty': ['Skincare', 'Makeup', 'Supplement', 'Personal Care', 'Fragrance'],
                'Toys & Games': ['Action Figure', 'Board Game', 'Puzzle', 'Electronic Toy', 'Educational']
            }
            
            product_type = np.random.choice(product_types[category])
            product_name = f"{brand} {product_type} {i:03d}"
            
            # Generate SKU
            sku = f"{category[:3].upper()}{i:05d}"
            
            # Price based on category
            base_prices = {
                'Electronics': np.random.uniform(50, 500),
                'Clothing': np.random.uniform(20, 150),
                'Food & Beverages': np.random.uniform(2, 25),
                'Home & Garden': np.random.uniform(30, 300),
                'Sports & Outdoors': np.random.uniform(25, 200),
                'Books & Media': np.random.uniform(10, 50),
                'Health & Beauty': np.random.uniform(15, 80),
                'Toys & Games': np.random.uniform(15, 100)
            }
            
            base_price = base_prices[category]
            cost_price = base_price * np.random.uniform(0.4, 0.7)  # 40-70% of selling price
            
            # Product dimensions and weight
            weight = np.random.uniform(0.1, 10.0)  # kg
            dimensions = f"{np.random.uniform(10, 50):.1f}x{np.random.uniform(10, 50):.1f}x{np.random.uniform(5, 30):.1f}"
            
            # Supplier information
            suppliers = ['Global Supplies Inc', 'Quality Goods Co', 'FastShip Logistics', 
                        'Premium Products Ltd', 'ValueMart Distributors']
            supplier = np.random.choice(suppliers)
            
            # Product status
            status = np.random.choice(['active', 'active', 'active', 'discontinued'], p=[0.85, 0.1, 0.03, 0.02])
            
            products.append({
                'product_id': i,
                'sku': sku,
                'product_name': product_name,
                'category': category,
                'brand': brand,
                'base_price': round(base_price, 2),
                'cost_price': round(cost_price, 2),
                'weight_kg': round(weight, 2),
                'dimensions_cm': dimensions,
                'supplier': supplier,
                'status': status,
                'created_date': datetime.now() - timedelta(days=np.random.randint(30, 365))
            })
        
        return pd.DataFrame(products)

    def generate_sales_data(self, products: pd.DataFrame, months: int) -> pd.DataFrame:
        """Generate daily sales data with seasonal patterns and trends."""
        
        sales_records = []
        start_date = datetime.now() - timedelta(days=months * 30)
        
        # Add overall trend (growing business)
        trend_factor = np.linspace(1.0, 1.2, months * 30)  # 20% growth over period
        
        for day_offset in range(months * 30):
            current_date = start_date + timedelta(days=day_offset)
            
            # Day of week patterns (weekends higher for some categories)
            day_of_week = current_date.weekday()
            weekend_boost = 1.3 if day_of_week >= 5 else 1.0
            
            # Monthly seasonal pattern
            month = current_date.month - 1  # 0-indexed for array access
            
            # Random events (promotions, stockouts, etc.)
            if np.random.random() < 0.05:  # 5% chance of promotion
                promotion_active = True
                promotion_discount = np.random.uniform(0.1, 0.3)  # 10-30% discount
            else:
                promotion_active = False
                promotion_discount = 0
            
            # Generate sales for random subset of products each day
            daily_products = products.sample(frac=np.random.uniform(0.3, 0.8))
            
            for _, product in daily_products.iterrows():
                # Base demand calculation
                category = product['category']
                base_demand = np.random.exponential(scale=2.0)  # Random base demand
                
                # Apply seasonal pattern
                seasonal_multiplier = self.seasonal_patterns[category][month]
                
                # Apply trend
                trend_multiplier = trend_factor[day_offset]
                
                # Apply weekend boost
                weekend_multiplier = weekend_boost if category in ['Clothing', 'Sports & Outdoors', 'Toys & Games'] else 1.0
                
                # Apply promotion effect
                if promotion_active:
                    promotion_multiplier = 1 + (promotion_discount * abs(self.price_elasticity[category]))
                    actual_price = product['base_price'] * (1 - promotion_discount)
                else:
                    promotion_multiplier = 1.0
                    actual_price = product['base_price']
                
                # Add some random noise
                noise_factor = np.random.normal(1.0, 0.1)
                
                # Calculate final demand
                daily_demand = max(0, int(base_demand * seasonal_multiplier * trend_multiplier * 
                                         weekend_multiplier * promotion_multiplier * noise_factor))
                
                if daily_demand > 0:
                    # Generate sales transactions throughout the day
                    for _ in range(min(daily_demand, 50)):  # Cap at 50 transactions per product per day
                        transaction_hour = np.random.choice(range(9, 21), p=[0.05, 0.05, 0.08, 0.1, 0.12, 0.15, 0.18, 0.12, 0.08, 0.05, 0.02, 0.0])
                        
                        quantity = np.random.choice([1, 1, 1, 2, 3, 4], p=[0.6, 0.2, 0.1, 0.05, 0.03, 0.02])
                        
                        sales_records.append({
                            'date': current_date.date(),
                            'product_id': product['product_id'],
                            'sku': product['sku'],
                            'quantity_sold': quantity,
                            'unit_price': round(actual_price, 2),
                            'total_revenue': round(actual_price * quantity, 2),
                            'hour': transaction_hour,
                            'promotion_active': promotion_active,
                            'promotion_discount': promotion_discount if promotion_active else 0,
                            'transaction_id': f"TXN{day_offset:05d}{len(sales_records):04d}"
                        })
        
        return pd.DataFrame(sales_records)

    def generate_inventory_data(self, products: pd.DataFrame, sales_data: pd.DataFrame) -> pd.DataFrame:
        """Generate inventory levels and movements based on sales data."""
        
        inventory_records = []
        
        # Get date range
        min_date = sales_data['date'].min()
        max_date = sales_data['date'].max()
        
        for _, product in products.iterrows():
            product_id = product['product_id']
            
            # Initial inventory level (based on category turnover)
            annual_turnover = self.inventory_turnover[product['category']]
            avg_daily_sales = sales_data[sales_data['product_id'] == product_id]['quantity_sold'].mean() if product_id in sales_data['product_id'].values else 1
            optimal_stock = int(avg_daily_sales * (365 / annual_turnover))
            
            # Start with some initial inventory
            current_stock = optimal_stock + np.random.randint(-20, 50)
            current_stock = max(current_stock, 10)  # Minimum stock
            
            # Generate daily inventory records
            current_date = min_date
            
            while current_date <= max_date:
                # Sales for this day
                day_sales = sales_data[(sales_data['product_id'] == product_id) & 
                                     (sales_data['date'] == current_date)]
                units_sold = day_sales['quantity_sold'].sum() if not day_sales.empty else 0
                
                # Stock arrivals (replenishment)
                if current_stock < optimal_stock * 0.3:  # Reorder when below 30%
                    replenishment = optimal_stock * np.random.uniform(0.8, 1.2)
                    current_stock += int(replenishment)
                    
                    inventory_records.append({
                        'date': current_date,
                        'product_id': product_id,
                        'sku': product['sku'],
                        'transaction_type': 'restock',
                        'quantity_change': int(replenishment),
                        'stock_level_after': current_stock,
                        'supplier': product['supplier'],
                        'cost_per_unit': product['cost_price']
                    })
                
                # Record stockout if occurred
                if units_sold > current_stock:
                    units_sold = current_stock  # Can't sell more than available
                    inventory_records.append({
                        'date': current_date,
                        'product_id': product_id,
                        'sku': product['sku'],
                        'transaction_type': 'stockout',
                        'quantity_change': 0,
                        'stock_level_after': 0,
                        'lost_sales': day_sales['quantity_sold'].sum() - current_stock if not day_sales.empty else 0,
                        'stockout_reason': 'insufficient_inventory'
                    })
                    current_stock = 0
                else:
                    current_stock -= units_sold
                
                # Daily inventory snapshot
                inventory_records.append({
                    'date': current_date,
                    'product_id': product_id,
                    'sku': product['sku'],
                    'transaction_type': 'daily_snapshot',
                    'quantity_change': -units_sold,
                    'stock_level_after': current_stock,
                    'optimal_stock_level': optimal_stock,
                    'days_of_supply': current_stock / max(avg_daily_sales, 1),
                    'inventory_value': current_stock * product['cost_price']
                })
                
                current_date += timedelta(days=1)
        
        return pd.DataFrame(inventory_records)

    def generate_competitor_pricing(self, products: pd.DataFrame) -> pd.DataFrame:
        """Generate competitor pricing data for pricing optimization."""
        
        competitor_data = []
        competitors = ['CompetitorA', 'CompetitorB', 'CompetitorC']
        
        for _, product in products.iterrows():
            for competitor in competitors:
                # Competitor pricing strategy (some cheaper, some premium)
                price_multiplier = np.random.choice([0.85, 0.9, 0.95, 1.0, 1.05, 1.1], 
                                                  p=[0.1, 0.2, 0.3, 0.2, 0.15, 0.05])
                
                competitor_price = product['base_price'] * price_multiplier
                
                # Stock availability (competitors might be out of stock)
                in_stock = np.random.choice([True, True, True, False], p=[0.8, 0.1, 0.05, 0.05])
                
                competitor_data.append({
                    'product_id': product['product_id'],
                    'sku': product['sku'],
                    'competitor': competitor,
                    'competitor_price': round(competitor_price, 2),
                    'price_difference_percent': round((competitor_price - product['base_price']) / product['base_price'] * 100, 2),
                    'in_stock': in_stock,
                    'last_updated': datetime.now() - timedelta(hours=np.random.randint(1, 72))
                })
        
        return pd.DataFrame(competitor_data)

    def save_data(self, products: pd.DataFrame, sales: pd.DataFrame, 
                  inventory: pd.DataFrame, competitor_pricing: pd.DataFrame, 
                  output_dir: str):
        """Save all generated datasets to files."""
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Save as CSV for easy loading
        products.to_csv(output_path / 'products.csv', index=False)
        sales.to_csv(output_path / 'sales.csv', index=False)
        inventory.to_csv(output_path / 'inventory.csv', index=False)
        competitor_pricing.to_csv(output_path / 'competitor_pricing.csv', index=False)
        
        # Save data schema documentation
        schema = {
            'products': {
                'columns': list(products.columns),
                'description': 'Product catalog with attributes and pricing',
                'record_count': len(products),
                'date_range': 'N/A'
            },
            'sales': {
                'columns': list(sales.columns),
                'description': 'Daily sales transactions with timestamps and promotions',
                'record_count': len(sales),
                'date_range': f"{sales['date'].min()} to {sales['date'].max()}"
            },
            'inventory': {
                'columns': list(inventory.columns),
                'description': 'Inventory movements, stock levels, and replenishment',
                'record_count': len(inventory),
                'date_range': f"{inventory['date'].min()} to {inventory['date'].max()}"
            },
            'competitor_pricing': {
                'columns': list(competitor_pricing.columns),
                'description': 'Competitor pricing and availability data',
                'record_count': len(competitor_pricing),
                'date_range': 'N/A'
            }
        }
        
        with open(output_path / 'data_schema.json', 'w') as f:
            json.dump(schema, f, indent=2, default=str)
        
        # Generate summary statistics
        summary = {
            'generation_timestamp': datetime.now().isoformat(),
            'data_summary': {
                'total_products': len(products),
                'total_sales_transactions': len(sales),
                'total_revenue': float(sales['total_revenue'].sum()),
                'unique_skus': products['sku'].nunique(),
                'categories': products['category'].unique().tolist(),
                'date_range_days': (sales['date'].max() - sales['date'].min()).days,
                'avg_daily_revenue': float(sales.groupby('date')['total_revenue'].sum().mean()),
                'top_products_by_revenue': sales.groupby('product_id')['total_revenue'].sum().nlargest(5).to_dict()
            }
        }
        
        with open(output_path / 'data_summary.json', 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        print(f"✅ Data generated successfully!")
        print(f"📁 Output directory: {output_path}")
        print(f"📊 Products: {len(products)}")
        print(f"💰 Sales transactions: {len(sales):,}")
        print(f"📦 Inventory records: {len(inventory):,}")
        print(f"🏪 Competitor data points: {len(competitor_pricing):,}")
        print(f"💵 Total revenue: ${sales['total_revenue'].sum():,.2f}")


def main():
    """Main function to run the data generator."""
    
    parser = argparse.ArgumentParser(description='Generate synthetic retail data for SmartShelf AI')
    parser.add_argument('--months', type=int, default=6, help='Number of months of data to generate')
    parser.add_argument('--products', type=int, default=100, help='Number of products to generate')
    parser.add_argument('--output_dir', type=str, default='data/raw', help='Output directory for generated data')
    parser.add_argument('--seed', type=int, default=42, help='Random seed for reproducibility')
    
    args = parser.parse_args()
    
    print("🚀 Starting SmartShelf AI data generator...")
    print(f"📅 Generating {args.months} months of data")
    print(f"📦 Creating {args.products} products")
    
    # Initialize generator
    generator = RetailDataGenerator(random_seed=args.seed)
    
    # Generate datasets
    print("\n📋 Generating product catalog...")
    products = generator.generate_products(args.products)
    
    print("💰 Generating sales data...")
    sales = generator.generate_sales_data(products, args.months)
    
    print("📦 Generating inventory data...")
    inventory = generator.generate_inventory_data(products, sales)
    
    print("🏪 Generating competitor pricing...")
    competitor_pricing = generator.generate_competitor_pricing(products)
    
    # Save all data
    generator.save_data(products, sales, inventory, competitor_pricing, args.output_dir)
    
    print("\n🎉 Data generation complete!")


if __name__ == "__main__":
    main()
