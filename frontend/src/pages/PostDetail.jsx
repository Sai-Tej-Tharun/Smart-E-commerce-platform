import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { getPost, listComments, addComment, likePost, unlikePost } from "../api/posts";

export default function PostDetail() {
  const { postId } = useParams();
  const { isAuthenticated } = useAuth();

  const [post, setPost] = useState(null);
  const [comments, setComments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [commentText, setCommentText] = useState("");
  const [commentSubmitting, setCommentSubmitting] = useState(false);
  const [commentError, setCommentError] = useState("");

  // The API doesn't report "did I already like this," so this starts false
  // and only reflects likes/unlikes made during this visit — a full refresh
  // resets it, but the post's like_count itself stays accurate either way.
  const [liked, setLiked] = useState(false);
  const [likeBusy, setLikeBusy] = useState(false);
  const [likeError, setLikeError] = useState("");

  const load = () => {
    setLoading(true);
    setError("");
    Promise.all([getPost(postId), listComments(postId)])
      .then(([postData, commentsData]) => {
        setPost(postData);
        setComments(commentsData);
      })
      .catch(() => setError("Could not load this post."))
      .finally(() => setLoading(false));
  };

  useEffect(load, [postId]);

  const handleCommentSubmit = async (e) => {
    e.preventDefault();
    setCommentError("");
    if (!commentText.trim()) return;

    setCommentSubmitting(true);
    try {
      const newComment = await addComment(postId, commentText.trim());
      setComments((prev) => [...prev, newComment]);
      setPost((prev) => (prev ? { ...prev, comment_count: prev.comment_count + 1 } : prev));
      setCommentText("");
    } catch (err) {
      setCommentError(err?.response?.data?.detail || "Could not post your comment.");
    } finally {
      setCommentSubmitting(false);
    }
  };

  const handleToggleLike = async () => {
    setLikeError("");
    setLikeBusy(true);
    try {
      if (liked) {
        await unlikePost(postId);
        setLiked(false);
        setPost((prev) => (prev ? { ...prev, like_count: Math.max(0, prev.like_count - 1) } : prev));
      } else {
        await likePost(postId);
        setLiked(true);
        setPost((prev) => (prev ? { ...prev, like_count: prev.like_count + 1 } : prev));
      }
    } catch (err) {
      setLikeError(err?.response?.data?.detail || "Could not update your like.");
    } finally {
      setLikeBusy(false);
    }
  };

  if (loading) return <div className="container" style={{ padding: "3rem 0" }}>Loading...</div>;
  if (error) return <div className="container" style={{ padding: "3rem 0" }}><p className="auth-error" role="alert">{error}</p></div>;
  if (!post) return null;

  return (
    <section className="section">
      <div className="container" style={{ maxWidth: "720px" }}>
        <Link to="/posts" className="nav-link" style={{ display: "inline-block", marginBottom: "1.5rem" }}>
          ← Back to all posts
        </Link>

        <header style={{ marginBottom: "1.5rem" }}>
          <h2 style={{ marginBottom: "0.4rem" }}>{post.title}</h2>
          <p style={{ opacity: 0.6, fontSize: "0.9rem" }}>
            By {post.author_name || "Unknown"} · {new Date(post.created_at).toLocaleString()} · {post.views} views
          </p>
        </header>

        {post.images.length > 0 && (
          <div style={{ display: "flex", flexWrap: "wrap", gap: "0.75rem", marginBottom: "1.5rem" }}>
            {post.images.map((url) => (
              <img
                key={url}
                src={url.startsWith("http") ? url : `${import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000"}${url}`}
                alt={post.title}
                style={{ maxWidth: "100%", maxHeight: "360px", borderRadius: "8px" }}
              />
            ))}
          </div>
        )}

        <p style={{ whiteSpace: "pre-wrap", lineHeight: 1.6, marginBottom: "1.5rem" }}>{post.content}</p>

        <div style={{ display: "flex", alignItems: "center", gap: "1rem", marginBottom: "2rem" }}>
          <button
            type="button"
            className="nav-btn nav-btn--quote"
            disabled={!isAuthenticated || likeBusy}
            onClick={handleToggleLike}
            title={!isAuthenticated ? "Log in to like this post" : undefined}
          >
            {liked ? "♥ Liked" : "♡ Like"} ({post.like_count})
          </button>
          {likeError && <span className="auth-error" role="alert">{likeError}</span>}
        </div>

        <h3>Comments ({post.comment_count})</h3>

        {isAuthenticated ? (
          <form onSubmit={handleCommentSubmit} style={{ marginBottom: "1.5rem" }}>
            <div className="auth-field" style={{ margin: "0 0 0.75rem" }}>
              <label className="auth-label" htmlFor="commentText">Add a comment</label>
              <textarea
                id="commentText"
                className="auth-input"
                rows={3}
                value={commentText}
                onChange={(e) => setCommentText(e.target.value)}
                placeholder="Share your thoughts..."
              />
            </div>
            {commentError && <p className="auth-error" role="alert">{commentError}</p>}
            <button type="submit" className="auth-submit" style={{ width: "auto", padding: "0 1.5rem" }} disabled={commentSubmitting}>
              {commentSubmitting ? "Posting..." : "Post Comment"}
            </button>
          </form>
        ) : (
          <p style={{ marginBottom: "1.5rem" }}>
            <Link to="/login">Log in</Link> to like or comment on this post.
          </p>
        )}

        {comments.length === 0 ? (
          <p style={{ opacity: 0.7 }}>No comments yet — be the first.</p>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
            {comments.map((c) => (
              <div key={c.id} className="auth-card" style={{ padding: "1rem 1.25rem" }}>
                <p style={{ margin: "0 0 0.3rem", fontWeight: 600 }}>{c.user_name || "Unknown"}</p>
                <p style={{ margin: "0 0 0.3rem" }}>{c.text}</p>
                <p style={{ margin: 0, fontSize: "0.8rem", opacity: 0.6 }}>
                  {new Date(c.created_at).toLocaleString()}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}