"""
routes/reviews.py
--------------------
POST /reviews                    - submit a review (starts as PENDING;
                                    only visible publicly once approved)
GET  /products/{id}/reviews      - a product's APPROVED reviews, plus the
                                    Rating Aggregation (average + total)

Validation, per the spec:
  - Only users with a completed order for this product can review
  - One review per user per product

"Completed order" is defined here as any order that reached DELIVERED at
some point — including RETURN_REQUESTED and RETURNED, since the customer
still received the item; only PENDING/PAID/SHIPPED (not yet in the
customer's hands) and CANCELLED are excluded. See _ELIGIBLE_ORDER_STATUSES
below — change that one tuple if a stricter definition is wanted.

Moderation (pending -> approved/rejected) happens directly in the Django
admin, not through an API here — see django_admin/storefront/admin.py's
ReviewAdmin. Unlike return requests, approving a review has no refund or
inventory side effects, so a plain editable status field is enough; no
dedicated approve/reject endpoints were built for this milestone.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from core.database import get_db
from core.security import get_current_user
from models.order import Order, OrderItem, OrderStatus
from models.review import Review, ReviewStatus
from models.user import User
from schemas.review import ProductReviewsOut, ReviewCreate, ReviewOut

router = APIRouter(tags=["Reviews"])

_ELIGIBLE_ORDER_STATUSES = (OrderStatus.DELIVERED, OrderStatus.RETURN_REQUESTED, OrderStatus.RETURNED)


@router.post("/reviews", response_model=ReviewOut, status_code=status.HTTP_201_CREATED)
def create_review(
    payload: ReviewCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # ---- Validation 1: only users with a completed order for this product ----
    has_completed_order = (
        db.query(OrderItem)
        .join(Order, Order.id == OrderItem.order_id)
        .filter(
            Order.user_id == current_user.id,
            OrderItem.product_id == payload.product_id,
            Order.order_status.in_(_ELIGIBLE_ORDER_STATUSES),
        )
        .first()
        is not None
    )
    if not has_completed_order:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only review products from a completed order",
        )

    # ---- Validation 2: one review per user per product ----
    existing = (
        db.query(Review)
        .filter(Review.user_id == current_user.id, Review.product_id == payload.product_id)
        .first()
    )
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You've already reviewed this product")

    review = Review(
        user_id=current_user.id,
        product_id=payload.product_id,
        rating=payload.rating,
        comment=payload.comment,
        status=ReviewStatus.PENDING,
    )
    db.add(review)
    db.commit()
    db.refresh(review)

    out = ReviewOut.model_validate(review)
    out.user_name = current_user.name
    return out


@router.get("/products/{product_id}/reviews", response_model=ProductReviewsOut)
def get_product_reviews(
    product_id: int,
    sort: str = Query("top", pattern="^(top|newest)$", description="'top' = highest rated first, 'newest' = most recent first"),
    db: Session = Depends(get_db),
):
    query = (
        db.query(Review)
        .options(joinedload(Review.user))
        .filter(Review.product_id == product_id, Review.status == ReviewStatus.APPROVED)
    )
    if sort == "newest":
        query = query.order_by(Review.created_at.desc())
    else:
        # "Top reviews" — highest rating first, most recent as the tiebreak.
        query = query.order_by(Review.rating.desc(), Review.created_at.desc())

    reviews = query.all()

    agg = (
        db.query(func.avg(Review.rating), func.count(Review.id))
        .filter(Review.product_id == product_id, Review.status == ReviewStatus.APPROVED)
        .first()
    )
    average_rating = round(float(agg[0]), 2) if agg and agg[0] is not None else None
    total_reviews = agg[1] if agg else 0

    review_outs = []
    for r in reviews:
        out = ReviewOut.model_validate(r)
        out.user_name = r.user.name if r.user else None
        review_outs.append(out)

    return ProductReviewsOut(average_rating=average_rating, total_reviews=total_reviews, reviews=review_outs)