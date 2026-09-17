"""add subscription plans, billing history, post images, like timestamps

Revision ID: e1f2a3b4c5d6
Revises: d7e8f9a1b234
Create Date: 2026-09-17 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'e1f2a3b4c5d6'
down_revision: Union[str, Sequence[str], None] = 'd7e8f9a1b234'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

plan_enum = sa.Enum("BASIC", "PREMIUM", "PRO", name="planname")


def upgrade() -> None:
    # --- subscription_plans ---
    plan_enum.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "subscription_plans",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", plan_enum, nullable=False, unique=True),
        sa.Column("price", sa.Numeric(10, 2), nullable=False),
        sa.Column("max_posts", sa.Integer(), nullable=False),
        sa.Column("max_images_per_post", sa.Integer(), nullable=False),
        sa.Column("max_likes_per_day", sa.Integer(), nullable=False),
        sa.Column("max_comments_per_day", sa.Integer(), nullable=False),
    )

    # --- billing_history ---
    op.create_table(
        "billing_history",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("plan_id", sa.Integer(), sa.ForeignKey("subscription_plans.id"), nullable=False),
        sa.Column("price", sa.Numeric(10, 2), nullable=False),
        sa.Column("start_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("transaction_id", sa.String(64), nullable=False, unique=True),
        sa.Column("invoice_path", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index(op.f("ix_billing_history_user_id"), "billing_history", ["user_id"], unique=False)

    # --- users.subscription_plan_id ---
    op.add_column("users", sa.Column("subscription_plan_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_users_subscription_plan_id",
        "users",
        "subscription_plans",
        ["subscription_plan_id"],
        ["id"],
    )

    # --- blog_post_images ---
    op.create_table(
        "blog_post_images",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("post_id", sa.Integer(), sa.ForeignKey("blog_posts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("image_url", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index(op.f("ix_blog_post_images_post_id"), "blog_post_images", ["post_id"], unique=False)

    # --- drop the old single-image column now that blog_post_images replaces it ---
    op.drop_column("blog_posts", "image")

    # --- blog_likes.created_at (for per-day like-limit checks) ---
    op.add_column("blog_likes", sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()))

    # --- seed the three plans ---
    subscription_plans = sa.table(
        "subscription_plans",
        sa.column("id", sa.Integer),
        sa.column("name", plan_enum),
        sa.column("price", sa.Numeric),
        sa.column("max_posts", sa.Integer),
        sa.column("max_images_per_post", sa.Integer),
        sa.column("max_likes_per_day", sa.Integer),
        sa.column("max_comments_per_day", sa.Integer),
    )
    op.bulk_insert(
        subscription_plans,
        [
            {
                "id": 1, "name": "BASIC", "price": 0.00,
                "max_posts": 1, "max_images_per_post": 1,
                "max_likes_per_day": 5, "max_comments_per_day": 5,
            },
            {
                "id": 2, "name": "PREMIUM", "price": 9.99,
                "max_posts": 2, "max_images_per_post": 2,
                "max_likes_per_day": 20, "max_comments_per_day": 20,
            },
            {
                "id": 3, "name": "PRO", "price": 29.99,
                "max_posts": -1, "max_images_per_post": -1,
                "max_likes_per_day": -1, "max_comments_per_day": -1,
            },
        ],
    )

    # --- backfill every existing user onto Basic (id=1) ---
    op.execute("UPDATE users SET subscription_plan_id = 1 WHERE subscription_plan_id IS NULL")


def downgrade() -> None:
    op.drop_column("blog_likes", "created_at")

    op.add_column("blog_posts", sa.Column("image", sa.String(255), nullable=True))

    op.drop_index(op.f("ix_blog_post_images_post_id"), table_name="blog_post_images")
    op.drop_table("blog_post_images")

    op.drop_constraint("fk_users_subscription_plan_id", "users", type_="foreignkey")
    op.drop_column("users", "subscription_plan_id")

    op.drop_index(op.f("ix_billing_history_user_id"), table_name="billing_history")
    op.drop_table("billing_history")

    op.drop_table("subscription_plans")
    plan_enum.drop(op.get_bind(), checkfirst=True)