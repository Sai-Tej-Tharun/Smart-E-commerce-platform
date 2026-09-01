import apiClient from "./client";

export const listNotifications = () => apiClient.get("/notifications").then((r) => r.data);

// Omit notificationId to mark every notification read in one call.
export const markNotificationsRead = (notificationId) =>
  apiClient.post("/notifications/read", notificationId ? { notification_id: notificationId } : {}).then((r) => r.data);