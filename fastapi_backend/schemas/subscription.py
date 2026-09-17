"""
schemas/subscription.py
----------------------------
Request/response models for plans, subscribing, and billing history.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from models.subscription import PlanName


class SubscriptionPlanOut(BaseModel):
    id: int
    name: PlanName
    price: float
    max_posts: int
    max_images_per_post: int
    max_likes_per_day: int
    max_comments_per_day: int

    class Config:
        from_attributes = True


class SubscribeRequest(BaseModel):
    plan: PlanName


class BillingHistoryOut(BaseModel):
    id: int
    plan_name: PlanName
    price: float
    start_date: datetime
    end_date: datetime
    transaction_id: str
    invoice_url: Optional[str] = None

    class Config:
        from_attributes = True


class MySubscriptionOut(BaseModel):
    plan: SubscriptionPlanOut
    posts_used: int
    images_used_today: Optional[int] = None  # not tracked cumulatively; per-post at creation time
    likes_used_today: int
    comments_used_today: int