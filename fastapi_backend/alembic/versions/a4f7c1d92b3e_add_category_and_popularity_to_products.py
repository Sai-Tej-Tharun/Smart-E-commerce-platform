"""add category and popularity to products

Revision ID: a4f7c1d92b3e
Revises: e338d74928c7
Create Date: 2026-08-17 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'a4f7c1d92b3e'
down_revision: Union[str, Sequence[str], None] = 'e338d74928c7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("products", sa.Column("category", sa.String(length=100), nullable=True))
    op.add_column("products", sa.Column("popularity", sa.Integer(), nullable=False, server_default="0"))
    op.create_index(op.f("ix_products_category"), "products", ["category"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_products_category"), table_name="products")
    op.drop_column("products", "popularity")
    op.drop_column("products", "category")
