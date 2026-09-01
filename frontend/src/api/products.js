import apiClient from "./client";

// filters: { category, min_price, max_price, in_stock, sort }
export const listProducts = (filters = {}) => {
  const params = {};
  if (filters.category) params.category = filters.category;
  if (filters.min_price !== undefined && filters.min_price !== "") params.min_price = filters.min_price;
  if (filters.max_price !== undefined && filters.max_price !== "") params.max_price = filters.max_price;
  if (filters.in_stock !== undefined && filters.in_stock !== "") params.in_stock = filters.in_stock;
  if (filters.sort) params.sort = filters.sort;
  return apiClient.get("/products", { params }).then((r) => r.data);
};

export const listProductsByCategory = (category, filters = {}) => {
  const params = {};
  if (filters.min_price !== undefined && filters.min_price !== "") params.min_price = filters.min_price;
  if (filters.max_price !== undefined && filters.max_price !== "") params.max_price = filters.max_price;
  if (filters.in_stock !== undefined && filters.in_stock !== "") params.in_stock = filters.in_stock;
  if (filters.sort) params.sort = filters.sort;
  return apiClient.get(`/products/category/${encodeURIComponent(category)}`, { params }).then((r) => r.data);
};

export const getProduct = (id) => apiClient.get(`/products/${id}`).then((r) => r.data);

export const createProduct = (payload) =>
  apiClient.post("/products", payload).then((r) => r.data);

export const updateProduct = (id, payload) =>
  apiClient.put(`/products/${id}`, payload).then((r) => r.data);

export const deleteProduct = (id) => apiClient.delete(`/products/${id}`);
