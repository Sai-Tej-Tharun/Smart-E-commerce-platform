import apiClient from "./client";

// Matches fastapi_backend/schemas/dashboard.py's DashboardOut exactly:
// { totals: { total_posts, total_comments_made, total_likes_received, total_views },
//   posts: [{ post_id, title, likes, comments, views, created_at }] }
export const getDashboard = () => apiClient.get("/user/dashboard").then((r) => r.data);