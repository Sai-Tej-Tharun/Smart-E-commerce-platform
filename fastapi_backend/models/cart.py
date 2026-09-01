"""
models/cart.py
-----------------
Cart items. Named CartItem (not Cart) because each row is one product line
within a user's cart — a user implicitly "has a cart" as the set of their
CartItem rows, rather than needing a separate empty Cart header row.
"""

from sqlalchemy import Column, DateTime, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from core.database import Base


class CartItem(Base):
    __tablename__ = "cart_items"
    __table_args__ = (
        # a user can only have ONE row per product; adding the same product
        # again should increase quantity, not create a duplicate row
        UniqueConstraint("user_id", "product_id", name="uq_cart_user_product"),
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    quantity = Column(Integer, default=1, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="cart_items")
    product = relationship("Product")

    def __repr__(self) -> str:
        return f"<CartItem user_id={self.user_id} product_id={self.product_id} qty={self.quantity}>"
