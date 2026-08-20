import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { getProduct } from "../api/products";
import { addToCart } from "../api/cart";
import { useAuth } from "../context/AuthContext";

export default function ProductDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();
  const [product, setProduct] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [adding, setAdding] = useState(false);
  const [quantity, setQuantity] = useState(1);

  useEffect(() => {
    setLoading(true);
    getProduct(id)
      .then(setProduct)
      .catch(() => setError("Product not found."))
      .finally(() => setLoading(false));
  }, [id]);

  const handleAddToCart = async () => {
    if (!isAuthenticated) {
      setMessage("Please log in to add items to your cart.");
      return;
    }
    setAdding(true);
    try {
      await addToCart({ product_id: product.id, quantity });
      setMessage(`Added ${quantity} × "${product.name}" to your cart.`);
    } catch {
      setMessage("Could not add that item to your cart.");
    } finally {
      setAdding(false);
    }
  };

  if (loading) return <div className="container" style={{ padding: "3rem 0" }}>Loading...</div>;
  if (error || !product) {
    return (
      <div className="container" style={{ padding: "3rem 0" }}>
        <p className="auth-error">{error || "Product not found."}</p>
        <button className="btn btn-primary" onClick={() => navigate("/products")}>Back to Products</button>
      </div>
    );
  }

  const image = product.images?.[0];

  return (
    <section className="section">
      <div className="container">
        <div className="grid grid-2" style={{ gap: "2.5rem", alignItems: "start" }}>
          <div className="product-card__image" style={{ borderRadius: "var(--radius-lg, 12px)", overflow: "hidden" }}>
            {image ? (
              <img src={image} alt={product.name} style={{ width: "100%", height: "auto", display: "block" }} />
            ) : (
              <div className="product-card__image-placeholder" style={{ minHeight: 320 }} aria-hidden="true" />
            )}
          </div>

          <div>
            {product.category && <p className="product-card__category">{product.category}</p>}
            <h1>{product.name}</h1>
            <p className="product-card__price-current" style={{ fontSize: "var(--text-3xl)" }}>
              ₹{Number(product.price).toFixed(2)}
            </p>
            {product.description && <p>{product.description}</p>}
            <p>
              <strong>{product.stock > 0 ? `${product.stock} in stock` : "Out of stock"}</strong>
            </p>

            <div style={{ display: "flex", gap: "0.75rem", alignItems: "center", margin: "1.5rem 0" }}>
              <label className="auth-label" htmlFor="qty">Qty</label>
              <input
                id="qty"
                type="number"
                min="1"
                max={product.stock || 1}
                value={quantity}
                onChange={(e) => setQuantity(Math.max(1, Number(e.target.value)))}
                className="auth-input"
                style={{ width: 90 }}
              />
            </div>

            {message && <p className="auth-error" role="status">{message}</p>}

            <button
              className="btn btn-primary"
              disabled={product.stock === 0 || adding}
              onClick={handleAddToCart}
            >
              {product.stock === 0 ? "Out of stock" : adding ? "Adding..." : "Add to Cart"}
            </button>
          </div>
        </div>
      </div>
    </section>
  );
}
