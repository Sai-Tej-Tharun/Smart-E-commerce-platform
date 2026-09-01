"""
models/product.py
--------------------
Product catalog table. `images` stores a JSON array of image URLs rather
than a separate table, since Day 1 scope doesn't require per-image metadata.
"""

from sqlalchemy import Column, DateTime, Integer, JSON, Numeric, String, Text
from sqlalchemy.sql import func

from core.database import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    price = Column(Numeric(10, 2), nullable=False)
    stock = Column(Integer, default=0, nullable=False)
    images = Column(JSON, default=list, nullable=False)  # e.g. ["https://.../img1.jpg"]
    category = Column(String(100), nullable=True, index=True)
    # Simple popularity counter: incremented every time this product is
    # added to a cart (see routes/cart.py). Used for the ?sort=popularity
    # catalog filter — a lightweight stand-in for real order/analytics data.
    popularity = Column(Integer, default=0, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self) -> str:
        return f"<Product id={self.id} name={self.name} price={self.price}>"
