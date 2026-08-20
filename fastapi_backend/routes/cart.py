"""
routes/cart.py
-----------------
GET    /cart          - view your own cart, with server-computed totals
POST   /cart/add       - add a product to your cart (or increase quantity if already present)
PUT    /cart/update    - change the quantity of an existing cart line
DELETE /cart/remove/{item_id} - remove a line from your cart

All endpoints require authentication (any role), and every query is scoped
to current_user.id — a customer can only ever see or modify their OWN cart,
never another user's, regardless of role. This is the User -> CartItem ->
Product relationship: each CartItem row belongs to exactly one user and
points at exactly one product (see models/cart.py).

Cart calculations (GET /cart, and returned again by add/update so the
frontend never has to compute money itself):
  item_total  = unit_price * quantity, per line
  subtotal    = sum of all item_totals
  tax         = subtotal * settings.TAX_RATE  (0 if TAX_RATE is 0)
  grand_total = subtotal + tax
"""

from decimal import Decimal
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from core.config import settings
from core.database import get_db
from core.pricing import compute_totals, money
from core.security import get_current_user
from models.cart import CartItem
from models.product import Product
from models.user import User
from schemas.cart import CartItemAdd, CartItemOut, CartItemUpdate, CartOut

router = APIRouter(prefix="/cart", tags=["Cart"])


def _build_cart_response(current_user: User, db: Session) -> CartOut:
    rows: List[CartItem] = (
        db.query(CartItem)
        .options(joinedload(CartItem.product))
        .filter(CartItem.user_id == current_user.id)
        .all()
    )

    line_items: List[CartItemOut] = []
    subtotal = Decimal("0")
    total_items = 0

    for row in rows:
        item_total = money(row.product.price * row.quantity)
        subtotal += item_total
        total_items += row.quantity
        line_items.append(
            CartItemOut(
                id=row.id,
                product_id=row.product_id,
                product_name=row.product.name,
                unit_price=row.product.price,
                quantity=row.quantity,
                item_total=item_total,
            )
        )

    tax, grand_total = compute_totals(subtotal)

    return CartOut(
        items=line_items,
        total_items=total_items,
        subtotal=subtotal,
        tax_rate=settings.TAX_RATE,
        tax=tax,
        grand_total=grand_total,
    )


@router.get("", response_model=CartOut)
def view_cart(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return _build_cart_response(current_user, db)


@router.post("/add", response_model=CartOut, status_code=status.HTTP_201_CREATED)
def add_to_cart(payload: CartItemAdd, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == payload.product_id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    existing = (
        db.query(CartItem)
        .filter(CartItem.user_id == current_user.id, CartItem.product_id == payload.product_id)
        .first()
    )
    if existing:
        existing.quantity += payload.quantity
    else:
        db.add(CartItem(user_id=current_user.id, product_id=payload.product_id, quantity=payload.quantity))

    # Popularity is a simple "how often has this been added to a cart"
    # counter, used by GET /products?sort=popularity.
    product.popularity += 1

    db.commit()
    return _build_cart_response(current_user, db)


@router.put("/update", response_model=CartOut)
def update_cart_item(payload: CartItemUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    item = (
        db.query(CartItem)
        .filter(CartItem.id == payload.item_id, CartItem.user_id == current_user.id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart item not found")

    item.quantity = payload.quantity
    db.commit()
    return _build_cart_response(current_user, db)


@router.delete("/remove/{item_id}", response_model=CartOut)
def remove_from_cart(item_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    item = db.query(CartItem).filter(CartItem.id == item_id, CartItem.user_id == current_user.id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart item not found")
    db.delete(item)
    db.commit()
    return _build_cart_response(current_user, db)
