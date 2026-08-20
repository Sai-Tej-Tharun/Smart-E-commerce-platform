import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import logo from "../assets/logo.svg";

export default function Navbar() {
  const { user, isAuthenticated, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <nav id="navbar" role="navigation" aria-label="Main navigation">
      <div className="navbar-inner">
        <Link to="/" className="navbar-logo" aria-label="GlowVeda – go to homepage">
          <img src={logo} alt="" height="44" className="logo-icon" />
          <span className="logo-text">
            Glow<span>Veda</span>
          </span>
        </Link>

        <ul className="navbar-nav" role="list">
          <li className="nav-item">
            <Link to="/" className="nav-link">Home</Link>
          </li>
          <li className="nav-item">
            <Link to="/products" className="nav-link">Products</Link>
          </li>
          <li className="nav-item">
            <Link to="/cart" className="nav-link">Cart</Link>
          </li>
          {isAuthenticated && (
            <li className="nav-item">
              <Link to="/orders" className="nav-link">Orders</Link>
            </li>
          )}
          {user?.role === "admin" && (
            <li className="nav-item">
              <Link to="/admin/products" className="nav-link">Admin</Link>
            </li>
          )}
        </ul>

        <div className="navbar-actions">
          {isAuthenticated ? (
            <>
              <span className="nav-ctrl-btn" style={{ width: "auto", padding: "0 .5rem" }}>
                {user?.name}
              </span>
              <button type="button" className="nav-btn nav-btn--login" onClick={handleLogout}>
                Logout
              </button>
            </>
          ) : (
            <>
              <Link to="/login" className="nav-btn nav-btn--login hide-mobile-btn">Login</Link>
              <Link to="/register" className="nav-btn nav-btn--quote">Sign Up</Link>
            </>
          )}
        </div>
      </div>
    </nav>
  );
}
