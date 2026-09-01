"""
routes/checkout.py
---------------------
POST /checkout           - turn the current user's cart into an Order + a
                            Stripe Checkout Session, ready to pay
POST /webhooks/stripe    - Stripe calls this when a session's payment
                            succeeds (or fails/expires); this is what
                            actually marks the order paid, decrements
                            stock, and empties the cart — never the
                            /checkout call itself, since the browser
                            redirect to Stripe happens *after* /checkout
                            returns and the user might abandon it there.

Checkout flow, step by step (mirrors the milestone's spec exactly):
  1. Validate cart items       -> cart must be non-empty; every product
                                   must still have enough stock
  2. Calculate total price     -> core/pricing.py, same logic GET /cart uses
  3. Create order record       -> Order (status=pending) + OrderItem
                                   snapshots of each cart line
  4. Initialize Stripe session -> stripe.checkout.Session.create(...) —
                                   creating a Checkout Session in "payment"
                                   mode also creates an underlying Stripe
                                   PaymentIntent for it automatically, so
                                   this one call satisfies both "Payment
                                   Intent" and "Checkout Session" from the
                                   spec without two separate payment flows.

Design choice, stated plainly: stock is checked (not decremented) and the
cart is left untouched at checkout time. Both only change once Stripe
confirms payment via the webhook below. This avoids the harder problem of
reserving/releasing stock for abandoned checkouts, at the cost of not
protecting against two customers checking out the last unit at the same
moment — an acceptable simplification for this milestone's scope.
"""

from decimal import Decimal
from typing import List

import stripe
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session, joinedload

import core.stripe_client  # noqa: F401  # side effect: sets stripe.api_key
from core.config import settings
from core.database import get_db
from core.notify import notify_user
from core.pricing import compute_totals, money
from core.realtime import broadcast_cart_updated
from core.security import get_current_user
from models.cart import CartItem
from models.notification import NotificationType
from models.order import Order, OrderItem, OrderStatus, PaymentStatus
from models.payment import Payment, PaymentTransactionStatus
from models.product import Product
from models.user import User
from schemas.checkout import CheckoutResponse
from schemas.order import OrderOut
from schemas.cart import CartOut

router = APIRouter(tags=["Checkout & Payments"])


@router.post("/checkout", response_model=CheckoutResponse, status_code=status.HTTP_201_CREATED)
def checkout(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # ---- Step 1: validate cart items ----
    cart_rows: List[CartItem] = (
        db.query(CartItem)
        .options(joinedload(CartItem.product))
        .filter(CartItem.user_id == current_user.id)
        .all()
    )
    if not cart_rows:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Your cart is empty")

    for row in cart_rows:
        if row.quantity > row.product.stock:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Only {row.product.stock} of '{row.product.name}' left in stock (you have {row.quantity} in your cart)",
            )

    # ---- Step 2: calculate total price ----
    subtotal = Decimal("0")
    line_items_data = []
    for row in cart_rows:
        line_total = money(row.product.price * row.quantity)
        subtotal += line_total
        line_items_data.append(
            {
                "product_id": row.product_id,
                "product_name": row.product.name,
                "unit_price": row.product.price,
                "quantity": row.quantity,
                "line_total": line_total,
            }
        )
    tax, grand_total = compute_totals(subtotal)

    # ---- Step 3: create order record ----
    order = Order(
        user_id=current_user.id,
        subtotal=subtotal,
        tax=tax,
        total=grand_total,
        order_status=OrderStatus.PENDING,
        payment_status=PaymentStatus.PENDING,
    )
    db.add(order)
    db.flush()  # assigns order.id without committing yet

    for item in line_items_data:
        db.add(OrderItem(order_id=order.id, **item))

    # ---- Step 4: initialize Stripe payment session ----
    if not settings.STRIPE_SECRET_KEY:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Stripe is not configured on the server (STRIPE_SECRET_KEY is empty in .env)",
        )

    try:
        session = stripe.checkout.Session.create(
            mode="payment",
            payment_method_types=["card"],
            line_items=[
                {
                    "price_data": {
                        "currency": settings.CURRENCY,
                        "product_data": {"name": item["product_name"]},
                        # Stripe wants the smallest currency unit (paise/cents), hence *100
                        "unit_amount": int(item["unit_price"] * 100),
                    },
                    "quantity": item["quantity"],
                }
                for item in line_items_data
            ],
            customer_email=current_user.email,
            success_url=f"{settings.FRONTEND_URL}/checkout/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{settings.FRONTEND_URL}/checkout/cancel?order_id={order.id}",
            metadata={"order_id": str(order.id), "user_id": str(current_user.id)},
        )
    except stripe.error.StripeError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Stripe error: {exc.user_message or str(exc)}")

    # ---- Payment record (tracks the Stripe side; see models/payment.py) ----
    db.add(
        Payment(
            order_id=order.id,
            amount=grand_total,
            payment_method="stripe",
            transaction_id=session.id,  # replaced with the PaymentIntent id once the webhook fires
            status=PaymentTransactionStatus.PENDING,
        )
    )

    db.commit()
    db.refresh(order)

    return CheckoutResponse(order=OrderOut.model_validate(order), checkout_url=session.url, session_id=session.id)


@router.post("/webhooks/stripe", include_in_schema=False)
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Stripe POSTs here on payment events. Not documented in Swagger
    (include_in_schema=False) since it's not something a human calls —
    only Stripe's servers do, authenticated by the signature below rather
    than a JWT.

    Local testing: run `stripe listen --forward-to localhost:8000/webhooks/stripe`
    (see the Screenshot Guide) — the Stripe CLI prints a `whsec_...` value
    to put in STRIPE_WEBHOOK_SECRET.
    """
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, settings.STRIPE_WEBHOOK_SECRET)
    except (ValueError, stripe.error.SignatureVerificationError):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Stripe webhook signature")

    event_type = event["type"]
    session_obj = event["data"]["object"]

    if event_type == "checkout.session.completed":
        await _mark_order_paid(db, session_obj)
    elif event_type in ("checkout.session.expired", "payment_intent.payment_failed"):
        await _mark_order_failed(db, session_obj)

    return {"received": True}


async def _mark_order_paid(db: Session, session_obj) -> None:
    print("========== MARK ORDER PAID ==========")
    print("Session ID:", session_obj.id)
    print("Metadata:", session_obj.metadata)
    print("Payment Intent:", session_obj.payment_intent)

    metadata = session_obj.metadata.to_dict()
    order_id = metadata.get("order_id")

    payment = (
        db.query(Payment)
        .filter(Payment.transaction_id == session_obj.id)
        .first()
    )

    order = (
        db.query(Order)
        .filter(Order.id == int(order_id))
        .first()
        if order_id
        else None
    )
    print("Payment found:", payment)
    print("Order found:", order)

    if not order or not payment:
        return

    order.order_status = OrderStatus.PAID
    order.payment_status = PaymentStatus.PAID
    payment.status = PaymentTransactionStatus.SUCCEEDED

    payment.transaction_id = (
        session_obj.payment_intent or payment.transaction_id
    )

    for item in order.items:
        if item.product_id:
            product = (
                db.query(Product)
                .filter(Product.id == item.product_id)
                .first()
            )
            if product:
                product.stock = max(0, product.stock - item.quantity)

    db.query(CartItem).filter(
        CartItem.user_id == order.user_id
    ).delete()

    db.commit()

    print("Payment/order updated successfully")

  

    user = db.query(User).filter(
        User.id == order.user_id
    ).first()

    print("Starting notifications...")

    if user:
        await notify_user(
            db,
            user,
            NotificationType.ORDER_CONFIRMED,
            order_id=order.id,
            total=str(order.total),
        )

        await notify_user(
            db,
            user,
            NotificationType.PAYMENT_SUCCESSFUL,
            order_id=order.id,
            total=str(order.total),
        )

        empty_cart = CartOut(
            items=[],
            total_items=0,
            subtotal=Decimal("0"),
            tax_rate=settings.TAX_RATE,
            tax=Decimal("0"),
            grand_total=Decimal("0"),
        )

        await broadcast_cart_updated(
            order.user_id,
            empty_cart,
        )


async def _mark_order_failed(db: Session, session_obj: dict) -> None:
    payment = db.query(Payment).filter(Payment.transaction_id == session_obj["id"]).first()
    if not payment:
        return
    order = db.query(Order).filter(Order.id == payment.order_id).first()
    payment.status = PaymentTransactionStatus.FAILED
    if order:
        order.payment_status = PaymentStatus.FAILED
    db.commit()

    if order:
        user = db.query(User).filter(User.id == order.user_id).first()
        if user:
            await notify_user(db, user, NotificationType.PAYMENT_FAILED, order_id=order.id, total=str(order.total))