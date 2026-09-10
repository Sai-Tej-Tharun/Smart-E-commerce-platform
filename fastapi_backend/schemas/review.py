from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class ReviewCreate(BaseModel):
    product_id: int
    rating: int = Field(ge=1, le=5)
    comment: Optional[str] = None


class ReviewOut(BaseModel):
    id: int
    user_id: int
    product_id: int
    rating: int
    comment: Optional[str]
    status: str
    created_at: datetime
    # Denormalized onto the response so the frontend can show "by Alice"
    # without a second lookup — populated in routes/reviews.py, not a real
    # column on the Review model itself.
    user_name: Optional[str] = None

    class Config:
        from_attributes = True


class ProductReviewsOut(BaseModel):
    """Response for GET /products/{id}/reviews — the Rating Aggregation
    requirement (average + total) bundled with the review list itself, so
    the frontend gets both in one call."""
    average_rating: Optional[float] = None
    total_reviews: int
    reviews: List[ReviewOut]