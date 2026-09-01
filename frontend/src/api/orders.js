import apiClient from "./client";

export const listMyOrders = () => apiClient.get("/orders").then((r) => r.data);

export const getOrder = (id) => apiClient.get(`/orders/${id}`).then((r) => r.data);

// NEW — Refund & Return milestone. Backend enforces "delivered only" and
// the 7-day window (see fastapi_backend/routes/orders.py); this just
// passes the reason/comment through.
export const requestReturn = (orderId, { reason, comment }) =>
  apiClient.post(`/orders/${orderId}/return`, { reason, comment: comment || null }).then((r) => r.data);