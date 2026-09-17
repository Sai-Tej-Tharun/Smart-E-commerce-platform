"""
models/subscription.py
--------------------------
Subscription plans and billing history for the blog feature's
plan-based access control.

SubscriptionPlan rows are seed data (Basic/Premium/Pro), not something
users create — see the migration in this document for the three rows.
-1 in any limit column means "unlimited" (used by the Pro plan).
"""

import enum

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from core.database import Base


class PlanName(str, enum.Enum):
    BASIC = "basic"
    PREMIUM = "premium"
    PRO = "pro"


class SubscriptionPlan(Base):
    __tablename__ = "subscription_plans"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(Enum(PlanName), unique=True, nullable=False)
    price = Column(Numeric(10, 2), nullable=False)

    # -1 = unlimited
    max_posts = Column(Integer, nullable=False)
    max_images_per_post = Column(Integer, nullable=False)
    max_likes_per_day = Column(Integer, nullable=False)
    max_comments_per_day = Column(Integer, nullable=False)

    def __repr__(self) -> str:
        return f"<SubscriptionPlan {self.name} ₹{self.price}>"


class BillingHistory(Base):
    __tablename__ = "billing_history"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    plan_id = Column(Integer, ForeignKey("subscription_plans.id"), nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
    transaction_id = Column(String(64), nullable=False, unique=True)
    invoice_path = Column(String(255), nullable=True)  # e.g. "/media/invoices/<uuid>.pdf"
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User")
    plan = relationship("SubscriptionPlan")

    def __repr__(self) -> str:
        return f"<BillingHistory user_id={self.user_id} plan_id={self.plan_id} tx={self.transaction_id}>"