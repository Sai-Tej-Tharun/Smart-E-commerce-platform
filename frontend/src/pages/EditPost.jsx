import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { listMyPosts, updatePost } from "../api/posts";
import PublishOptions, {
  appendPublishFields,
  submitLabel,
  toLocalParts,
  validatePublish,
} from "../components/PublishOptions";

export default function EditPost() {
  const { postId } = useParams();
  const navigate = useNavigate();

  const [post, setPost] = useState(null);
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [publish, setPublish] = useState({ option: "draft", date: "", time: "" });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    listMyPosts()
      .then((posts) => {
        const p = posts.find((x) => x.id === Number(postId));
        if (!p) {
          setError("Post not found.");
          return;
        }
        setPost(p);
        setTitle(p.title);
        setContent(p.content);
        if (p.status === "scheduled") {
          setPublish({ option: "schedule", ...toLocalParts(p.scheduled_at) });
        } else if (p.status === "draft") {
          setPublish({ option: "draft", date: "", time: "" });
        }
      })
      .catch(() => setError("Could not load this post."))
      .finally(() => setLoading(false));
  }, [postId]);

  const isPublished = post?.status === "published";

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

    if (!isPublished) {
      const publishError = validatePublish(publish);
      if (publishError) {
        setError(publishError);
        return;
      }
      appendPublishFields(formData, publish);
    }

    setSubmitting(true);
    try {
      await updatePost(postId, formData);
      navigate("/my-posts", { replace: true });
    } catch (err) {
      setError(err?.response?.data?.detail || "Could not update the post. Please try again.");
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) return <div className="container" style={{ padding: "3rem 0" }}>Loading...</div>;
  if (!post) return <div className="container" style={{ padding: "3rem 0" }}><p className="auth-error" role="alert">{error}</p></div>;

  return (
    <section className="section">
      <div className="container" style={{ maxWidth: "640px" }}>
        <header className="section-header">
          <p className="section-label">Blog</p>
          <h2>Edit Post</h2>
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
                  rows={8}
                  value={content}
                  onChange={(e) => setContent(e.target.value)}
                />
              </div>
            </div>

            {isPublished ? (
              <p style={{ opacity: 0.7 }}>This post is already published.</p>
            ) : (
              <PublishOptions value={publish} onChange={setPublish} />
            )}

            {error && <span className="auth-error" role="alert">{error}</span>}

            <button type="submit" className="auth-submit" disabled={submitting}>
              {isPublished ? (submitting ? "Saving..." : "Save Changes") : submitLabel(publish.option, submitting)}
            </button>
          </form>
        </div>
      </div>
    </section>
  );
}