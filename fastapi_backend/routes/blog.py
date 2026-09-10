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

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from core.database import get_db
from core.email import send_email
from core.security import get_current_user
from models.blog import Comment, Like, Post
from models.user import User
from schemas.blog import CommentCreate, CommentOut, LikeOut, PostCreate, PostOut, PostUpdate

logger = logging.getLogger("blog")

router = APIRouter(tags=["Blog"])


def _serialize_post(db: Session, post: Post) -> PostOut:
    like_count = db.query(func.count(Like.id)).filter(Like.post_id == post.id).scalar() or 0
    comment_count = db.query(func.count(Comment.id)).filter(Comment.post_id == post.id).scalar() or 0
    out = PostOut.model_validate(post)
    out.like_count = like_count
    out.comment_count = comment_count
    out.author_name = post.author.name if post.author else None
    return out


# ---------------------------------------------------------------- Posts ----

@router.post("/posts", response_model=PostOut, status_code=status.HTTP_201_CREATED)
def create_post(
    payload: PostCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    post = Post(title=payload.title, content=payload.content, author_id=current_user.id)
    db.add(post)
    db.commit()
    db.refresh(post)
    return _serialize_post(db, post)


@router.get("/posts", response_model=List[PostOut])
def list_posts(db: Session = Depends(get_db)):
    """Public — anyone can view all posts, no auth required."""
    posts = db.query(Post).order_by(Post.created_at.desc()).all()
    return [_serialize_post(db, p) for p in posts]


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
    payload: PostUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    if post.author_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only edit your own posts")

    if payload.title is not None:
        post.title = payload.title
    if payload.content is not None:
        post.content = payload.content

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

    db.delete(post)
    db.commit()
    return None


# ------------------------------------------------------------- Comments ----

@router.post("/posts/{post_id}/comments", response_model=CommentOut, status_code=status.HTTP_201_CREATED)
def add_comment(
    post_id: int,
    payload: CommentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

    comment = Comment(post_id=post_id, user_id=current_user.id, text=payload.text)
    db.add(comment)
    db.commit()
    db.refresh(comment)

    if post.author_id != current_user.id:
        try:
            send_email(
                to=post.author.email,
                subject="New comment on your post",
                body=f"{current_user.name} commented on '{post.title}':\n\n{payload.text}",
            )
        except Exception:
            logger.exception("Failed to send new-comment notification email to %s", post.author.email)

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

    like = Like(post_id=post_id, user_id=current_user.id)
    db.add(like)
    db.commit()
    db.refresh(like)

    if post.author_id != current_user.id:
        try:
            send_email(
                to=post.author.email,
                subject="Someone liked your post",
                body=f"{current_user.name} liked your post '{post.title}'.",
            )
        except Exception:
            logger.exception("Failed to send new-like notification email to %s", post.author.email)

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