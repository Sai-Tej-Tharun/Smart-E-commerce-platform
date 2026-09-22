"""
routes/dashboard.py
------------------------
GET /user/dashboard - the current user's own blog activity statistics.

Every figure here is scoped to current_user via JWT (core.security.get_current_user)
— there is no way to request another user's dashboard through this endpoint.
"""

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from core.database import get_db
from core.security import get_current_user
from models.blog import Comment, Like, Post
from models.user import User
from schemas.dashboard import DashboardOut, DashboardPostStat, DashboardTotals

router = APIRouter(prefix="/user", tags=["Dashboard"])


@router.get("/dashboard", response_model=DashboardOut)
def get_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    posts = (
        db.query(Post)
        .filter(Post.author_id == current_user.id)
        .order_by(Post.created_at.asc())
        .all()
    )

    total_comments_made = (
        db.query(func.count(Comment.id)).filter(Comment.user_id == current_user.id).scalar() or 0
    )

    post_stats: list[DashboardPostStat] = []
    total_likes_received = 0
    total_views = 0

    for post in posts:
        like_count = db.query(func.count(Like.id)).filter(Like.post_id == post.id).scalar() or 0
        comment_count = db.query(func.count(Comment.id)).filter(Comment.post_id == post.id).scalar() or 0
        views = post.views or 0

        total_likes_received += like_count
        total_views += views

        post_stats.append(
            DashboardPostStat(
                post_id=post.id,
                title=post.title,
                likes=like_count,
                comments=comment_count,
                views=views,
                created_at=post.created_at,
            )
        )

    return DashboardOut(
        totals=DashboardTotals(
            total_posts=len(posts),
            total_comments_made=total_comments_made,
            total_likes_received=total_likes_received,
            total_views=total_views,
        ),
        posts=post_stats,
    )