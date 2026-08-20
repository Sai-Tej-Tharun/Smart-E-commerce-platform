"""
routes/products.py
---------------------
GET  /products                     - public, browse the catalog with filters
GET  /products/{id}                - public, single product
GET  /products/category/{category} - public, shortcut for ?category=<category>
POST /products                     - admin only
PUT  /products/{id}                - admin only
DELETE /products/{id}              - admin only

Demonstrates role-based access control: browsing is open, but managing the
catalog is restricted to the 'admin' role via require_role("admin").

Filtering (GET /products query params, all optional and combinable):
  category=<str>        exact match, case-insensitive
  min_price=<number>     inclusive
  max_price=<number>     inclusive
  in_stock=<true|false>  true = stock > 0, false = stock == 0
  sort=<popularity|price_asc|price_desc|newest>   defaults to newest
"""

from decimal import Decimal
from enum import Enum
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from core.database import get_db
from core.permissions import require_role
from models.product import Product
from schemas.product import ProductCreate, ProductOut

router = APIRouter(prefix="/products", tags=["Products"])


class SortOption(str, Enum):
    popularity = "popularity"
    price_asc = "price_asc"
    price_desc = "price_desc"
    newest = "newest"


def _apply_filters(
    query,
    category: Optional[str],
    min_price: Optional[Decimal],
    max_price: Optional[Decimal],
    in_stock: Optional[bool],
    sort: SortOption,
):
    if category:
        query = query.filter(func.lower(Product.category) == category.lower())
    if min_price is not None:
        query = query.filter(Product.price >= min_price)
    if max_price is not None:
        query = query.filter(Product.price <= max_price)
    if in_stock is True:
        query = query.filter(Product.stock > 0)
    elif in_stock is False:
        query = query.filter(Product.stock == 0)

    if sort == SortOption.popularity:
        query = query.order_by(Product.popularity.desc())
    elif sort == SortOption.price_asc:
        query = query.order_by(Product.price.asc())
    elif sort == SortOption.price_desc:
        query = query.order_by(Product.price.desc())
    else:
        query = query.order_by(Product.created_at.desc())

    return query


@router.get("", response_model=List[ProductOut])
def list_products(
    category: Optional[str] = Query(None, description="Exact category match, case-insensitive"),
    min_price: Optional[Decimal] = Query(None, ge=0),
    max_price: Optional[Decimal] = Query(None, ge=0),
    in_stock: Optional[bool] = Query(None, description="true = in stock, false = out of stock"),
    sort: SortOption = Query(SortOption.newest),
    db: Session = Depends(get_db),
):
    query = _apply_filters(db.query(Product), category, min_price, max_price, in_stock, sort)
    return query.all()


@router.get("/category/{category}", response_model=List[ProductOut])
def list_products_by_category(
    category: str,
    min_price: Optional[Decimal] = Query(None, ge=0),
    max_price: Optional[Decimal] = Query(None, ge=0),
    in_stock: Optional[bool] = Query(None),
    sort: SortOption = Query(SortOption.newest),
    db: Session = Depends(get_db),
):
    # Same filtering/sorting as GET /products, just with category as a path
    # segment instead of a query param — a friendlier URL for category pages.
    query = _apply_filters(db.query(Product), category, min_price, max_price, in_stock, sort)
    return query.all()


@router.get("/{product_id}", response_model=ProductOut)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return product


@router.post("", response_model=ProductOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_role("admin"))])
def create_product(payload: ProductCreate, db: Session = Depends(get_db)):
    product = Product(**payload.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@router.put("/{product_id}", response_model=ProductOut, dependencies=[Depends(require_role("admin"))])
def update_product(product_id: int, payload: ProductCreate, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    for field, value in payload.model_dump().items():
        setattr(product, field, value)
    db.commit()
    db.refresh(product)
    return product


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_role("admin"))])
def delete_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    db.delete(product)
    db.commit()
