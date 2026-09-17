"""
routes/subscriptions.py
----------------------------
POST /subscriptions/subscribe   - change plan, create a BillingHistory row, generate an invoice PDF
GET  /subscriptions/plans       - list the 3 available plans (public)
GET  /subscriptions/my          - current plan + today's usage
GET  /subscriptions/invoices    - the current user's billing history
"""

import uuid
from datetime import datetime, timedelta
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from core.database import get_db
from core.invoices import generate_invoice_pdf
from core.security import get_current_user
from models.blog import Comment, Like, Post
from models.subscription import BillingHistory, SubscriptionPlan
from models.user import User
from schemas.subscription import BillingHistoryOut, MySubscriptionOut, SubscribeRequest, SubscriptionPlanOut

router = APIRouter(prefix="/subscriptions", tags=["Subscriptions"])

SUBSCRIPTION_PERIOD_DAYS = 30


@router.get("/plans", response_model=List[SubscriptionPlanOut])
def list_plans(db: Session = Depends(get_db)):
    """Public — anyone can see what the three plans offer."""
    return db.query(SubscriptionPlan).order_by(SubscriptionPlan.price.asc()).all()


@router.post("/subscribe", response_model=BillingHistoryOut, status_code=status.HTTP_201_CREATED)
def subscribe(
    payload: SubscribeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.name == payload.plan).first()
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")

    start_date = datetime.utcnow()
    end_date = start_date + timedelta(days=SUBSCRIPTION_PERIOD_DAYS)
    transaction_id = f"TXN-{uuid.uuid4().hex[:12].upper()}"

    invoice_path = generate_invoice_pdf(
        user_name=current_user.name,
        plan_name=plan.name.value.capitalize(),
        price=f"₹{plan.price}",
        start_date=start_date.strftime("%Y-%m-%d"),
        end_date=end_date.strftime("%Y-%m-%d"),
        transaction_id=transaction_id,
    )

    billing_row = BillingHistory(
        user_id=current_user.id,
        plan_id=plan.id,
        price=plan.price,
        start_date=start_date,
        end_date=end_date,
        transaction_id=transaction_id,
        invoice_path=invoice_path,
    )
    db.add(billing_row)

    current_user.subscription_plan_id = plan.id

    db.commit()
    db.refresh(billing_row)

    return BillingHistoryOut(
        id=billing_row.id,
        plan_name=plan.name,
        price=float(billing_row.price),
        start_date=billing_row.start_date,
        end_date=billing_row.end_date,
        transaction_id=billing_row.transaction_id,
        invoice_url=billing_row.invoice_path,
    )


@router.get("/my", response_model=MySubscriptionOut)
def my_subscription(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from core.subscription_limits import _start_of_today, get_active_plan  # local import avoids a circular import at module load time

    plan = get_active_plan(db, current_user)
    posts_used = db.query(func.count(Post.id)).filter(Post.author_id == current_user.id).scalar() or 0
    likes_today = (
        db.query(func.count(Like.id))
        .filter(Like.user_id == current_user.id, Like.created_at >= _start_of_today())
        .scalar()
        or 0
    )
    comments_today = (
        db.query(func.count(Comment.id))
        .filter(Comment.user_id == current_user.id, Comment.created_at >= _start_of_today())
        .scalar()
        or 0
    )

    return MySubscriptionOut(
        plan=plan,
        posts_used=posts_used,
        likes_used_today=likes_today,
        comments_used_today=comments_today,
    )


@router.get("/invoices", response_model=List[BillingHistoryOut])
def my_invoices(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(BillingHistory)
        .filter(BillingHistory.user_id == current_user.id)
        .order_by(BillingHistory.created_at.desc())
        .all()
    )
    return [
        BillingHistoryOut(
            id=r.id,
            plan_name=r.plan.name,
            price=float(r.price),
            start_date=r.start_date,
            end_date=r.end_date,
            transaction_id=r.transaction_id,
            invoice_url=r.invoice_path,
        )
        for r in rows
    ]