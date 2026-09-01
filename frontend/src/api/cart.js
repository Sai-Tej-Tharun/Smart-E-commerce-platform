import apiClient from "./client";

// All three now return the full CartOut shape:
// { items: [{id, product_id, product_name, unit_price, quantity, item_total}],
//   total_items, subtotal, tax_rate, tax, grand_total }
// so the frontend never has to total up prices itself.

export const getCart = () => apiClient.get("/cart").then((r) => r.data);

export const addToCart = ({ product_id, quantity }) =>
  apiClient.post("/cart/add", { product_id, quantity }).then((r) => r.data);

export const updateCartItem = ({ item_id, quantity }) =>
  apiClient.put("/cart/update", { item_id, quantity }).then((r) => r.data);

export const removeFromCart = (itemId) =>
  apiClient.delete(`/cart/remove/${itemId}`).then((r) => r.data);
