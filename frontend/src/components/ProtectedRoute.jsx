import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

// Wrap any page that requires login (and optionally a specific role).
// Usage: <ProtectedRoute requireRole="admin"><AdminProducts /></ProtectedRoute>
export default function ProtectedRoute({ children, requireRole }) {
  const { isAuthenticated, loading, user } = useAuth();
  const location = useLocation();

  if (loading) {
    return <div className="page-loading">Loading...</div>;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (requireRole && user?.role !== requireRole) {
    return (
      <div className="container" style={{ padding: "4rem 0", textAlign: "center" }}>
        <h2>403 — Forbidden</h2>
        <p>This page is restricted to the "{requireRole}" role. Your role is "{user?.role}".</p>
      </div>
    );
  }

  return children;
}
