"""
core/subscription_limits.py
--------------------------------
Model-level access control for the blog's subscription plans. Every
enforcement function here raises the same friendly 403 when a user is
over their plan's limit, and is a no-op (returns None) when the relevant
limit is -1 (unlimited, i.e. the Pro plan).

Called from routes/blog.py before a post/comment/like is actually
created, and from routes/blog.py's image handling before files are saved.
"""

from datetime import datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from models.blog import Comment, Like, Post
from models.subscription import PlanName, SubscriptionPlan
from models.user import User

LIMIT_MESSAGE = "You've reached your plan limit. Kindly upgrade your plan to continue."


def get_active_plan(db: Session, user: User) -> SubscriptionPlan:
    """
    Every user should have subscription_plan_id set (backfilled by the
    migration in this document), but this falls back to Basic defensively
    in case a user row somehow has it null.
    """
    if user.subscription_plan_id:
        plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.id == user.subscription_plan_id).first()
        if plan:
            return plan
    basic = db.query(SubscriptionPlan).filter(SubscriptionPlan.name == PlanName.BASIC).first()
    if not basic:
        raise RuntimeError("Basic plan is missing — has the subscription seed migration been run?")
    return basic


def _start_of_today() -> datetime:
    now = datetime.utcnow()
    return datetime(now.year, now.month, now.day)


def enforce_post_limit(db: Session, user: User) -> None:
    plan = get_active_plan(db, user)
    if plan.max_posts == -1:
        return
    current_count = db.query(func.count(Post.id)).filter(Post.author_id == user.id).scalar() or 0
    if current_count >= plan.max_posts:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=LIMIT_MESSAGE)


def enforce_image_limit(db: Session, user: User, incoming_image_count: int) -> None:
    plan = get_active_plan(db, user)
    if plan.max_images_per_post == -1:
        return
    if incoming_image_count > plan.max_images_per_post:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=LIMIT_MESSAGE)


def enforce_like_limit(db: Session, user: User) -> None:
    plan = get_active_plan(db, user)
    if plan.max_likes_per_day == -1:
        return
    today_count = (
        db.query(func.count(Like.id))
        .filter(Like.user_id == user.id, Like.created_at >= _start_of_today())
        .scalar()
        or 0
    )
    if today_count >= plan.max_likes_per_day:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=LIMIT_MESSAGE)


def enforce_comment_limit(db: Session, user: User) -> None:
    plan = get_active_plan(db, user)
    if plan.max_comments_per_day == -1:
        return
    today_count = (
        db.query(func.count(Comment.id))
        .filter(Comment.user_id == user.id, Comment.created_at >= _start_of_today())
        .scalar()
        or 0
    )
    if today_count >= plan.max_comments_per_day:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=LIMIT_MESSAGE)