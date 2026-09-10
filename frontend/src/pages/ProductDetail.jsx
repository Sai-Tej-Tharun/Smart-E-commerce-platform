import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { getProduct } from "../api/products";
import { addToCart } from "../api/cart";
import { getProductReviews, submitReview } from "../api/reviews";
import { getSimilarProducts } from "../api/recommendations";
import { useAuth } from "../context/AuthContext";
import StarRating from "../components/StarRating";
import RecommendationsSection from "../components/RecommendationsSection";

// NEW — Reviews & Ratings milestone. Its own component so the review
// form's local state (rating/comment/submitting/error) doesn't clutter
// the parent page, and so submitting can just tell the parent "a review
// was submitted" without owning the review list itself.
function WriteReviewForm({ productId, onSubmitted }) {
  const [rating, setRating] = useState(5);
  const [comment, setComment] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      await submitReview({ product_id: productId, rating, comment });
      setSuccess(true);
      onSubmitted?.();
    } catch (err) {
      // Covers both backend rules: no completed order for this product
      // (403), or already reviewed (400) — see fastapi_backend/routes/reviews.py.
      setError(err?.response?.data?.detail || "Could not submit your review.");
    } finally {
      setSubmitting(false);
    }
  };

  if (success) {
    return <p className="auth-error" role="status">Thanks! Your review has been submitted and will appear once approved.</p>;
  }

  return (
    <form onSubmit={handleSubmit} className="auth-form" style={{ maxWidth: 480 }}>
      <div className="auth-field">
        <label className="auth-label" htmlFor="rating">Your rating</label>
        <select id="rating" className="auth-input" value={rating} onChange={(e) => setRating(Number(e.target.value))}>
          {[5, 4, 3, 2, 1].map((n) => (
            <option key={n} value={n}>{n} star{n === 1 ? "" : "s"}</option>
          ))}
        </select>
      </div>
      <div className="auth-field">
        <label className="auth-label" htmlFor="comment">Comment (optional)</label>
        <textarea
          id="comment"
          className="auth-input"
          rows={3}
          value={comment}
          onChange={(e) => setComment(e.target.value)}
          placeholder="What did you think?"
        />
      </div>
      {error && <span className="auth-error" role="alert">{error}</span>}
      <button type="submit" className="btn btn-primary" disabled={submitting}>
        {submitting ? "Submitting..." : "Submit Review"}
      </button>
    </form>
  );
}

export default function ProductDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();
  const [product, setProduct] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [adding, setAdding] = useState(false);
  const [quantity, setQuantity] = useState(1);

  // NEW — Reviews & Ratings milestone
  const [reviewData, setReviewData] = useState(null);
  const [reviewSort, setReviewSort] = useState("top");
  const [showReviewForm, setShowReviewForm] = useState(false);

  // NEW — Recommendation System milestone
  const [similarProducts, setSimilarProducts] = useState([]);
  const [similarAddingId, setSimilarAddingId] = useState(null);

  useEffect(() => {
    setLoading(true);
    getProduct(id)
      .then(setProduct)
      .catch(() => setError("Product not found."))
      .finally(() => setLoading(false));
  }, [id]);

  const loadReviews = () => {
    getProductReviews(id, reviewSort).then(setReviewData);
  };

  useEffect(() => {
    loadReviews();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id, reviewSort]);

  // NEW — Recommendation System milestone: "Similar Products"
  useEffect(() => {
    getSimilarProducts(id, 4)
      .then((data) => setSimilarProducts(data.products))
      .catch(() => setSimilarProducts([]));
  }, [id]);

  const handleAddSimilarToCart = async (similarProduct) => {
    if (!isAuthenticated) {
      setMessage("Please log in to add items to your cart.");
      return;
    }
    setSimilarAddingId(similarProduct.id);
    try {
      await addToCart({ product_id: similarProduct.id, quantity: 1 });
      setMessage(`Added "${similarProduct.name}" to your cart.`);
    } catch {
      setMessage("Could not add that item to your cart.");
    } finally {
      setSimilarAddingId(null);
    }
  };

  const handleAddToCart = async () => {
    if (!isAuthenticated) {
      setMessage("Please log in to add items to your cart.");
      return;
    }
    setAdding(true);
    try {
      await addToCart({ product_id: product.id, quantity });
      setMessage(`Added ${quantity} × "${product.name}" to your cart.`);
    } catch {
      setMessage("Could not add that item to your cart.");
    } finally {
      setAdding(false);
    }
  };

  const handleReviewSubmitted = () => {
    setShowReviewForm(false);
    loadReviews(); // won't show the new one yet (still pending), but keeps the list fresh
  };

  if (loading) return <div className="container" style={{ padding: "3rem 0" }}>Loading...</div>;
  if (error || !product) {
    return (
      <div className="container" style={{ padding: "3rem 0" }}>
        <p className="auth-error">{error || "Product not found."}</p>
        <button className="btn btn-primary" onClick={() => navigate("/products")}>Back to Products</button>
      </div>
    );
  }

  const image = product.images?.[0];
  
  return (
    <>
    <section className="section">
      <div className="container">
        <div className="grid grid-2" style={{ gap: "2.5rem", alignItems: "start" }}>
          <div className="product-card__image" style={{ borderRadius: "var(--radius-lg, 12px)", overflow: "hidden" }}>
            {image ? (
              <img src={image} alt={product.name} style={{ width: "100%", height: "auto", display: "block" }} />
            ) : (
              <div className="product-card__image-placeholder" style={{ minHeight: 320 }} aria-hidden="true" />
            )}
          </div>

          <div>
            {product.category && <p className="product-card__category">{product.category}</p>}
            <h1>{product.name}</h1>
            <div style={{ margin: "0.5rem 0" }}>
              <StarRating value={product.average_rating} count={product.review_count} size="1.1rem" />
            </div>
            <p className="product-card__price-current" style={{ fontSize: "var(--text-3xl)" }}>
              ₹{Number(product.price).toFixed(2)}
            </p>
            {product.description && <p>{product.description}</p>}
            <p>
              <strong>{product.stock > 0 ? `${product.stock} in stock` : "Out of stock"}</strong>
            </p>

            <div style={{ display: "flex", gap: "0.75rem", alignItems: "center", margin: "1.5rem 0" }}>
              <label className="auth-label" htmlFor="qty">Qty</label>
              <input
                id="qty"
                type="number"
                min="1"
                max={product.stock || 1}
                value={quantity}
                onChange={(e) => setQuantity(Math.max(1, Number(e.target.value)))}
                className="auth-input"
                style={{ width: 90 }}
              />
            </div>

            {message && <p className="auth-error" role="status">{message}</p>}

            <button
              className="btn btn-primary"
              disabled={product.stock === 0 || adding}
              onClick={handleAddToCart}
            >
              {product.stock === 0 ? "Out of stock" : adding ? "Adding..." : "Add to Cart"}
            </button>
          </div>
        </div>

        {/* NEW — Reviews & Ratings milestone */}
        <div style={{ marginTop: "3rem", borderTop: "1px solid var(--color-gray-light)", paddingTop: "2rem" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "1rem" }}>
            <h2 style={{ margin: 0 }}>
              Reviews {reviewData && reviewData.total_reviews > 0 ? `(${reviewData.total_reviews})` : ""}
            </h2>
            <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
              <label className="auth-label" htmlFor="review-sort" style={{ margin: 0 }}>Sort by</label>
              <select
                id="review-sort"
                className="auth-input"
                style={{ width: "auto" }}
                value={reviewSort}
                onChange={(e) => setReviewSort(e.target.value)}
              >
                <option value="top">Top reviews</option>
                <option value="newest">Newest</option>
              </select>
            </div>
          </div>

          {isAuthenticated && !showReviewForm && (
            <button className="nav-btn nav-btn--login" style={{ margin: "1rem 0" }} onClick={() => setShowReviewForm(true)}>
              Write a Review
            </button>
          )}
          {!isAuthenticated && <p style={{ margin: "1rem 0", opacity: 0.7 }}>Log in to write a review.</p>}

          {showReviewForm && (
            <div style={{ margin: "1rem 0" }}>
              <WriteReviewForm productId={product.id} onSubmitted={handleReviewSubmitted} />
            </div>
          )}

          {!reviewData ? (
            <p>Loading reviews...</p>
          ) : reviewData.reviews.length === 0 ? (
            <p style={{ opacity: 0.7 }}>No reviews yet — be the first to leave one.</p>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: "1.25rem", marginTop: "1.5rem" }}>
              {reviewData.reviews.map((review) => (
                <div key={review.id} className="auth-card" style={{ padding: "1rem 1.25rem" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "0.5rem" }}>
                    <StarRating value={review.rating} size="0.95rem" />
                    <span style={{ fontSize: "0.85rem", opacity: 0.7 }}>
                      {review.user_name || "Anonymous"} · {new Date(review.created_at).toLocaleDateString()}
                    </span>
                  </div>
                  {review.comment && <p style={{ margin: "0.5rem 0 0" }}>{review.comment}</p>}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </section>

    {/* NEW — Recommendation System milestone */}
    <RecommendationsSection
      title="Similar Products"
      subtitle="You May Also Like"
      products={similarProducts}
      onAddToCart={handleAddSimilarToCart}
      addingId={similarAddingId}
    />
    </>
  );
}