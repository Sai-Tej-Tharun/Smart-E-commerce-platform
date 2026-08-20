import { Link } from "react-router-dom";
import logoDark from "../assets/logo-dark.svg";

export default function Footer() {
  return (
    <footer id="footer" role="contentinfo" aria-label="Site footer">
      <div className="footer-top">
        <div className="footer-grid">
          <div className="footer-brand">
            <Link to="/" className="navbar-logo navbar-logo-fixed-dark" aria-label="GlowVeda – go to homepage">
              <img src={logoDark} alt="" height="44" className="logo-icon" />
              <span className="logo-text">
                Glow<span>Veda</span>
              </span>
            </Link>
            <p>
              A Smart E-Commerce Platform build — FastAPI backend, Django admin
              panel, and this React storefront, sharing one MySQL database.
            </p>
          </div>

          <div className="footer-col">
            <h4>Shop</h4>
            <ul className="footer-links" role="list">
              <li><Link to="/products" className="footer-link" role="listitem">All Products</Link></li>
              <li><Link to="/cart" className="footer-link" role="listitem">Your Cart</Link></li>
            </ul>
          </div>

          <div className="footer-col">
            <h4>Account</h4>
            <ul className="footer-links" role="list">
              <li><Link to="/login" className="footer-link" role="listitem">Login</Link></li>
              <li><Link to="/register" className="footer-link" role="listitem">Register</Link></li>
            </ul>
          </div>
        </div>
      </div>

      <div className="footer-bottom">
        <p>&copy; <span id="footer-year">{new Date().getFullYear()}</span> GlowVeda. All rights reserved.</p>
      </div>
    </footer>
  );
}
