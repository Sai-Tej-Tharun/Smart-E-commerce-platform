"""
schemas/recommendation.py
----------------------------
NEW (Recommendation System milestone).
"""

from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel


class RecommendedProductOut(BaseModel):
    id: int
    name: str
    description: Optional[str]
    price: Decimal
    stock: int
    images: List[str]
    category: Optional[str]
    popularity: int

    # Computed in services/recommendation_service.py from approved reviews
    # only, same pattern as ProductOut — not real columns on Product.
    average_rating: Optional[float] = None
    review_count: int = 0

    class Config:
        from_attributes = True


class RecommendationsOut(BaseModel):
    """Response for GET /recommendations/{user_id}. `source` tells the
    frontend whether these are truly personalized or a cold-start
    fallback, so the UI can label the section honestly (e.g. show
    "Trending now" copy instead of "Because you viewed..." copy)."""

    source: str  # "personalized" | "trending"
    products: List[RecommendedProductOut]


class SimilarProductsOut(BaseModel):
    """Response for GET /products/{id}/similar."""

    product_id: int
    products: List[RecommendedProductOut]


class TrendingProductsOut(BaseModel):
    """Response for GET /products/trending."""

    products: List[RecommendedProductOut]