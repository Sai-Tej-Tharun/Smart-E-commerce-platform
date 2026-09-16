"""add image column to blog_posts

Revision ID: d7e8f9a1b234
Revises: c1a2b3d4e5f6
Create Date: 2026-09-15 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'd7e8f9a1b234'
down_revision: Union[str, Sequence[str], None] = 'c1a2b3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("blog_posts", sa.Column("image", sa.String(255), nullable=True))


def downgrade() -> None:
    op.drop_column("blog_posts", "image")