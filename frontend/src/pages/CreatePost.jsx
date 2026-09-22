import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { createPost } from "../api/posts";

export default function CreatePost() {
  const navigate = useNavigate();
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [images, setImages] = useState([]);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const handleFileChange = (e) => setImages(Array.from(e.target.files));

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    if (!title.trim() || !content.trim()) {
      setError("Title and content are both required.");
      return;
    }

    const formData = new FormData();
    formData.append("title", title);
    formData.append("content", content);
    images.forEach((file) => formData.append("images", file));

    setSubmitting(true);
    try {
      const post = await createPost(formData);
      navigate(`/dashboard`, { replace: true, state: { createdPostId: post.id } });
    } catch (err) {
      setError(err?.response?.data?.detail || "Could not create the post. Please try again.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <section className="section">
      <div className="container" style={{ maxWidth: "640px" }}>
        <header className="section-header">
          <p className="section-label">Blog</p>
          <h2>Create a Post</h2>
        </header>

        <div className="auth-card" style={{ padding: "1.5rem" }}>
          <form onSubmit={handleSubmit} className="auth-form" noValidate>
            <div className="auth-field">
              <label className="auth-label" htmlFor="postTitle">Title</label>
              <div className="auth-input-wrap">
                <input
                  type="text"
                  id="postTitle"
                  className="auth-input"
                  placeholder="My First Blog Post"
                  required
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                />
              </div>
            </div>

            <div className="auth-field">
              <label className="auth-label" htmlFor="postContent">Content</label>
              <div className="auth-input-wrap">
                <textarea
                  id="postContent"
                  className="auth-input"
                  placeholder="Write your post..."
                  rows={8}
                  required
                  value={content}
                  onChange={(e) => setContent(e.target.value)}
                />
              </div>
            </div>

            <div className="auth-field">
              <label className="auth-label" htmlFor="postImages">
                Image(s) — optional, count allowed depends on your plan
              </label>
              <div className="auth-input-wrap">
                <input
                  type="file"
                  id="postImages"
                  accept="image/*"
                  multiple
                  onChange={handleFileChange}
                />
              </div>
              {images.length > 0 && (
                <p style={{ fontSize: "0.85rem", opacity: 0.7, marginTop: "0.4rem" }}>
                  {images.length} image{images.length > 1 ? "s" : ""} selected
                </p>
              )}
            </div>

            {error && <span className="auth-error" role="alert">{error}</span>}

            <button type="submit" className="auth-submit" disabled={submitting}>
              {submitting ? "Publishing..." : "Publish Post"}
            </button>
          </form>
        </div>
      </div>
    </section>
  );
}