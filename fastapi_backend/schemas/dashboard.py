"""
schemas/dashboard.py
-------------------------
Response shapes for GET /user/dashboard.
"""

from datetime import datetime
from typing import List

from pydantic import BaseModel


class DashboardPostStat(BaseModel):
    """One row per post the current user owns — feeds the per-post chart."""
    post_id: int
    title: str
    likes: int
    comments: int
    views: int
    created_at: datetime


class DashboardTotals(BaseModel):
    total_posts: int
    total_comments_made: int
    total_likes_received: int
    total_views: int


class DashboardOut(BaseModel):
    totals: DashboardTotals
    posts: List[DashboardPostStat]