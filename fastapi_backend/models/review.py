"""
models/review.py
--------------------
One row per product review. `status` starts PENDING and only becomes
visible to shoppers once an admin approves it — moderation happens
directly in the Django admin (a simple editable `status` field there,
see django_admin/storefront/admin.py's ReviewAdmin), since approving a
review has no side effects worth building a dedicated API for, unlike
approving a return (which triggers a refund) — see routes/admin_returns.py
for the contrast.

The unique constraint on (user_id, product_id) is what enforces "one
review per user per product" at the database level — routes/reviews.py
also checks this before insert (for a clean error message), but the
constraint is the actual guarantee.
"""

import enum

from sqlalchemy import CheckConstraint, Column, DateTime, Enum, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from core.database import Base


class ReviewStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class Review(Base):
    __tablename__ = "reviews"
    __table_args__ = (
        UniqueConstraint("user_id", "product_id", name="uq_review_user_product"),
        CheckConstraint("rating >= 1 AND rating <= 5", name="ck_review_rating_range"),
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    rating = Column(Integer, nullable=False)
    comment = Column(Text, nullable=True)
    status = Column(Enum(ReviewStatus), default=ReviewStatus.PENDING, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User")
    product = relationship("Product")

    def __repr__(self) -> str:
        return f"<Review user_id={self.user_id} product_id={self.product_id} rating={self.rating} status={self.status}>"