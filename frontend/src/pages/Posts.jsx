import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { listPosts } from "../api/posts";

export default function Posts() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);

  const load = () => {
    setLoading(true);
    setError("");
    listPosts({ page, limit: 10, search })
      .then(setData)
      .catch(() => setError("Could not load posts. Is the FastAPI backend running?"))
      .finally(() => setLoading(false));
  };

  useEffect(load, [page]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    setPage(1);
    // load() reruns via the page-change effect only if page actually changes;
    // if we were already on page 1, trigger it directly.
    if (page === 1) load();
  };

  return (
    <section className="section">
      <div className="container">
        <header className="section-header">
          <p className="section-label">Blog</p>
          <h2>All Posts</h2>
        </header>

        <form
          onSubmit={handleSearchSubmit}
          style={{ display: "flex", gap: "0.75rem", marginBottom: "2rem", maxWidth: "480px" }}
        >
          <div className="auth-field" style={{ margin: 0, flex: 1 }}>
            <label className="auth-label" htmlFor="postSearch">Search</label>
            <input
              id="postSearch"
              className="auth-input"
              placeholder="Search by title or content..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          <button type="submit" className="auth-submit" style={{ alignSelf: "end", width: "auto", padding: "0 1.25rem" }}>
            Search
          </button>
        </form>

        {error && <p className="auth-error" role="alert">{error}</p>}

        {loading ? (
          <p>Loading posts...</p>
        ) : !data || data.items.length === 0 ? (
          <p>No posts found.</p>
        ) : (
          <>
            <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
              {data.items.map((post) => (
                <Link
                  key={post.id}
                  to={`/posts/${post.id}`}
                  className="auth-card"
                  style={{ padding: "1.25rem 1.5rem", display: "block", textDecoration: "none", color: "inherit" }}
                >
                  <h3 style={{ margin: "0 0 0.4rem" }}>{post.title}</h3>
                  <p style={{ margin: "0 0 0.6rem", opacity: 0.75 }}>
                    {post.content.length > 160 ? `${post.content.slice(0, 160)}…` : post.content}
                  </p>
                  <p style={{ margin: 0, fontSize: "0.85rem", opacity: 0.6 }}>
                    By {post.author_name || "Unknown"} · {post.like_count} likes · {post.comment_count} comments · {post.views} views
                  </p>
                </Link>
              ))}
            </div>

            <div style={{ display: "flex", justifyContent: "center", gap: "1rem", alignItems: "center", marginTop: "2rem" }}>
              <button
                type="button"
                className="nav-btn nav-btn--login"
                disabled={page <= 1}
                onClick={() => setPage((p) => p - 1)}
              >
                Previous
              </button>
              <span>Page {data.page} of {data.total_pages || 1}</span>
              <button
                type="button"
                className="nav-btn nav-btn--login"
                disabled={page >= data.total_pages}
                onClick={() => setPage((p) => p + 1)}
              >
                Next
              </button>
            </div>
          </>
        )}
      </div>
    </section>
  );
}