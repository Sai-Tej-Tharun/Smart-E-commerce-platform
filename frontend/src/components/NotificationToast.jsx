import { useNotifications } from "../context/NotificationContext";

// A brief, dismissable popup shown the instant a WebSocket notification
// arrives — separate from the persistent bell dropdown (NotificationBell),
// this is the "real-time" part actually being visible without opening
// anything. Auto-clears itself after 5s (see NotificationContext).
export default function NotificationToast() {
  const { toast } = useNotifications();

  if (!toast) return null;

  return (
    <div
      role="status"
      style={{
        position: "fixed",
        bottom: "1.5rem",
        right: "1.5rem",
        maxWidth: 320,
        background: "var(--color-primary-dark, #2f3b2f)",
        color: "#fff",
        padding: "0.85rem 1.1rem",
        borderRadius: 10,
        boxShadow: "0 8px 24px rgba(0,0,0,0.2)",
        zIndex: 100,
        fontSize: "0.9rem",
      }}
    >
      🔔 {toast}
    </div>
  );
}