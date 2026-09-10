import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { listProducts } from "../api/products";
import ProductCard from "../components/ProductCard";
import RecommendationsSection from "../components/RecommendationsSection";
import { useAuth } from "../context/AuthContext";
import { addToCart } from "../api/cart";
import { getRecommendationsForUser, getTrendingProducts } from "../api/recommendations";

export default function Home() {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const { isAuthenticated, user } = useAuth();
  const [addingId, setAddingId] = useState(null);
  const [message, setMessage] = useState("");

  // NEW (Recommendation System milestone)
  const [recommended, setRecommended] = useState([]);
  const [trending, setTrending] = useState([]);

  useEffect(() => {
    listProducts()
      .then((data) => setProducts(data.slice(0, 4)))
      .finally(() => setLoading(false));
  }, []);

  // "You May Also Like" — storewide trending rail, shown to everyone.
  useEffect(() => {
    getTrendingProducts(8)
      .then((data) => setTrending(data.products))
      .catch(() => setTrending([]));
  }, []);

  // "Recommended For You" — personalized, only once we know who's logged in.
  useEffect(() => {
    if (!isAuthenticated || !user?.id) {
      setRecommended([]);
      return;
    }
    getRecommendationsForUser(user.id, 8)
      .then((data) => setRecommended(data.products))
      .catch(() => setRecommended([]));
  }, [isAuthenticated, user?.id]);

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

      {/* NEW (Recommendation System milestone) — personalized, only rendered
          once we actually have picks (empty until getRecommendationsForUser
          resolves, and RecommendationsSection itself no-ops on an empty list). */}
      <RecommendationsSection
        title="Recommended For You"
        subtitle="Just For You"
        products={recommended}
        onAddToCart={handleAddToCart}
        addingId={addingId}
      />

      {/* NEW (Recommendation System milestone) — storewide trending rail,
          shown to everyone regardless of login state. */}
      <RecommendationsSection
        title="You May Also Like"
        subtitle="Trending Now"
        products={trending}
        onAddToCart={handleAddToCart}
        addingId={addingId}
      />
    </>
  );
}