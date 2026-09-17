"""
models/blog.py
------------------
Blog Management feature: Post, Comment, Like.

Follows the same conventions as models/review.py in this project:
  - FKs to users.id with ondelete="CASCADE"
  - a UniqueConstraint enforcing "one like per user per post" at the DB level
"""

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from core.database import Base


class Post(Base):
    __tablename__ = "blog_posts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    author_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    author = relationship("User")
    comments = relationship("Comment", back_populates="post", cascade="all, delete-orphan")
    likes = relationship("Like", back_populates="post", cascade="all, delete-orphan")
    images = relationship("PostImage", back_populates="post", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Post id={self.id} author_id={self.author_id} title={self.title!r}>"


class Comment(Base):
    __tablename__ = "blog_comments"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    post_id = Column(Integer, ForeignKey("blog_posts.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    text = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    post = relationship("Post", back_populates="comments")
    user = relationship("User")

    def __repr__(self) -> str:
        return f"<Comment id={self.id} post_id={self.post_id} user_id={self.user_id}>"


class Like(Base):
    __tablename__ = "blog_likes"
    __table_args__ = (UniqueConstraint("post_id", "user_id", name="uq_like_user_post"),)

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    post_id = Column(Integer, ForeignKey("blog_posts.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    # Added for the subscription feature's per-day like-limit check.
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    post = relationship("Post", back_populates="likes")
    user = relationship("User")

    def __repr__(self) -> str:
        return f"<Like post_id={self.post_id} user_id={self.user_id}>"


class PostImage(Base):
    """
    One row per uploaded image. A post can have 1 (Basic), 2 (Premium), or
    unlimited (Pro) of these — enforced in routes/blog.py via
    core/subscription_limits.py, not at the table level, since the limit
    depends on the post's author's current plan, not a fixed schema rule.
    """
    __tablename__ = "blog_post_images"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    post_id = Column(Integer, ForeignKey("blog_posts.id", ondelete="CASCADE"), nullable=False, index=True)
    image_url = Column(String(255), nullable=False)  # e.g. "/media/posts/<uuid>.jpg"
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    post = relationship("Post", back_populates="images")

    def __repr__(self) -> str:
        return f"<PostImage post_id={self.post_id} url={self.image_url}>"