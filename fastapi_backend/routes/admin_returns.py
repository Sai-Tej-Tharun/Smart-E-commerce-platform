"""
routes/admin_returns.py
---------------------------
GET  /admin/returns                - every return request, newest first
                                      (optionally ?status=pending/approved/rejected)
POST /admin/returns/{id}/approve   - approve a request: restock the
                                      returned items, refund the payment
                                      via Stripe, notify the customer
POST /admin/returns/{id}/reject    - reject a request: order goes back to
                                      DELIVERED, notify the customer

All three are admin-only (require_role("admin")) — this is the
"Admin APIs" half of the return lifecycle; routes/orders.py's
POST /orders/{id}/return is the customer-facing half.

Status handling, exactly per the spec:
  Approved  -> ReturnRequest.status = APPROVED, Order.order_status = RETURNED
  Rejected  -> ReturnRequest.status = REJECTED, Order.order_status = DELIVERED (reverted)
  Refund completed -> Payment.status = REFUNDED, Order.payment_status = REFUNDED

Deliberate design choice: approving and refunding happen in the SAME
request (one POST /admin/returns/{id}/approve call), not two separate
steps. The spec lists "Approved -> Returned" and "Refund completed ->
Refunded" as distinct status transitions, but doesn't ask for a separate
endpoint to trigger the refund — so approving a return immediately
attempts the Stripe refund. If the Stripe call fails, NOTHING is
committed (see the try/except below) — the request stays PENDING so an
admin can simply retry, rather than leaving stock/notifications out of
sync with a refund that never actually happened.
"""

from typing import List, Optional

import stripe
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

import core.stripe_client  # noqa: F401  # side effect: sets stripe.api_key
from core.database import get_db
from core.notify import notify_user
from core.permissions import require_role
from models.notification import NotificationType
from models.order import Order, OrderStatus, PaymentStatus
from models.payment import Payment, PaymentTransactionStatus
from models.product import Product
from models.return_request import ReturnRequest, ReturnRequestStatus
from models.user import User
from schemas.return_request import RefundResultOut, ReturnRequestAdminOut, ReturnRequestOut

router = APIRouter(prefix="/admin/returns", tags=["Admin - Returns"])


@router.get("", response_model=List[ReturnRequestAdminOut], dependencies=[Depends(require_role("admin"))])
def list_return_requests(status_filter: Optional[str] = None, db: Session = Depends(get_db)):
    query = (
        db.query(ReturnRequest)
        .options(joinedload(ReturnRequest.order), joinedload(ReturnRequest.user))
        .order_by(ReturnRequest.created_at.desc())
    )
    if status_filter:
        try:
            query = query.filter(ReturnRequest.status == ReturnRequestStatus(status_filter.lower()))
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid status '{status_filter}'")

    results = []
    for rr in query.all():
        results.append(
            ReturnRequestAdminOut(
                id=rr.id,
                order_id=rr.order_id,
                reason=rr.reason,
                comment=rr.comment,
                status=rr.status.value,
                created_at=rr.created_at,
                user_id=rr.user_id,
                user_email=rr.user.email,
                order_status=rr.order.order_status.value,
                order_total=rr.order.total,
            )
        )
    return results


@router.post("/{return_id}/approve", response_model=RefundResultOut)
async def approve_return(
    return_id: int,
    admin_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    rr = db.query(ReturnRequest).filter(ReturnRequest.id == return_id).first()
    if not rr:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Return request not found")
    if rr.status != ReturnRequestStatus.PENDING:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"This request is already '{rr.status.value}'")

    order = db.query(Order).options(joinedload(Order.items), joinedload(Order.payment)).filter(Order.id == rr.order_id).first()
    if not order or not order.payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order or payment record not found")

    payment: Payment = order.payment
    if not payment.transaction_id or payment.status != PaymentTransactionStatus.SUCCEEDED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This order's payment was never confirmed as succeeded — nothing to refund",
        )

    # ---- Payment Refund (Stripe) — attempted BEFORE anything else is
    # committed, so a Stripe failure leaves the database exactly as it
    # was (request still PENDING, stock untouched) rather than half-applied. ----
    try:
        refund = stripe.Refund.create(payment_intent=payment.transaction_id)
    except stripe.error.StripeError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Stripe refund failed: {exc.user_message or str(exc)}")

    # ---- Status handling, per the spec ----
    rr.status = ReturnRequestStatus.APPROVED
    order.order_status = OrderStatus.RETURNED
    payment.status = PaymentTransactionStatus.REFUNDED
    order.payment_status = PaymentStatus.REFUNDED

    # ---- Inventory Management: restock every item on the order ----
    for item in order.items:
        if item.product_id:
            product = db.query(Product).filter(Product.id == item.product_id).first()
            if product:
                product.stock += item.quantity

    db.commit()

    # ---- Notifications: both events fire from this one approval, since
    # this endpoint approves AND refunds in the same call (see module docstring) ----
    await notify_user(db, rr.user, NotificationType.RETURN_APPROVED, order_id=order.id, total=str(order.total))
    await notify_user(db, rr.user, NotificationType.REFUND_COMPLETED, order_id=order.id, total=str(payment.amount))

    db.refresh(rr)
    return RefundResultOut(
        return_request=ReturnRequestOut.model_validate(rr),
        order_status=order.order_status.value,
        payment_status=order.payment_status.value,
        stripe_refund_id=refund.id,
    )


@router.post("/{return_id}/reject", response_model=ReturnRequestOut)
async def reject_return(
    return_id: int,
    admin_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    rr = db.query(ReturnRequest).options(joinedload(ReturnRequest.user)).filter(ReturnRequest.id == return_id).first()
    if not rr:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Return request not found")
    if rr.status != ReturnRequestStatus.PENDING:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"This request is already '{rr.status.value}'")

    order = db.query(Order).filter(Order.id == rr.order_id).first()

    rr.status = ReturnRequestStatus.REJECTED
    if order:
        # Reverted, not cancelled — the order itself is unaffected; only
        # the return attempt was denied.
        order.order_status = OrderStatus.DELIVERED
    db.commit()

    await notify_user(db, rr.user, NotificationType.RETURN_REJECTED, order_id=rr.order_id)

    db.refresh(rr)
    return rr