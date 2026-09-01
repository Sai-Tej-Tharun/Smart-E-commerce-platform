import { useState } from "react";
import { useNotifications } from "../context/NotificationContext";

const TYPE_LABELS = {
  order_confirmed: "Order Confirmed",
  payment_successful: "Payment Successful",
  payment_failed: "Payment Failed",
  order_shipped: "Order Shipped",
  order_delivered: "Order Delivered",
};

export default function NotificationBell() {
  const { notifications, unreadCount, markRead } = useNotifications();
  const [open, setOpen] = useState(false);

  const handleToggle = () => setOpen((prev) => !prev);

  const handleItemClick = (notification) => {
    if (!notification.read_status && !String(notification.id).startsWith("live-")) {
      markRead(notification.id);
    } else if (!notification.read_status) {
      markRead(); // live (WebSocket-only) items have no real DB id yet — mark everything read
    }
  };

  return (
    <div style={{ position: "relative" }}>
      <button
        type="button"
        className="nav-ctrl-btn"
        aria-label={`Notifications${unreadCount > 0 ? ` (${unreadCount} unread)` : ""}`}
        onClick={handleToggle}
        style={{ position: "relative" }}
      >
        🔔
        {unreadCount > 0 && (
          <span
            style={{
              position: "absolute",
              top: -4,
              right: -4,
              background: "var(--color-accent, #d94f4f)",
              color: "#fff",
              borderRadius: "999px",
              fontSize: "0.65rem",
              minWidth: 16,
              height: 16,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              padding: "0 4px",
            }}
          >
            {unreadCount > 9 ? "9+" : unreadCount}
          </span>
        )}
      </button>

      {open && (
        <div
          className="auth-card"
          style={{
            position: "absolute",
            right: 0,
            top: "calc(100% + 8px)",
            width: 320,
            maxHeight: 400,
            overflowY: "auto",
            zIndex: 50,
            padding: "0.75rem",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.5rem" }}>
            <strong>Notifications</strong>
            {unreadCount > 0 && (
              <button type="button" className="footer-link" style={{ fontSize: "0.8rem" }} onClick={() => markRead()}>
                Mark all read
              </button>
            )}
          </div>

          {notifications.length === 0 ? (
            <p style={{ fontSize: "0.9rem", opacity: 0.7 }}>No notifications yet.</p>
          ) : (
            <ul style={{ listStyle: "none", margin: 0, padding: 0, display: "flex", flexDirection: "column", gap: "0.5rem" }}>
              {notifications.map((n) => (
                <li
                  key={n.id}
                  onClick={() => handleItemClick(n)}
                  style={{
                    padding: "0.5rem",
                    borderRadius: 8,
                    background: n.read_status ? "transparent" : "var(--bg-section-alt, #f5f0e8)",
                    cursor: "pointer",
                    fontSize: "0.85rem",
                  }}
                >
                  <div style={{ fontWeight: 600 }}>{TYPE_LABELS[n.type] || n.type}</div>
                  <div>{n.message}</div>
                  <div style={{ opacity: 0.6, fontSize: "0.75rem" }}>{new Date(n.timestamp).toLocaleString()}</div>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}