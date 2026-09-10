import apiClient from "./client";

// GET /recommendations/{user_id}
// Response: { source: "personalized" | "trending", products: [...] }
// `source` is "trending" when the user has no browsing/purchase history
// yet (cold start) — the UI can use it to adjust the section's copy.
export const getRecommendationsForUser = (userId, limit = 8) =>
  apiClient.get(`/recommendations/${userId}`, { params: { limit } }).then((r) => r.data);

// GET /products/{id}/similar
// Response: { product_id, products: [...] }
export const getSimilarProducts = (productId, limit = 8) =>
  apiClient.get(`/products/${productId}/similar`, { params: { limit } }).then((r) => r.data);

// GET /products/trending
// Response: { products: [...] }
export const getTrendingProducts = (limit = 8) =>
  apiClient.get("/products/trending", { params: { limit } }).then((r) => r.data);