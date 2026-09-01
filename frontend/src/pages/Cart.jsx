import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getCart, removeFromCart, updateCartItem } from "../api/cart";
import { startCheckout } from "../api/checkout";

// The backend now computes everything (item_total, subtotal, tax, grand_total)
// server-side (see fastapi_backend/routes/cart.py) — this page just renders
// whatever GET /cart returns, and re-fetches after every add/update/remove.
export default function Cart() {
  const [cart, setCart] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [busyId, setBusyId] = useState(null);
  const [checkingOut, setCheckingOut] = useState(false);
  const [checkoutError, setCheckoutError] = useState("");

  const load = async () => {
    setLoading(true);
    setError("");
    try {
      setCart(await getCart());
    } catch {
      setError("Could not load your cart.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const handleQuantityChange = async (item, quantity) => {
    if (quantity < 1) return;
    setBusyId(item.id);
    try {
      setCart(await updateCartItem({ item_id: item.id, quantity }));
    } catch {
      setError("Could not update that item's quantity.");
    } finally {
      setBusyId(null);
    }
  };

  const handleRemove = async (item) => {
    setBusyId(item.id);
    try {
      setCart(await removeFromCart(item.id));
    } catch {
      setError("Could not remove that item.");
    } finally {
      setBusyId(null);
    }
  };

  const handleCheckout = async () => {
    setCheckoutError("");
    setCheckingOut(true);
    try {
      const { checkout_url } = await startCheckout();
      // Hand off to Stripe's hosted payment page. It redirects back to
      // /checkout/success or /checkout/cancel when the customer is done.
      window.location.href = checkout_url;
    } catch (err) {
      setCheckoutError(err?.response?.data?.detail || "Could not start checkout. Please try again.");
      setCheckingOut(false);
    }
  };

  if (loading) return <div className="container" style={{ padding: "3rem 0" }}>Loading your cart...</div>;

  return (
    <section className="section">
      <div className="container">
        <header className="section-header">
          <p className="section-label">Your Cart</p>
          <h2>Shopping Cart</h2>
        </header>

        {error && <p className="auth-error" role="alert">{error}</p>}

        {!cart || cart.items.length === 0 ? (
          <p>
            Your cart is empty. <Link to="/products">Browse products</Link>.
          </p>
        ) : (
          <>
            <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
              {cart.items.map((item) => (
                <div
                  key={item.id}
                  className="auth-card"
                  style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "1rem 1.5rem", flexWrap: "wrap", gap: "1rem" }}
                >
                  <div>
                    <strong>{item.product_name}</strong>
                    <p style={{ margin: 0 }}>₹{Number(item.unit_price).toFixed(2)} each</p>
                  </div>

                  <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
                    <label className="auth-label" htmlFor={`qty-${item.id}`} style={{ margin: 0 }}>Qty</label>
                    <input
                      id={`qty-${item.id}`}
                      type="number"
                      min="1"
                      className="auth-input"
                      style={{ width: 80 }}
                      value={item.quantity}
                      disabled={busyId === item.id}
                      onChange={(e) => handleQuantityChange(item, Number(e.target.value))}
                    />
                    <span className="product-card__price-current">₹{Number(item.item_total).toFixed(2)}</span>
                    <button
                      className="nav-btn nav-btn--login"
                      disabled={busyId === item.id}
                      onClick={() => handleRemove(item)}
                    >
                      {busyId === item.id ? "..." : "Remove"}
                    </button>
                  </div>
                </div>
              ))}
            </div>

            <div style={{ marginTop: "1.5rem", marginLeft: "auto", maxWidth: 320 }}>
              <div style={{ display: "flex", justifyContent: "space-between" }}>
                <span>Subtotal ({cart.total_items} items)</span>
                <span>₹{Number(cart.subtotal).toFixed(2)}</span>
              </div>
              <div style={{ display: "flex", justifyContent: "space-between" }}>
                <span>Tax ({(cart.tax_rate * 100).toFixed(0)}%)</span>
                <span>₹{Number(cart.tax).toFixed(2)}</span>
              </div>
              <div style={{ display: "flex", justifyContent: "space-between", fontWeight: 700, marginTop: "0.5rem", borderTop: "1px solid var(--color-gray-light)", paddingTop: "0.5rem" }}>
                <span>Grand Total</span>
                <span>₹{Number(cart.grand_total).toFixed(2)}</span>
              </div>

              {checkoutError && <p className="auth-error" role="alert" style={{ marginTop: "0.75rem" }}>{checkoutError}</p>}

              <button
                className="btn btn-primary w-full"
                style={{ marginTop: "1rem" }}
                disabled={checkingOut}
                onClick={handleCheckout}
              >
                {checkingOut ? "Redirecting to Stripe..." : "Proceed to Checkout"}
              </button>
              <p style={{ opacity: 0.7, marginTop: "0.5rem", fontSize: "0.85rem" }}>
                You'll be taken to Stripe's secure payment page. Use test card 4242 4242 4242 4242, any future expiry, any CVC.
              </p>
            </div>
          </>
        )}
      </div>
    </section>
  );
}
