"""
routes/blog.py
------------------
Blog Management feature.

POST   /posts                          - create a post (auth required)
GET    /posts                          - list all posts (public)
GET    /posts/mine                     - current user's own posts (auth required)
GET    /posts/{post_id}                - view a single post (public)
PUT    /posts/{post_id}                - update own post (auth + ownership)
DELETE /posts/{post_id}                - delete own post (auth + ownership)

POST   /posts/{post_id}/comments       - add a comment (auth required)
GET    /posts/{post_id}/comments       - list comments (public)
DELETE /posts/{post_id}/comments/{id}  - delete own comment, or comment on your own post (auth)

POST   /posts/{post_id}/like           - like a post (auth required)
DELETE /posts/{post_id}/like           - unlike a post (auth required)

Route order note: /posts/mine is declared BEFORE /posts/{post_id}, same
reasoning as recommendations.router vs products.router in main.py — otherwise
FastAPI would try to parse "mine" as a post_id and 422 instead of 200.

Email notifications reuse core/email.py's send_email(), same
graceful-degradation pattern as core/notify.py: if SMTP_HOST isn't set in
.env, the email is logged instead of sent, so this works out of the box
with nothing configured.
"""

import logging
from typing import List

from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from core.database import get_db
from core.media import delete_post_image, save_post_image
from core.security import get_current_user
from core.subscription_limits import enforce_comment_limit, enforce_image_limit, enforce_like_limit, enforce_post_limit
from models.blog import Comment, Like, Post, PostImage
from models.user import User
from services.notification_service import notify_post_owner_of_comment, notify_post_owner_of_like
from schemas.blog import (
    CommentCreate,
    CommentOut,
    LikeOut,
    PaginatedPostsOut,
    PostOut,
    PostUpdate,
)

logger = logging.getLogger("blog")

router = APIRouter(tags=["Blog"])


def _serialize_post(db: Session, post: Post) -> PostOut:
    like_count = (
        db.query(func.count(Like.id))
        .filter(Like.post_id == post.id)
        .scalar()
        or 0
    )

    comment_count = (
        db.query(func.count(Comment.id))
        .filter(Comment.post_id == post.id)
        .scalar()
        or 0
    )

    out = PostOut(
        id=post.id,
        title=post.title,
        content=post.content,
        images=[img.image_url for img in post.images],
        author_id=post.author_id,
        created_at=post.created_at,
        author_name=post.author.name if post.author else None,
        like_count=like_count,
        comment_count=comment_count,
    )

    return out


# ---------------------------------------------------------------- Posts ----

@router.post("/posts", response_model=PostOut, status_code=status.HTTP_201_CREATED)
def create_post(
    title: str = Form(..., min_length=1, max_length=200),
    content: str = Form(..., min_length=1),
    images: List[UploadFile] = File(default=[]),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    enforce_post_limit(db, current_user)

    uploaded = [f for f in images if f is not None and f.filename]
    enforce_image_limit(db, current_user, len(uploaded))

    post = Post(title=title, content=content, author_id=current_user.id)
    db.add(post)
    db.flush()  # assigns post.id without committing, so PostImage rows can reference it

    for f in uploaded:
        try:
            image_path = save_post_image(f)
        except ValueError as e:
            db.rollback()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        db.add(PostImage(post_id=post.id, image_url=image_path))

    db.commit()
    db.refresh(post)
    return _serialize_post(db, post)


@router.get("/posts", response_model=PaginatedPostsOut)
def list_posts(
    page: int = Query(1, ge=1, description="1-indexed page number"),
    limit: int = Query(10, ge=1, le=100, description="Posts per page (max 100)"),
    search: Optional[str] = Query(None, min_length=1, description="Matches against title or content"),
    db: Session = Depends(get_db),
):
    """Public — anyone can view all posts, no auth required. Supports pagination and search together."""
    query = db.query(Post)

    if search:
        like_pattern = f"%{search}%"
        query = query.filter(or_(Post.title.ilike(like_pattern), Post.content.ilike(like_pattern)))

    total = query.count()
    total_pages = (total + limit - 1) // limit if total > 0 else 0

    posts = (
        query.order_by(Post.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )

    return PaginatedPostsOut(
        items=[_serialize_post(db, p) for p in posts],
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages,
    )


@router.get("/posts/mine", response_model=List[PostOut])
def my_posts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    posts = (
        db.query(Post)
        .filter(Post.author_id == current_user.id)
        .order_by(Post.created_at.desc())
        .all()
    )
    return [_serialize_post(db, p) for p in posts]


@router.get("/posts/{post_id}", response_model=PostOut)
def get_post(post_id: int, db: Session = Depends(get_db)):
    """Public — anyone can view a single post."""
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    return _serialize_post(db, post)


@router.put("/posts/{post_id}", response_model=PostOut)
def update_post(
    post_id: int,
    title: Optional[str] = Form(None, min_length=1, max_length=200),
    content: Optional[str] = Form(None, min_length=1),
    images: List[UploadFile] = File(default=[]),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    If `images` is provided (non-empty), it REPLACES all of the post's
    existing images — this keeps the plan-limit check simple (count the
    new set, not "existing + new"). Omit `images` entirely to leave the
    post's current images untouched while editing title/content.
    """
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    if post.author_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only edit your own posts")

    if title is not None:
        post.title = title
    if content is not None:
        post.content = content

    uploaded = [f for f in images if f is not None and f.filename]
    if uploaded:
        enforce_image_limit(db, current_user, len(uploaded))

        for old in list(post.images):
            delete_post_image(old.image_url)
            db.delete(old)

        for f in uploaded:
            try:
                image_path = save_post_image(f)
            except ValueError as e:
                db.rollback()
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
            db.add(PostImage(post_id=post.id, image_url=image_path))

    db.commit()
    db.refresh(post)
    return _serialize_post(db, post)


@router.delete("/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    if post.author_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only delete your own posts")

    for img in post.images:
        delete_post_image(img.image_url)
    db.delete(post)  # cascades to blog_post_images via the relationship/FK
    db.commit()
    return None


# ------------------------------------------------------------- Comments ----

@router.post("/posts/{post_id}/comments", response_model=CommentOut, status_code=status.HTTP_201_CREATED)
def add_comment(
    post_id: int,
    payload: CommentCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

    enforce_comment_limit(db, current_user)

    comment = Comment(post_id=post_id, user_id=current_user.id, text=payload.text)
    db.add(comment)
    db.commit()
    db.refresh(comment)

    background_tasks.add_task(notify_post_owner_of_comment, post, current_user)

    out = CommentOut.model_validate(comment)
    out.user_name = current_user.name
    return out


@router.get("/posts/{post_id}/comments", response_model=List[CommentOut])
def list_comments(post_id: int, db: Session = Depends(get_db)):
    """Public — anyone can view comments."""
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

    comments = (
        db.query(Comment)
        .filter(Comment.post_id == post_id)
        .order_by(Comment.created_at.asc())
        .all()
    )
    outs = []
    for c in comments:
        out = CommentOut.model_validate(c)
        out.user_name = c.user.name if c.user else None
        outs.append(out)
    return outs


@router.delete("/posts/{post_id}/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comment(
    post_id: int,
    comment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    comment = (
        db.query(Comment)
        .filter(Comment.id == comment_id, Comment.post_id == post_id)
        .first()
    )
    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")

    post = db.query(Post).filter(Post.id == post_id).first()
    # Either the comment's author OR the post's owner can remove a comment
    if comment.user_id != current_user.id and post.author_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this comment")

    db.delete(comment)
    db.commit()
    return None


# ---------------------------------------------------------------- Likes ----

@router.post("/posts/{post_id}/like", response_model=LikeOut, status_code=status.HTTP_201_CREATED)
def like_post(
    post_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

    existing = (
        db.query(Like)
        .filter(Like.post_id == post_id, Like.user_id == current_user.id)
        .first()
    )
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You already liked this post")

    enforce_like_limit(db, current_user)

    like = Like(post_id=post_id, user_id=current_user.id)
    db.add(like)
    db.commit()
    db.refresh(like)

    background_tasks.add_task(notify_post_owner_of_like, post, current_user)

    return like


@router.delete("/posts/{post_id}/like", status_code=status.HTTP_204_NO_CONTENT)
def unlike_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    like = (
        db.query(Like)
        .filter(Like.post_id == post_id, Like.user_id == current_user.id)
        .first()
    )
    if not like:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="You haven't liked this post")

    db.delete(like)
    db.commit()
    return None