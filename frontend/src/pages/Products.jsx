import { useEffect, useState } from "react";
import { listProducts } from "../api/products";
import { addToCart } from "../api/cart";
import ProductCard from "../components/ProductCard";
import { useAuth } from "../context/AuthContext";

const SORT_OPTIONS = [
  { value: "newest", label: "Newest" },
  { value: "popularity", label: "Most Popular" },
  { value: "price_asc", label: "Price: Low to High" },
  { value: "price_desc", label: "Price: High to Low" },
];

export default function Products() {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [addingId, setAddingId] = useState(null);
  const { isAuthenticated } = useAuth();

  const [filters, setFilters] = useState({
    category: "",
    min_price: "",
    max_price: "",
    in_stock: "",
    sort: "newest",
  });

  const load = () => {
    setLoading(true);
    setError("");
    listProducts(filters)
      .then(setProducts)
      .catch(() => setError("Could not load products. Is the FastAPI backend running?"))
      .finally(() => setLoading(false));
  };

  // Re-fetch whenever a filter changes — GET /products?category=&min_price=&... (see api/products.js)
  useEffect(load, [filters.category, filters.min_price, filters.max_price, filters.in_stock, filters.sort]);

  const handleFilterChange = (e) => {
    const { name, value } = e.target;
    setFilters((prev) => ({ ...prev, [name]: value }));
  };

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
    <section className="section">
      <div className="container">
        <header className="section-header">
          <p className="section-label">Shop</p>
          <h2>All Products</h2>
        </header>

        <form
          onSubmit={(e) => e.preventDefault()}
          style={{ display: "flex", flexWrap: "wrap", gap: "1rem", alignItems: "end", marginBottom: "2rem" }}
        >
          <div className="auth-field" style={{ margin: 0 }}>
            <label className="auth-label" htmlFor="f-category">Category</label>
            <input id="f-category" name="category" className="auth-input" placeholder="e.g. Skincare" value={filters.category} onChange={handleFilterChange} />
          </div>
          <div className="auth-field" style={{ margin: 0 }}>
            <label className="auth-label" htmlFor="f-min">Min ₹</label>
            <input id="f-min" name="min_price" type="number" min="0" className="auth-input" style={{ width: 100 }} value={filters.min_price} onChange={handleFilterChange} />
          </div>
          <div className="auth-field" style={{ margin: 0 }}>
            <label className="auth-label" htmlFor="f-max">Max ₹</label>
            <input id="f-max" name="max_price" type="number" min="0" className="auth-input" style={{ width: 100 }} value={filters.max_price} onChange={handleFilterChange} />
          </div>
          <div className="auth-field" style={{ margin: 0 }}>
            <label className="auth-label" htmlFor="f-stock">Availability</label>
            <select id="f-stock" name="in_stock" className="auth-input" value={filters.in_stock} onChange={handleFilterChange}>
              <option value="">All</option>
              <option value="true">In stock</option>
              <option value="false">Out of stock</option>
            </select>
          </div>
          <div className="auth-field" style={{ margin: 0 }}>
            <label className="auth-label" htmlFor="f-sort">Sort by</label>
            <select id="f-sort" name="sort" className="auth-input" value={filters.sort} onChange={handleFilterChange}>
              {SORT_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>{o.label}</option>
              ))}
            </select>
          </div>
        </form>

        {message && <p className="auth-error" role="status" style={{ marginBottom: "1rem" }}>{message}</p>}
        {error && <p className="auth-error" role="alert">{error}</p>}

        {loading ? (
          <p>Loading products...</p>
        ) : products.length === 0 ? (
          <p>No products match those filters.</p>
        ) : (
          <div className="grid grid-4 products-grid">
            {products.map((p) => (
              <ProductCard key={p.id} product={p} onAddToCart={handleAddToCart} adding={addingId === p.id} />
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
