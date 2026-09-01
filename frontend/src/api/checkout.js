import apiClient from "./client";

// POST /checkout turns the current cart into an Order + a Stripe Checkout
// Session, and returns { order, checkout_url, session_id }. The frontend's
// only job after that is to redirect the browser to checkout_url — Stripe
// hosts the actual payment form.
export const startCheckout = () => apiClient.post("/checkout").then((r) => r.data);
