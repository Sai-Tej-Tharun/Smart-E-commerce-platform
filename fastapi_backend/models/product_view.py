
"""
models/product_view.py
------------------------
NEW (Recommendation System milestone).

One row per product page view. user_id is nullable so anonymous/guest
views still count toward storewide "trending" / "most viewed" signals,
while only rows WITH a user_id feed that specific user's personalized
"browsing history" signal in services/recommendation_service.py.

Rows are written by routes/products.py's get_product() on every
GET /products/{id} call (see services.recommendation_service.record_product_view).
No update/delete path is needed — this is an append-only event log.
"""

from sqlalchemy import Column, DateTime, ForeignKey, Integer
from sqlalchemy.sql import func

from core.database import Base


class ProductView(Base):
    __tablename__ = "product_views"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    viewed_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    def __repr__(self) -> str:
        return f"<ProductView user_id={self.user_id} product_id={self.product_id} viewed_at={self.viewed_at}>"
