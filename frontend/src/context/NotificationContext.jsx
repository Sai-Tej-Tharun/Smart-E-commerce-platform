import { createContext, useContext, useEffect, useRef, useState } from "react";
import { listNotifications, markNotificationsRead } from "../api/notifications";
import { tokenStore } from "../api/client";
import { useAuth } from "./AuthContext";

const NotificationContext = createContext(null);

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";
const WS_BASE_URL = API_BASE_URL.replace(/^http/, "ws");

export function NotificationProvider({ children }) {
  const { isAuthenticated } = useAuth();
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [cartBadge, setCartBadge] = useState(null); // {total_items, grand_total} from cart_updated events
  const [toast, setToast] = useState(null); // most recent real-time notification, shown briefly
  const socketRef = useRef(null);

  const refresh = async () => {
    try {
      const data = await listNotifications();
      setNotifications(data.notifications);
      setUnreadCount(data.unread_count);
    } catch {
      // not logged in yet, or backend unreachable — leave state as-is
    }
  };

  const markRead = async (notificationId) => {
    const data = await markNotificationsRead(notificationId);
    setNotifications(data.notifications);
    setUnreadCount(data.unread_count);
  };

  // Load the notification list once on login, then keep it live via WebSocket.
  useEffect(() => {
    if (!isAuthenticated) {
      setNotifications([]);
      setUnreadCount(0);
      setCartBadge(null);
      return;
    }
    refresh();
  }, [isAuthenticated]);

  // WS /ws/notifications?token=... — see fastapi_backend/routes/ws.py.
  // Browsers can't set a WebSocket Authorization header, so the JWT access
  // token goes in the query string instead.
  useEffect(() => {
    if (!isAuthenticated) {
      socketRef.current?.close();
      socketRef.current = null;
      return;
    }

    const token = tokenStore.getAccess();
    if (!token) return;

    const socket = new WebSocket(`${WS_BASE_URL}/ws/notifications?token=${encodeURIComponent(token)}`);
    socketRef.current = socket;

    socket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.event === "order_status_updated") {
        setUnreadCount((prev) => prev + 1);
        setNotifications((prev) => [
          { id: `live-${Date.now()}`, type: data.notification_type, message: data.message, read_status: false, timestamp: new Date().toISOString() },
          ...prev,
        ]);
        setToast(data.message);
        setTimeout(() => setToast((current) => (current === data.message ? null : current)), 5000);
      } else if (data.event === "cart_updated") {
        setCartBadge({ total_items: data.total_items, grand_total: data.grand_total });
      }
    };

    socket.onclose = () => {
      socketRef.current = null;
    };

    return () => socket.close();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAuthenticated]);

  return (
    <NotificationContext.Provider value={{ notifications, unreadCount, cartBadge, toast, refresh, markRead }}>
      {children}
    </NotificationContext.Provider>
  );
}

export function useNotifications() {
  const ctx = useContext(NotificationContext);
  if (!ctx) throw new Error("useNotifications must be used inside <NotificationProvider>");
  return ctx;
}