import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { listMyOrders } from "../api/orders";

const STATUS_LABELS = {
  pending: "Pending",
  paid: "Paid",
  shipped: "Shipped",
  delivered: "Delivered",
  cancelled: "Cancelled",
};

export default function Orders() {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    listMyOrders()
      .then(setOrders)
      .catch(() => setError("Could not load your orders."))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="container" style={{ padding: "3rem 0" }}>Loading your orders...</div>;

  return (
    <section className="section">
      <div className="container">
        <header className="section-header">
          <p className="section-label">Order History</p>
          <h2>Your Orders</h2>
        </header>

        {error && <p className="auth-error" role="alert">{error}</p>}

        {orders.length === 0 ? (
          <p>
            No orders yet. <Link to="/products">Start shopping</Link>.
          </p>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
            {orders.map((order) => (
              <div key={order.id} className="auth-card" style={{ padding: "1.25rem 1.5rem" }}>
                <div style={{ display: "flex", justifyContent: "space-between", flexWrap: "wrap", gap: "0.5rem", marginBottom: "0.75rem" }}>
                  <strong>Order #{order.id}</strong>
                  <div style={{ display: "flex", gap: "0.5rem" }}>
                    <span className="badge badge-accent">{STATUS_LABELS[order.order_status] || order.order_status}</span>
                    <span className="badge">{STATUS_LABELS[order.payment_status] || order.payment_status}</span>
                  </div>
                </div>

                <ul style={{ margin: "0 0 0.75rem", paddingLeft: "1.1rem" }}>
                  {order.items.map((item) => (
                    <li key={item.id}>
                      {item.product_name} × {item.quantity} — ₹{Number(item.line_total).toFixed(2)}
                    </li>
                  ))}
                </ul>

                <div style={{ display: "flex", justifyContent: "space-between", fontWeight: 700 }}>
                  <span>Total</span>
                  <span>₹{Number(order.total).toFixed(2)}</span>
                </div>
                <p style={{ opacity: 0.7, margin: "0.25rem 0 0", fontSize: "0.85rem" }}>
                  Placed {new Date(order.created_at).toLocaleString()}
                  {order.payment?.transaction_id && ` · Stripe ref: ${order.payment.transaction_id}`}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
