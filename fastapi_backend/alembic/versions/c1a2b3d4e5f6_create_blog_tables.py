"""create blog tables (posts, comments, likes)

Revision ID: c1a2b3d4e5f6
Revises: b6d2f4a8c105
Create Date: 2026-09-10 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'c1a2b3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'b6d2f4a8c105'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "blog_posts",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("author_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index(op.f("ix_blog_posts_author_id"), "blog_posts", ["author_id"], unique=False)

    op.create_table(
        "blog_comments",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("post_id", sa.Integer(), sa.ForeignKey("blog_posts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index(op.f("ix_blog_comments_post_id"), "blog_comments", ["post_id"], unique=False)
    op.create_index(op.f("ix_blog_comments_user_id"), "blog_comments", ["user_id"], unique=False)

    op.create_table(
        "blog_likes",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("post_id", sa.Integer(), sa.ForeignKey("blog_posts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.UniqueConstraint("post_id", "user_id", name="uq_like_user_post"),
    )
    op.create_index(op.f("ix_blog_likes_post_id"), "blog_likes", ["post_id"], unique=False)
    op.create_index(op.f("ix_blog_likes_user_id"), "blog_likes", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_blog_likes_user_id"), table_name="blog_likes")
    op.drop_index(op.f("ix_blog_likes_post_id"), table_name="blog_likes")
    op.drop_table("blog_likes")

    op.drop_index(op.f("ix_blog_comments_user_id"), table_name="blog_comments")
    op.drop_index(op.f("ix_blog_comments_post_id"), table_name="blog_comments")
    op.drop_table("blog_comments")

    op.drop_index(op.f("ix_blog_posts_author_id"), table_name="blog_posts")
    op.drop_table("blog_posts")