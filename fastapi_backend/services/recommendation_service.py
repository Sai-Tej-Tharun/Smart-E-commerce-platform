"""
services/recommendation_service.py
------------------------------------
NEW (Recommendation System milestone).

Recommendation engine for the Smart E-Commerce Platform. Combines the five
signals called out in the spec:

  1. Browsing history  -> models.product_view.ProductView, per user
  2. Past purchases    -> models.order.Order / OrderItem, per user
  3. Product similarity -> shared category + name/description keyword
                            overlap + comparable price (no ML dependency)
  4. Most viewed items  -> ProductView counts across all users
  5. Top-rated products -> models.review.Review (approved only)

This module is pure logic — it never touches the request/response cycle.
routes/recommendations.py calls these functions and serializes the result.
Keeping it here (rather than in the routes file) means the scoring logic
can be unit-tested or reused (e.g. from a future batch/offline job)
without dragging in FastAPI.
"""

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from models.order import Order, OrderItem, OrderStatus
from models.product import Product
from models.product_view import ProductView
from models.review import Review, ReviewStatus

# Orders this far along count as a genuine "purchase" signal — the same
# definition routes/reviews.py already uses for "did this user actually
# receive the product".
_PURCHASED_STATUSES = (
    OrderStatus.PAID,
    OrderStatus.SHIPPED,
    OrderStatus.DELIVERED,
    OrderStatus.RETURN_REQUESTED,
    OrderStatus.RETURNED,
)

# Only views from the last N days count toward "trending", so the section
# reflects what's hot right now rather than what was hot at store launch.
TRENDING_WINDOW_DAYS = 14

# An average rating isn't trusted for "top rated" until a product has at
# least this many approved reviews — stops one 5-star review from
# outranking a product with 40 reviews averaging 4.7.
MIN_REVIEWS_FOR_TOP_RATED = 2

DEFAULT_LIMIT = 8


def _attach_review_stats(products: List[Product], db: Session) -> List[Product]:
    """Mirrors routes/products.py's _attach_review_stats. Duplicated (not
    imported) so this service has no dependency on the routes package —
    average_rating/review_count aren't real columns, just instance
    attributes set here for ProductOut/RecommendedProductOut to read."""
    if not products:
        return products
    ids = [p.id for p in products]
    stats = (
        db.query(Review.product_id, func.avg(Review.rating).label("avg"), func.count(Review.id).label("cnt"))
        .filter(Review.product_id.in_(ids), Review.status == ReviewStatus.APPROVED)
        .group_by(Review.product_id)
        .all()
    )
    stats_by_id = {row.product_id: (float(row.avg), row.cnt) for row in stats}
    for p in products:
        avg, cnt = stats_by_id.get(p.id, (None, 0))
        p.average_rating = round(avg, 2) if avg is not None else None
        p.review_count = cnt
    return products


def _tokenize(text: Optional[str]) -> set:
    if not text:
        return set()
    return {w.strip(".,!?()[]").lower() for w in text.split() if len(w) > 2}


def _similarity_score(a: Product, b: Product) -> float:
    """Lightweight content-based similarity — deliberately dependency-free
    (no numpy/sklearn in requirements.txt) so it runs anywhere the rest of
    the app already runs:
      +3.0        same category (exact, case-insensitive)
      +up to 2.0  Jaccard overlap of name+description keywords
      +up to 1.0  price within 30% of each other (closer = higher)
    """
    score = 0.0
    if a.category and b.category and a.category.lower() == b.category.lower():
        score += 3.0

    tokens_a = _tokenize(a.name) | _tokenize(a.description)
    tokens_b = _tokenize(b.name) | _tokenize(b.description)
    if tokens_a and tokens_b:
        overlap = len(tokens_a & tokens_b) / len(tokens_a | tokens_b)
        score += overlap * 2.0

    if a.price and b.price:
        hi, lo = max(float(a.price), float(b.price)), min(float(a.price), float(b.price))
        diff_ratio = (hi - lo) / hi if hi else 1.0
        if diff_ratio <= 0.3:
            score += (1 - diff_ratio)

    return score


def get_similar_products(db: Session, product_id: int, limit: int = DEFAULT_LIMIT) -> List[Product]:
    """Powers GET /products/{id}/similar — "Similar Products" / "You May
    Also Like" on the product detail page."""
    target = db.query(Product).filter(Product.id == product_id).first()
    if not target:
        return []

    candidates = db.query(Product).filter(Product.id != product_id).all()
    scored = [(p, _similarity_score(target, p)) for p in candidates]
    scored = [pair for pair in scored if pair[1] > 0]
    scored.sort(key=lambda pair: pair[1], reverse=True)

    top = [p for p, _ in scored[:limit]]
    return _attach_review_stats(top, db)


def get_most_viewed_products(db: Session, limit: int = DEFAULT_LIMIT, days: Optional[int] = None) -> List[Product]:
    query = db.query(ProductView.product_id, func.count(ProductView.id).label("views"))
    if days is not None:
        since = datetime.utcnow() - timedelta(days=days)
        query = query.filter(ProductView.viewed_at >= since)
    rows = query.group_by(ProductView.product_id).order_by(func.count(ProductView.id).desc()).limit(limit).all()

    if not rows:
        return []
    ids_in_order = [row.product_id for row in rows]
    products_by_id = {p.id: p for p in db.query(Product).filter(Product.id.in_(ids_in_order)).all()}
    ordered = [products_by_id[i] for i in ids_in_order if i in products_by_id]
    return _attach_review_stats(ordered, db)


def get_top_rated_products(db: Session, limit: int = DEFAULT_LIMIT) -> List[Product]:
    rows = (
        db.query(Review.product_id, func.avg(Review.rating).label("avg"), func.count(Review.id).label("cnt"))
        .filter(Review.status == ReviewStatus.APPROVED)
        .group_by(Review.product_id)
        .having(func.count(Review.id) >= MIN_REVIEWS_FOR_TOP_RATED)
        .order_by(func.avg(Review.rating).desc(), func.count(Review.id).desc())
        .limit(limit)
        .all()
    )
    if not rows:
        return []
    ids_in_order = [row.product_id for row in rows]
    products_by_id = {p.id: p for p in db.query(Product).filter(Product.id.in_(ids_in_order)).all()}
    ordered = [products_by_id[i] for i in ids_in_order if i in products_by_id]
    return _attach_review_stats(ordered, db)


def get_trending_products(db: Session, limit: int = DEFAULT_LIMIT) -> List[Product]:
    """Powers GET /products/trending. 'Trending' = most viewed in the last
    TRENDING_WINDOW_DAYS. Falls back to top-rated, then newest, if there
    isn't enough recent view data yet (e.g. a freshly seeded store), so
    the endpoint never just returns an empty list."""
    trending = get_most_viewed_products(db, limit=limit, days=TRENDING_WINDOW_DAYS)
    if len(trending) >= limit:
        return trending

    seen_ids = {p.id for p in trending}

    for p in get_top_rated_products(db, limit=limit):
        if len(trending) >= limit:
            break
        if p.id not in seen_ids:
            trending.append(p)
            seen_ids.add(p.id)

    if len(trending) < limit:
        newest = _attach_review_stats(
            db.query(Product).order_by(Product.created_at.desc()).limit(limit).all(), db
        )
        for p in newest:
            if len(trending) >= limit:
                break
            if p.id not in seen_ids:
                trending.append(p)
                seen_ids.add(p.id)

    return trending[:limit]


def get_personalized_recommendations(db: Session, user_id: int, limit: int = DEFAULT_LIMIT) -> List[Product]:
    """Powers GET /recommendations/{user_id} — "Recommended For You".

    Seeds a candidate score from what the user has viewed (weight capped
    per-product so one obsessively-refreshed item can't dominate) and what
    they've purchased (weighted higher — a purchase is a stronger taste
    signal than a view). Every other product then earns
    seed_weight * similarity_to_seed, summed across all seeds. Already
    -purchased products are excluded from the result — no point
    recommending what they already own.

    Cold start (brand-new user, no views/orders yet): falls back to
    storewide trending products so the section is never empty.
    """
    viewed_rows = (
        db.query(ProductView.product_id, func.count(ProductView.id).label("cnt"))
        .filter(ProductView.user_id == user_id)
        .group_by(ProductView.product_id)
        .all()
    )
    purchased_ids = {
        row.product_id
        for row in (
            db.query(OrderItem.product_id)
            .join(Order, Order.id == OrderItem.order_id)
            .filter(Order.user_id == user_id, Order.order_status.in_(_PURCHASED_STATUSES))
            .distinct()
        )
    }

    seed_weights: Dict[int, float] = defaultdict(float)
    for row in viewed_rows:
        seed_weights[row.product_id] += min(row.cnt, 5) * 1.0
    for pid in purchased_ids:
        seed_weights[pid] += 2.0

    if not seed_weights:
        return get_trending_products(db, limit=limit)

    all_products = db.query(Product).filter(~Product.id.in_(purchased_ids)).all() if purchased_ids else db.query(Product).all()
    seed_products_by_id = {p.id: p for p in db.query(Product).filter(Product.id.in_(seed_weights.keys())).all()}

    scores: Dict[int, float] = defaultdict(float)
    for candidate in all_products:
        for seed_id, weight in seed_weights.items():
            seed_product = seed_products_by_id.get(seed_id)
            if not seed_product or seed_product.id == candidate.id:
                continue
            scores[candidate.id] += weight * _similarity_score(seed_product, candidate)
        # Small boost toward generally popular products so ties break
        # toward things other shoppers already like.
        scores[candidate.id] += candidate.popularity * 0.01

    ranked_ids = [pid for pid, score in sorted(scores.items(), key=lambda kv: kv[1], reverse=True) if score > 0]

    if len(ranked_ids) < limit:
        # Sparse catalog/history — top up with trending products not
        # already selected or already purchased.
        for p in get_trending_products(db, limit=limit):
            if p.id not in ranked_ids and p.id not in purchased_ids:
                ranked_ids.append(p.id)
            if len(ranked_ids) >= limit:
                break

    products_by_id = {p.id: p for p in all_products}
    ordered = [products_by_id[pid] for pid in ranked_ids[:limit] if pid in products_by_id]
    return _attach_review_stats(ordered, db)


def record_product_view(db: Session, product_id: int, user_id: Optional[int]) -> None:
    """Fire-and-forget browsing-history log, called from GET /products/{id}
    in routes/products.py on every product page view. Never raises — a
    failed view log should never break the product page itself."""
    try:
        db.add(ProductView(product_id=product_id, user_id=user_id))
        db.commit()
    except Exception:
        db.rollback()