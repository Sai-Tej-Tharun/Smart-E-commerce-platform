"""
routes/orders.py
--------------------
GET /orders       - the current user's order history
GET /orders/{id}  - one order, scoped to its owner (same pattern as cart:
                    a customer can never view another user's order)

Admins manage order_status (shipped/delivered/cancelled) from the Django
admin panel, not here — see django_admin/storefront/admin.py. These two
endpoints are read-only and customer-facing.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from core.database import get_db
from core.security import get_current_user
from models.order import Order
from models.user import User
from schemas.order import OrderOut

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.get("", response_model=List[OrderOut])
def list_my_orders(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return (
        db.query(Order)
        .options(joinedload(Order.items), joinedload(Order.payment))
        .filter(Order.user_id == current_user.id)
        .order_by(Order.created_at.desc())
        .all()
    )


@router.get("/{order_id}", response_model=OrderOut)
def get_order(order_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    order = (
        db.query(Order)
        .options(joinedload(Order.items), joinedload(Order.payment))
        .filter(Order.id == order_id, Order.user_id == current_user.id)
        .first()
    )
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return order
