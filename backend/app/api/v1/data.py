"""
SmartShelf AI - Data Management API v1

Endpoints for data upload, validation, and management.
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import pandas as pd
import io
import logging
from datetime import datetime

from ...database import get_db
from ...database import Product, Sale, InventoryRecord, CompetitorPrice
from ...models.product import (
    ProductCreate, ProductUpdate, ProductResponse, ProductListResponse,
    ProductSearchRequest, BulkProductCreate, BulkProductResponse
)
from ...models.sales import (
    SaleCreate, SaleResponse, SalesSearchRequest, BulkSaleCreate, BulkSaleResponse
)
from ...core.exceptions import ValidationError, DatabaseError, DataProcessingError

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/upload", response_model=Dict[str, Any])
async def upload_data(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    data_type: str = "sales",
    db: Session = Depends(get_db)
):
    """
    Upload and process data from CSV file.
    
    Args:
        file: CSV file to upload
        data_type: Type of data ('sales', 'products', 'inventory', 'competitor_pricing')
        db: Database session
        
    Returns:
        Upload status and processing information
    """
    # Validate file type
    if not file.filename.endswith('.csv'):
        raise ValidationError("Only CSV files are supported")
    
    # Validate data type
    valid_types = ['sales', 'products', 'inventory', 'competitor_pricing']
    if data_type not in valid_types:
        raise ValidationError(f"Invalid data type. Must be one of: {valid_types}")
    
    try:
        # Read CSV file
        contents = await file.read()
        df = pd.read_csv(io.StringIO(contents.decode('utf-8')))
        
        # Basic validation
        if df.empty:
            raise ValidationError("CSV file is empty")
        
        # Add processing task to background
        task_id = f"upload_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
        background_tasks.add_task(
            process_uploaded_data,
            task_id=task_id,
            df=df,
            data_type=data_type,
            db=db
        )
        
        return {
            "message": "File uploaded successfully",
            "task_id": task_id,
            "filename": file.filename,
            "data_type": data_type,
            "rows_uploaded": len(df),
            "columns": list(df.columns),
            "status": "processing"
        }
        
    except pd.errors.EmptyDataError:
        raise ValidationError("CSV file is empty or malformed")
    except pd.errors.ParserError:
        raise ValidationError("Invalid CSV format")
    except Exception as e:
        logger.error(f"Data upload failed: {e}")
        raise DataProcessingError(f"Failed to process uploaded file: {str(e)}")


async def process_uploaded_data(
    task_id: str,
    df: pd.DataFrame,
    data_type: str,
    db: Session
):
    """Process uploaded data in background."""
    logger.info(f"Processing task {task_id} for {data_type} data")
    
    try:
        if data_type == "products":
            await process_products_data(df, db)
        elif data_type == "sales":
            await process_sales_data(df, db)
        elif data_type == "inventory":
            await process_inventory_data(df, db)
        elif data_type == "competitor_pricing":
            await process_competitor_data(df, db)
        
        logger.info(f"Completed processing task {task_id}")
        
    except Exception as e:
        logger.error(f"Failed to process task {task_id}: {e}")
        raise


async def process_products_data(df: pd.DataFrame, db: Session):
    """Process products data."""
    required_columns = ['sku', 'product_name', 'category', 'base_price', 'cost_price']
    missing_columns = set(required_columns) - set(df.columns)
    
    if missing_columns:
        raise ValidationError(f"Missing required columns: {missing_columns}")
    
    created_count = 0
    for _, row in df.iterrows():
        # Check if product already exists
        existing = db.query(Product).filter(Product.sku == row['sku']).first()
        if existing:
            continue
        
        product = Product(
            sku=row['sku'],
            product_name=row['product_name'],
            category=row['category'],
            brand=row.get('brand'),
            base_price=row['base_price'],
            cost_price=row['cost_price'],
            weight_kg=row.get('weight_kg'),
            dimensions_cm=row.get('dimensions_cm'),
            supplier=row.get('supplier'),
            status=row.get('status', 'active')
        )
        db.add(product)
        created_count += 1
    
    db.commit()
    logger.info(f"Created {created_count} new products")


async def process_sales_data(df: pd.DataFrame, db: Session):
    """Process sales data."""
    required_columns = ['product_id', 'date', 'quantity_sold', 'unit_price']
    missing_columns = set(required_columns) - set(df.columns)
    
    if missing_columns:
        raise ValidationError(f"Missing required columns: {missing_columns}")
    
    # Convert date column
    df['date'] = pd.to_datetime(df['date'])
    
    created_count = 0
    for _, row in df.iterrows():
        sale = Sale(
            transaction_id=row.get('transaction_id', f"SALE_{datetime.now().strftime('%Y%m%d%H%M%S')}_{created_count}"),
            product_id=row['product_id'],
            sku=row.get('sku', ''),
            date=row['date'],
            hour=row.get('hour', row['date'].hour),
            quantity_sold=row['quantity_sold'],
            unit_price=row['unit_price'],
            total_revenue=row['quantity_sold'] * row['unit_price'],
            promotion_active=row.get('promotion_active', False),
            promotion_discount=row.get('promotion_discount', 0.0)
        )
        db.add(sale)
        created_count += 1
        
        # Batch commit every 1000 records
        if created_count % 1000 == 0:
            db.commit()
    
    db.commit()
    logger.info(f"Created {created_count} sales records")


async def process_inventory_data(df: pd.DataFrame, db: Session):
    """Process inventory data."""
    required_columns = ['product_id', 'date', 'transaction_type', 'quantity_change', 'stock_level_after']
    missing_columns = set(required_columns) - set(df.columns)
    
    if missing_columns:
        raise ValidationError(f"Missing required columns: {missing_columns}")
    
    # Convert date column
    df['date'] = pd.to_datetime(df['date'])
    
    created_count = 0
    for _, row in df.iterrows():
        inventory = InventoryRecord(
            product_id=row['product_id'],
            sku=row.get('sku', ''),
            date=row['date'],
            transaction_type=row['transaction_type'],
            quantity_change=row['quantity_change'],
            stock_level_after=row['stock_level_after'],
            optimal_stock_level=row.get('optimal_stock_level'),
            days_of_supply=row.get('days_of_supply'),
            inventory_value=row.get('inventory_value'),
            supplier=row.get('supplier'),
            cost_per_unit=row.get('cost_per_unit')
        )
        db.add(inventory)
        created_count += 1
        
        # Batch commit every 1000 records
        if created_count % 1000 == 0:
            db.commit()
    
    db.commit()
    logger.info(f"Created {created_count} inventory records")


async def process_competitor_data(df: pd.DataFrame, db: Session):
    """Process competitor pricing data."""
    required_columns = ['product_id', 'competitor', 'competitor_price']
    missing_columns = set(required_columns) - set(df.columns)
    
    if missing_columns:
        raise ValidationError(f"Missing required columns: {missing_columns}")
    
    created_count = 0
    for _, row in df.iterrows():
        pricing = CompetitorPrice(
            product_id=row['product_id'],
            sku=row.get('sku', ''),
            competitor=row['competitor'],
            competitor_price=row['competitor_price'],
            price_difference_percent=row.get('price_difference_percent', 0.0),
            in_stock=row.get('in_stock', True),
            last_updated=pd.to_datetime(row.get('last_updated', datetime.now()))
        )
        db.add(pricing)
        created_count += 1
    
    db.commit()
    logger.info(f"Created {created_count} competitor pricing records")


# Product endpoints
@router.post("/products", response_model=ProductResponse)
async def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    """Create a new product."""
    # Check if SKU already exists
    existing = db.query(Product).filter(Product.sku == product.sku).first()
    if existing:
        raise ValidationError(f"Product with SKU '{product.sku}' already exists")
    
    db_product = Product(**product.dict())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    
    return ProductResponse.from_orm(db_product)


@router.get("/products", response_model=ProductListResponse)
async def get_products(
    search: ProductSearchRequest = Depends(),
    db: Session = Depends(get_db)
):
    """Get products with search and pagination."""
    query = db.query(Product)
    
    # Apply filters
    if search.sku:
        query = query.filter(Product.sku.ilike(f"%{search.sku}%"))
    if search.category:
        query = query.filter(Product.category == search.category)
    if search.brand:
        query = query.filter(Product.brand.ilike(f"%{search.brand}%"))
    if search.supplier:
        query = query.filter(Product.supplier.ilike(f"%{search.supplier}%"))
    if search.status:
        query = query.filter(Product.status == search.status)
    if search.min_price:
        query = query.filter(Product.base_price >= search.min_price)
    if search.max_price:
        query = query.filter(Product.base_price <= search.max_price)
    
    # Apply sorting
    if search.sort_by == "base_price":
        order_column = Product.base_price
    elif search.sort_by == "created_date":
        order_column = Product.created_date
    else:
        order_column = Product.id
    
    if search.sort_order == "desc":
        query = query.order_by(order_column.desc())
    else:
        query = query.order_by(order_column.asc())
    
    # Count total
    total = query.count()
    
    # Apply pagination
    offset = (search.page - 1) * search.per_page
    products = query.offset(offset).limit(search.per_page).all()
    
    return ProductListResponse(
        products=[ProductResponse.from_orm(p) for p in products],
        total=total,
        page=search.page,
        per_page=search.per_page,
        total_pages=(total + search.per_page - 1) // search.per_page
    )


@router.get("/products/{product_id}", response_model=ProductResponse)
async def get_product(product_id: int, db: Session = Depends(get_db)):
    """Get a specific product by ID."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise NotFoundError("Product", product_id)
    
    return ProductResponse.from_orm(product)


@router.put("/products/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: int,
    product_update: ProductUpdate,
    db: Session = Depends(get_db)
):
    """Update a product."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise NotFoundError("Product", product_id)
    
    # Update fields
    update_data = product_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(product, field, value)
    
    product.updated_date = datetime.utcnow()
    db.commit()
    db.refresh(product)
    
    return ProductResponse.from_orm(product)


@router.delete("/products/{product_id}")
async def delete_product(product_id: int, db: Session = Depends(get_db)):
    """Delete a product."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise NotFoundError("Product", product_id)
    
    db.delete(product)
    db.commit()
    
    return {"message": f"Product {product_id} deleted successfully"}


@router.post("/products/bulk", response_model=BulkProductResponse)
async def create_products_bulk(
    bulk_data: BulkProductCreate,
    db: Session = Depends(get_db)
):
    """Create multiple products in bulk."""
    success_count = 0
    failed_count = 0
    errors = []
    created_products = []
    
    for i, product_data in enumerate(bulk_data.products):
        try:
            # Check if SKU already exists
            existing = db.query(Product).filter(Product.sku == product_data.sku).first()
            if existing:
                errors.append({
                    "index": i,
                    "sku": product_data.sku,
                    "error": "Product with this SKU already exists"
                })
                failed_count += 1
                continue
            
            db_product = Product(**product_data.dict())
            db.add(db_product)
            created_products.append(db_product)
            success_count += 1
            
        except Exception as e:
            errors.append({
                "index": i,
                "sku": product_data.sku,
                "error": str(e)
            })
            failed_count += 1
    
    # Commit all successful creations
    if created_products:
        db.commit()
        # Refresh to get IDs
        for product in created_products:
            db.refresh(product)
    
    return BulkProductResponse(
        success_count=success_count,
        failed_count=failed_count,
        total_count=len(bulk_data.products),
        errors=errors,
        created_products=[ProductResponse.from_orm(p) for p in created_products]
    )


# Sales endpoints
@router.post("/sales", response_model=SaleResponse)
async def create_sale(sale: SaleCreate, db: Session = Depends(get_db)):
    """Create a new sale record."""
    db_sale = Sale(**sale.dict())
    db.add(db_sale)
    db.commit()
    db.refresh(db_sale)
    
    return SaleResponse.from_orm(db_sale)


@router.get("/sales", response_model=List[SaleResponse])
async def get_sales(
    search: SalesSearchRequest = Depends(),
    db: Session = Depends(get_db)
):
    """Get sales records with search and pagination."""
    query = db.query(Sale)
    
    # Apply filters
    if search.product_id:
        query = query.filter(Sale.product_id == search.product_id)
    if search.sku:
        query = query.filter(Sale.sku.ilike(f"%{search.sku}%"))
    if search.start_date:
        query = query.filter(Sale.date >= search.start_date)
    if search.end_date:
        query = query.filter(Sale.date <= search.end_date)
    if search.promotion_active is not None:
        query = query.filter(Sale.promotion_active == search.promotion_active)
    if search.min_quantity:
        query = query.filter(Sale.quantity_sold >= search.min_quantity)
    if search.max_quantity:
        query = query.filter(Sale.quantity_sold <= search.max_quantity)
    if search.min_revenue:
        query = query.filter(Sale.total_revenue >= search.min_revenue)
    if search.max_revenue:
        query = query.filter(Sale.total_revenue <= search.max_revenue)
    
    # Apply sorting
    if search.sort_by == "date":
        order_column = Sale.date
    elif search.sort_by == "total_revenue":
        order_column = Sale.total_revenue
    else:
        order_column = Sale.id
    
    if search.sort_order == "desc":
        query = query.order_by(order_column.desc())
    else:
        query = query.order_by(order_column.asc())
    
    # Apply pagination
    offset = (search.page - 1) * search.per_page
    sales = query.offset(offset).limit(search.per_page).all()
    
    return [SaleResponse.from_orm(s) for s in sales]


@router.post("/sales/bulk", response_model=BulkSaleResponse)
async def create_sales_bulk(
    bulk_data: BulkSaleCreate,
    db: Session = Depends(get_db)
):
    """Create multiple sales records in bulk."""
    success_count = 0
    failed_count = 0
    errors = []
    created_sales = []
    
    for i, sale_data in enumerate(bulk_data.sales):
        try:
            db_sale = Sale(**sale_data.dict())
            db.add(db_sale)
            created_sales.append(db_sale)
            success_count += 1
            
            # Batch commit every 1000 records
            if success_count % 1000 == 0:
                db.commit()
                
        except Exception as e:
            errors.append({
                "index": i,
                "transaction_id": sale_data.transaction_id,
                "error": str(e)
            })
            failed_count += 1
    
    # Final commit
    db.commit()
    
    # Refresh to get IDs
    for sale in created_sales:
        db.refresh(sale)
    
    return BulkSaleResponse(
        success_count=success_count,
        failed_count=failed_count,
        total_count=len(bulk_data.sales),
        errors=errors,
        created_sales=[SaleResponse.from_orm(s) for s in created_sales]
    )


@router.get("/stats", response_model=Dict[str, Any])
async def get_data_stats(db: Session = Depends(get_db)):
    """Get data statistics and summary."""
    from ...database import get_database_stats
    
    try:
        stats = get_database_stats()
        return stats
    except Exception as e:
        logger.error(f"Failed to get database stats: {e}")
        raise DatabaseError("Failed to retrieve database statistics")


# Import NotFoundError from exceptions
from ...core.exceptions import NotFoundError
