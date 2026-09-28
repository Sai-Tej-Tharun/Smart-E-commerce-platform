"""add status, scheduled_at, published_at to blog_posts

Revision ID: a7c1d9e4f2b6
Revises: b2c3d4e5f6a8
Create Date: 2026-09-28 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'a7c1d9e4f2b6'
down_revision: Union[str, Sequence[str], None] = 'b2c3d4e5f6a8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Existing posts were all live, so they default to "published".
    op.add_column("blog_posts", sa.Column("status", sa.String(20), nullable=False, server_default="published"))
    op.add_column("blog_posts", sa.Column("scheduled_at", sa.DateTime(), nullable=True))
    op.add_column("blog_posts", sa.Column("published_at", sa.DateTime(), nullable=True))
    op.execute("UPDATE blog_posts SET published_at = created_at WHERE published_at IS NULL")
    op.create_index("ix_blog_posts_status", "blog_posts", ["status"])
    op.create_index("ix_blog_posts_scheduled_at", "blog_posts", ["scheduled_at"])


def downgrade() -> None:
    op.drop_index("ix_blog_posts_scheduled_at", table_name="blog_posts")
    op.drop_index("ix_blog_posts_status", table_name="blog_posts")
    op.drop_column("blog_posts", "published_at")
    op.drop_column("blog_posts", "scheduled_at")
    op.drop_column("blog_posts", "status")