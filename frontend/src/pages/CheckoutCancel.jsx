import { Link, useSearchParams } from "react-router-dom";

// Stripe redirects here if the customer backs out of the hosted payment
// page (see cancel_url in fastapi_backend/routes/checkout.py). The order
// stays in the database with order_status/payment_status still "pending"
// — nothing to clean up here, the customer can just try checking out again.
export default function CheckoutCancel() {
  const [searchParams] = useSearchParams();
  const orderId = searchParams.get("order_id");

  return (
    <section className="section">
      <div className="container" style={{ maxWidth: 560, textAlign: "center" }}>
        <p className="section-label">Checkout</p>
        <h2>Checkout cancelled</h2>
        <p>
          No payment was taken{orderId && ` (order #${orderId} is still pending)`}. Your cart is exactly as you left it.
        </p>
        <div style={{ marginTop: "1.5rem", display: "flex", gap: "1rem", justifyContent: "center" }}>
          <Link to="/cart" className="btn btn-primary">Back to Cart</Link>
          <Link to="/products" className="nav-btn nav-btn--login">Continue Shopping</Link>
        </div>
      </div>
    </section>
  );
}
