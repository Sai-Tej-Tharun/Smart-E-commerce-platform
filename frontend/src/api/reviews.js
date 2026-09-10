import apiClient from "./client";

// Response shape: {average_rating, total_reviews, reviews: [...]}
// sort: "top" (default, highest rated first) or "newest"
export const getProductReviews = (productId, sort = "top") =>
  apiClient.get(`/products/${productId}/reviews`, { params: { sort } }).then((r) => r.data);

// Starts as "pending" — only visible on the product page once an admin
// approves it (see django_admin/storefront/admin.py's ReviewAdmin).
export const submitReview = ({ product_id, rating, comment }) =>
  apiClient.post("/reviews", { product_id, rating, comment: comment || null }).then((r) => r.data);