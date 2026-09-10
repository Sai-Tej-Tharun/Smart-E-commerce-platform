"""
routes/recommendations.py
----------------------------
NEW (Recommendation System milestone).

GET /recommendations/{user_id}   - personalized picks for one user
                                    ("Recommended For You")
GET /products/{id}/similar       - content-based similar products
                                    ("Similar Products")
GET /products/trending           - storewide most-viewed/top-rated
                                    ("You May Also Like" / trending rail)

All scoring logic lives in services/recommendation_service.py — this file
only handles HTTP concerns (auth, query params, response shaping).

GET /recommendations/{user_id} requires authentication. A customer can
only ever request their OWN id — the same "you can only see your own
data" rule routes/cart.py and routes/orders.py already use. staff/admin
may look up any user's recommendations.

IMPORTANT — registration order in main.py: this router defines
GET /products/trending, a single path segment that collides with
routes/products.py's GET /products/{product_id}. FastAPI matches routes
in the order they're registered, so this router MUST be included with
app.include_router(...) BEFORE products.router, or "/products/trending"
will be swallowed by "/products/{product_id}" and return a 422 (failing
to parse "trending" as an int). See the main.py snippet in the write-up.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from core.database import get_db
from core.security import get_current_user
from models.product_view import ProductView
from models.user import User
from schemas.recommendation import RecommendationsOut, SimilarProductsOut, TrendingProductsOut
from services import recommendation_service as recs

router = APIRouter(tags=["Recommendations"])


@router.get("/recommendations/{user_id}", response_model=RecommendationsOut)
def get_recommendations(
    user_id: int,
    limit: int = Query(8, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.id != user_id and current_user.role not in ("admin", "staff"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own recommendations",
        )

    has_history = db.query(ProductView).filter(ProductView.user_id == user_id).first() is not None

    products = recs.get_personalized_recommendations(db, user_id, limit=limit)
    source = "personalized" if has_history else "trending"
    return RecommendationsOut(source=source, products=products)


@router.get("/products/{product_id}/similar", response_model=SimilarProductsOut)
def get_similar_products(
    product_id: int,
    limit: int = Query(8, ge=1, le=50),
    db: Session = Depends(get_db),
):
    products = recs.get_similar_products(db, product_id, limit=limit)
    return SimilarProductsOut(product_id=product_id, products=products)


@router.get("/products/trending", response_model=TrendingProductsOut)
def get_trending(
    limit: int = Query(8, ge=1, le=50),
    db: Session = Depends(get_db),
):
    products = recs.get_trending_products(db, limit=limit)
    return TrendingProductsOut(products=products)