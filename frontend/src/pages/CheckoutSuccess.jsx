import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { listMyOrders } from "../api/orders";

// Stripe redirects here after a successful payment (see success_url in
// fastapi_backend/routes/checkout.py). The actual order-paid update
// happens server-side via the Stripe webhook, which can take a second or
// two to arrive — so this page polls GET /orders briefly rather than
// assuming the order is already marked paid the instant we land here.
export default function CheckoutSuccess() {
  const [searchParams] = useSearchParams();
  const sessionId = searchParams.get("session_id");
  const [order, setOrder] = useState(null);
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    let attempts = 0;
    let cancelled = false;

    const poll = async () => {
      try {
        const orders = await listMyOrders();
        const match = orders.find((o) => o.payment?.transaction_id === sessionId) || orders[0];
        if (!cancelled) {
          setOrder(match || null);
          if (match?.order_status === "paid" || attempts >= 5) {
            setChecking(false);
            return;
          }
        }
      } catch {
        // fall through and retry
      }
      attempts += 1;
      if (attempts < 5 && !cancelled) {
        setTimeout(poll, 1500);
      } else if (!cancelled) {
        setChecking(false);
      }
    };

    poll();
    return () => {
      cancelled = true;
    };
  }, [sessionId]);

  return (
    <section className="section">
      <div className="container" style={{ maxWidth: 560, textAlign: "center" }}>
        <p className="section-label">Checkout</p>
        <h2>{order?.order_status === "paid" ? "Payment successful 🎉" : "Confirming your payment..."}</h2>

        {checking && order?.order_status !== "paid" && (
          <p>This usually takes a couple of seconds while Stripe confirms the payment.</p>
        )}

        {order && (
          <div className="auth-card" style={{ textAlign: "left", marginTop: "1.5rem" }}>
            <p><strong>Order #{order.id}</strong></p>
            <p>Status: {order.order_status} / payment: {order.payment_status}</p>
            <p>Total: ₹{Number(order.total).toFixed(2)}</p>
          </div>
        )}

        <div style={{ marginTop: "1.5rem", display: "flex", gap: "1rem", justifyContent: "center" }}>
          <Link to="/orders" className="btn btn-primary">View My Orders</Link>
          <Link to="/products" className="nav-btn nav-btn--login">Continue Shopping</Link>
        </div>
      </div>
    </section>
  );
}
