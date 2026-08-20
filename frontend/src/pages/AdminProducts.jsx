import { useEffect, useState } from "react";
import { createProduct, deleteProduct, listProducts } from "../api/products";

const emptyForm = { name: "", description: "", price: "", stock: "", images: "", category: "" };

export default function AdminProducts() {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [form, setForm] = useState(emptyForm);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const load = () => {
    setLoading(true);
    listProducts()
      .then(setProducts)
      .finally(() => setLoading(false));
  };

  useEffect(load, []);

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      await createProduct({
        name: form.name,
        description: form.description || null,
        price: Number(form.price),
        stock: Number(form.stock) || 0,
        images: form.images ? form.images.split(",").map((s) => s.trim()).filter(Boolean) : [],
        category: form.category || null,
      });
      setForm(emptyForm);
      load();
    } catch (err) {
      // 403 here means the logged-in user isn't an admin (see core/permissions.py)
      setError(err?.response?.data?.detail || "Could not create product.");
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (id) => {
    try {
      await deleteProduct(id);
      setProducts((prev) => prev.filter((p) => p.id !== id));
    } catch {
      setError("Could not delete that product.");
    }
  };

  return (
    <section className="section">
      <div className="container">
        <header className="section-header">
          <p className="section-label">Admin</p>
          <h2>Manage Products</h2>
          <p>Create, view, and delete products. Requires the "admin" role (POST /products is admin-only, per core/permissions.py).</p>
        </header>

        <form onSubmit={handleSubmit} className="auth-form" style={{ maxWidth: 480, marginBottom: "2.5rem" }}>
          <div className="auth-field">
            <label className="auth-label" htmlFor="name">Name</label>
            <input id="name" name="name" className="auth-input" required value={form.name} onChange={handleChange} />
          </div>
          <div className="auth-field">
            <label className="auth-label" htmlFor="description">Description</label>
            <input id="description" name="description" className="auth-input" value={form.description} onChange={handleChange} />
          </div>
          <div className="auth-field">
            <label className="auth-label" htmlFor="price">Price</label>
            <input id="price" name="price" type="number" step="0.01" min="0.01" className="auth-input" required value={form.price} onChange={handleChange} />
          </div>
          <div className="auth-field">
            <label className="auth-label" htmlFor="stock">Stock</label>
            <input id="stock" name="stock" type="number" min="0" className="auth-input" value={form.stock} onChange={handleChange} />
          </div>
          <div className="auth-field">
            <label className="auth-label" htmlFor="category">Category</label>
            <input id="category" name="category" className="auth-input" placeholder="e.g. Skincare" value={form.category} onChange={handleChange} />
          </div>
          <div className="auth-field">
            <label className="auth-label" htmlFor="images">Image URLs (comma-separated)</label>
            <input id="images" name="images" className="auth-input" placeholder="https://example.com/product.jpg" value={form.images} onChange={handleChange} />
          </div>

          {error && <span className="auth-error" role="alert">{error}</span>}

          <button type="submit" className="auth-submit" disabled={submitting}>
            {submitting ? "Creating..." : "Create Product"}
          </button>
        </form>

        <h3>Existing Products</h3>
        {loading ? (
          <p>Loading...</p>
        ) : (
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ textAlign: "left", borderBottom: "1px solid var(--color-gray-light)" }}>
                <th style={{ padding: "0.5rem" }}>Name</th>
                <th style={{ padding: "0.5rem" }}>Category</th>
                <th style={{ padding: "0.5rem" }}>Price</th>
                <th style={{ padding: "0.5rem" }}>Stock</th>
                <th style={{ padding: "0.5rem" }}>Popularity</th>
                <th style={{ padding: "0.5rem" }}></th>
              </tr>
            </thead>
            <tbody>
              {products.map((p) => (
                <tr key={p.id} style={{ borderBottom: "1px solid var(--color-gray-light)" }}>
                  <td style={{ padding: "0.5rem" }}>{p.name}</td>
                  <td style={{ padding: "0.5rem" }}>{p.category || "—"}</td>
                  <td style={{ padding: "0.5rem" }}>₹{Number(p.price).toFixed(2)}</td>
                  <td style={{ padding: "0.5rem" }}>{p.stock}</td>
                  <td style={{ padding: "0.5rem" }}>{p.popularity}</td>
                  <td style={{ padding: "0.5rem" }}>
                    <button className="nav-btn nav-btn--login" onClick={() => handleDelete(p.id)}>Delete</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </section>
  );
}
