import apiClient from "./client";

export const listMyOrders = () => apiClient.get("/orders").then((r) => r.data);

export const getOrder = (id) => apiClient.get(`/orders/${id}`).then((r) => r.data);
