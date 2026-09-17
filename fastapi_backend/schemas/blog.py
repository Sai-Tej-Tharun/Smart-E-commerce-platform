"""
schemas/blog.py
-------------------
Pydantic request/response models for the Blog Management feature.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


# ---------- Post ----------
class PostCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)


class PostUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    content: Optional[str] = Field(None, min_length=1)


class PostOut(BaseModel):
    id: int
    title: str
    content: str
    images: List[str] = Field(default_factory=list)
    author_id: int
    created_at: datetime
    # Denormalized for the frontend — populated in routes/blog.py, not a real column
    author_name: Optional[str] = None
    like_count: int = 0
    comment_count: int = 0

    class Config:
        from_attributes = True


# ---------- Comment ----------
class CommentCreate(BaseModel):
    text: str = Field(..., min_length=1, max_length=1000)


class CommentOut(BaseModel):
    id: int
    post_id: int
    user_id: int
    text: str
    created_at: datetime
    user_name: Optional[str] = None

    class Config:
        from_attributes = True


# ---------- Like ----------
class LikeOut(BaseModel):
    id: int
    post_id: int
    user_id: int

    class Config:
        from_attributes = True


class PaginatedPostsOut(BaseModel):
    items: List[PostOut]
    total: int
    page: int
    limit: int
    total_pages: int