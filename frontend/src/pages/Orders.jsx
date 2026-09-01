import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { listMyOrders, requestReturn } from "../api/orders";

const STATUS_LABELS = {
  pending: "Pending",
  paid: "Paid",
  shipped: "Shipped",
  delivered: "Delivered",
  cancelled: "Cancelled",
  return_requested: "Return Requested", // NEW — Refund & Return milestone
};

const RETURN_REASONS = [
  "Item damaged or defective",
  "Wrong item received",
  "No longer needed",
  "Item not as described",
  "Other",
];

// One day, in milliseconds — used only for the optional "closes in N days"
// hint below; the backend (routes/orders.py) is the actual source of
// truth for whether a return is still allowed.
const ONE_DAY_MS = 24 * 60 * 60 * 1000;
const RETURN_WINDOW_DAYS = 7;

function daysRemaining(deliveredAt) {
  if (!deliveredAt) return null;
  const deadline = new Date(deliveredAt).getTime() + RETURN_WINDOW_DAYS * ONE_DAY_MS;
  return Math.ceil((deadline - Date.now()) / ONE_DAY_MS);
}

// NEW — Refund & Return milestone. A small inline form, shown under an
// order once "Request Return" is clicked. Kept as its own component so
// each order's form has independent state (open/closed, reason, etc.)
// without the parent Orders component tracking per-order form state.
function ReturnRequestForm({ order, onSuccess, onCancel }) {
  const [reason, setReason] = useState(RETURN_REASONS[0]);
  const [comment, setComment] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      await requestReturn(order.id, { reason, comment });
      onSuccess();
    } catch (err) {
      // Covers the backend's actual rules: not delivered, window expired,
      // or a request already exists — see fastapi_backend/routes/orders.py.
      setError(err?.response?.data?.detail || "Could not submit the return request.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="auth-form" style={{ marginTop: "0.75rem", paddingTop: "0.75rem", borderTop: "1px solid var(--color-gray-light)" }}>
      <div className="auth-field">
        <label className="auth-label" htmlFor={`reason-${order.id}`}>Reason for return</label>
        <select
          id={`reason-${order.id}`}
          className="auth-input"
          value={reason}
          onChange={(e) => setReason(e.target.value)}
        >
          {RETURN_REASONS.map((r) => (
            <option key={r} value={r}>{r}</option>
          ))}
        </select>
      </div>

      <div className="auth-field">
        <label className="auth-label" htmlFor={`comment-${order.id}`}>Additional details (optional)</label>
        <textarea
          id={`comment-${order.id}`}
          className="auth-input"
          rows={3}
          value={comment}
          onChange={(e) => setComment(e.target.value)}
          placeholder="Tell us more about the issue..."
        />
      </div>

      {error && <span className="auth-error" role="alert">{error}</span>}

      <div style={{ display: "flex", gap: "0.75rem" }}>
        <button type="submit" className="btn btn-primary" disabled={submitting}>
          {submitting ? "Submitting..." : "Submit Return Request"}
        </button>
        <button type="button" className="nav-btn nav-btn--login" onClick={onCancel} disabled={submitting}>
          Cancel
        </button>
      </div>
    </form>
  );
}

export default function Orders() {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [openReturnFormFor, setOpenReturnFormFor] = useState(null);
  const [returnMessage, setReturnMessage] = useState("");

  const load = () => {
    listMyOrders()
      .then(setOrders)
      .catch(() => setError("Could not load your orders."))
      .finally(() => setLoading(false));
  };

  useEffect(load, []);

  const handleReturnSuccess = () => {
    setOpenReturnFormFor(null);
    setReturnMessage("Your return request was submitted. We'll review it shortly.");
    load(); // refresh so the order shows its new "Return Requested" status
  };

  if (loading) return <div className="container" style={{ padding: "3rem 0" }}>Loading your orders...</div>;

  return (
    <section className="section">
      <div className="container">
        <header className="section-header">
          <p className="section-label">Order History</p>
          <h2>Your Orders</h2>
        </header>

        {error && <p className="auth-error" role="alert">{error}</p>}
        {returnMessage && <p className="auth-error" role="status" style={{ marginBottom: "1rem" }}>{returnMessage}</p>}

        {orders.length === 0 ? (
          <p>
            No orders yet. <Link to="/products">Start shopping</Link>.
          </p>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
            {orders.map((order) => {
              const remaining = daysRemaining(order.delivered_at);
              // NEW — Refund & Return milestone: only offer the button on
              // delivered orders. The backend is still the real gatekeeper
              // for the 7-day window and duplicate requests — this is
              // just about not showing the button somewhere it can't work.
              const canRequestReturn = order.order_status === "delivered";

              return (
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

                  {canRequestReturn && openReturnFormFor !== order.id && (
                    <div style={{ marginTop: "0.75rem" }}>
                      <button
                        type="button"
                        className="nav-btn nav-btn--login"
                        onClick={() => setOpenReturnFormFor(order.id)}
                      >
                        Request Return
                      </button>
                      {remaining !== null && (
                        <span style={{ marginLeft: "0.75rem", fontSize: "0.8rem", opacity: 0.7 }}>
                          {remaining > 0 ? `Return window closes in ${remaining} day${remaining === 1 ? "" : "s"}` : "Return window may have closed"}
                        </span>
                      )}
                    </div>
                  )}

                  {openReturnFormFor === order.id && (
                    <ReturnRequestForm
                      order={order}
                      onSuccess={handleReturnSuccess}
                      onCancel={() => setOpenReturnFormFor(null)}
                    />
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </section>
  );
}