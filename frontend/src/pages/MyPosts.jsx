import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { listMyPosts } from "../api/posts";

const BADGE = {
  draft: { label: "Draft", bg: "#e5e7eb", color: "#374151" },
  scheduled: { label: "Scheduled", bg: "#fef3c7", color: "#92400e" },
  published: { label: "Published", bg: "#d1fae5", color: "#065f46" },
};

const fmt = (iso) => (iso ? new Date(iso).toLocaleString() : "");

export default function MyPosts() {
  const [posts, setPosts] = useState([]);
  const [filter, setFilter] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    setLoading(true);
    setError("");
    listMyPosts(filter)
      .then(setPosts)
      .catch(() => setError("Could not load your posts."))
      .finally(() => setLoading(false));
  }, [filter]);

  return (
    <section className="section">
      <div className="container">
        <header className="section-header">
          <p className="section-label">Blog</p>
          <h2>My Posts</h2>
        </header>

        <div style={{ display: "flex", gap: "0.5rem", marginBottom: "1.5rem", flexWrap: "wrap" }}>
          {[["", "All"], ["draft", "Drafts"], ["scheduled", "Scheduled"], ["published", "Published"]].map(([val, label]) => (
            <button
              key={val || "all"}
              type="button"
              className="nav-btn nav-btn--login"
              style={{ opacity: filter === val ? 1 : 0.6 }}
              onClick={() => setFilter(val)}
            >
              {label}
            </button>
          ))}
        </div>

        {error && <p className="auth-error" role="alert">{error}</p>}

        {loading ? (
          <p>Loading...</p>
        ) : posts.length === 0 ? (
          <p>No posts here yet.</p>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
            {posts.map((post) => {
              const badge = BADGE[post.status] || BADGE.published;
              return (
                <div key={post.id} className="auth-card" style={{ padding: "1.25rem 1.5rem" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", gap: "1rem", alignItems: "start" }}>
                    <h3 style={{ margin: "0 0 0.4rem" }}>{post.title}</h3>
                    <span
                      style={{
                        background: badge.bg,
                        color: badge.color,
                        padding: "0.15rem 0.6rem",
                        borderRadius: "999px",
                        fontSize: "0.75rem",
                        fontWeight: 600,
                        whiteSpace: "nowrap",
                      }}
                    >
                      {badge.label}
                    </span>
                  </div>

                  <p style={{ margin: "0 0 0.6rem", fontSize: "0.85rem", opacity: 0.65 }}>
                    {post.status === "scheduled" && `Goes live ${fmt(post.scheduled_at)}`}
                    {post.status === "published" && `Published ${fmt(post.published_at)}`}
                    {post.status === "draft" && "Not published"}
                  </p>

                  <div style={{ display: "flex", gap: "1rem" }}>
                    <Link to={`/posts/${post.id}/edit`}>Edit</Link>
                    {post.status === "published" && <Link to={`/posts/${post.id}`}>View</Link>}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </section>
  );
}