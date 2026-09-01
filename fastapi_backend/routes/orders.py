"""
routes/orders.py
--------------------
GET /orders                    - the current user's order history
GET /orders/{id}                - one order, scoped to its owner (same pattern as cart:
                                    a customer can never view another user's order)
POST /orders/{id}/return        - NEW (Refund & Return milestone): request a
                                    return on a delivered order, within the
                                    return window (settings.RETURN_WINDOW_DAYS)

Admins manage order_status (shipped/delivered/cancelled) from the Django
admin panel, not here — see django_admin/storefront/admin.py. The two GET
endpoints are read-only and customer-facing; POST /orders/{id}/return is
the one write action a customer can take against their own order.
"""

from datetime import datetime, timedelta
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from core.config import settings
from core.database import get_db
from core.security import get_current_user
from models.order import Order, OrderStatus
from models.return_request import ReturnRequest, ReturnRequestStatus
from models.user import User
from schemas.order import OrderOut
from schemas.return_request import ReturnRequestCreate, ReturnRequestOut

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


@router.post("/{order_id}/return", response_model=ReturnRequestOut, status_code=status.HTTP_201_CREATED)
def request_return(
    order_id: int,
    payload: ReturnRequestCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    order = db.query(Order).filter(Order.id == order_id, Order.user_id == current_user.id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    if order.order_status != OrderStatus.DELIVERED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only delivered orders can be returned (this order is '{order.order_status.value}')",
        )

    # delivered_at is set by django_admin the moment an admin marks an
    # order Delivered (see django_admin/storefront/signals.py). Orders
    # delivered before that column existed won't have it — fall back to
    # updated_at as a best-effort approximation for those, rather than
    # blocking a legitimate return outright.
    delivered_reference = order.delivered_at or order.updated_at
    if delivered_reference:
        # MySQL's DATETIME column has no timezone concept, so SQLAlchemy
        # reads these back as naive datetimes even though the column is
        # declared DateTime(timezone=True) — comparing a naive value
        # against an aware datetime.now(timezone.utc) raises a TypeError.
        # (Caught by an actual test run, not by inspection — see the
        # equivalent note in the report.) Normalize to naive UTC on both
        # sides so the comparison works regardless of what the DB driver
        # happens to hand back.
        if delivered_reference.tzinfo is not None:
            delivered_reference = delivered_reference.replace(tzinfo=None)
        deadline = delivered_reference + timedelta(days=settings.RETURN_WINDOW_DAYS)
        if datetime.utcnow() > deadline:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"The {settings.RETURN_WINDOW_DAYS}-day return window for this order has expired",
            )

    existing = (
        db.query(ReturnRequest)
        .filter(
            ReturnRequest.order_id == order.id,
            ReturnRequest.status.in_([ReturnRequestStatus.PENDING, ReturnRequestStatus.APPROVED]),
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A return request already exists for this order")

    return_request = ReturnRequest(
        order_id=order.id,
        user_id=current_user.id,
        reason=payload.reason,
        comment=payload.comment,
    )
    db.add(return_request)

    # "When requested -> status = 'Return Requested'" — per the spec.
    order.order_status = OrderStatus.RETURN_REQUESTED

    db.commit()
    db.refresh(return_request)
    return return_request