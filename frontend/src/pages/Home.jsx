import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { listProducts } from "../api/products";
import ProductCard from "../components/ProductCard";
import { useAuth } from "../context/AuthContext";
import { addToCart } from "../api/cart";

export default function Home() {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const { isAuthenticated } = useAuth();
  const [addingId, setAddingId] = useState(null);
  const [message, setMessage] = useState("");

  useEffect(() => {
    listProducts()
      .then((data) => setProducts(data.slice(0, 4)))
      .finally(() => setLoading(false));
  }, []);

  const handleAddToCart = async (product) => {
    if (!isAuthenticated) {
      setMessage("Please log in to add items to your cart.");
      return;
    }
    setAddingId(product.id);
    try {
      await addToCart({ product_id: product.id, quantity: 1 });
      setMessage(`Added "${product.name}" to your cart.`);
    } catch {
      setMessage("Could not add that item to your cart.");
    } finally {
      setAddingId(null);
    }
  };

  return (
    <>
      <section className="hero" style={{ padding: "5rem 0 3rem" }}>
        <div className="container">
          <p className="section-label">Smart E-Commerce Platform</p>
          <h1 style={{ maxWidth: 720 }}>Handmade skincare, powered by a full-stack e-commerce build.</h1>
          <p style={{ maxWidth: 560 }}>
            FastAPI authentication with JWT, Auth0 social login, role-based
            access control, and a Django admin panel — all backing this React
            storefront.
          </p>
          <Link to="/products" className="btn btn-primary" style={{ marginTop: "1.5rem", display: "inline-block" }}>
            Shop All Products
          </Link>
        </div>
      </section>

      <section className="section">
        <div className="container">
          <header className="section-header">
            <p className="section-label">Bestsellers</p>
            <h2>Most Loved Products</h2>
          </header>

          {message && <p className="auth-error" role="status" style={{ marginBottom: "1rem" }}>{message}</p>}

          {loading ? (
            <p>Loading products...</p>
          ) : products.length === 0 ? (
            <p>
              No products yet — log in as an admin and add some from the{" "}
              <Link to="/admin/products">Admin</Link> page.
            </p>
          ) : (
            <div className="grid grid-4 products-grid">
              {products.map((p) => (
                <ProductCard key={p.id} product={p} onAddToCart={handleAddToCart} adding={addingId === p.id} />
              ))}
            </div>
          )}
        </div>
      </section>
    </>
  );
}
