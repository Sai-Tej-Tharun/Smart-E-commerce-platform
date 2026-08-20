import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import SocialLoginButtons from "../components/SocialLoginButtons";
import logo from "../assets/logo.svg";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [form, setForm] = useState({ email: "", password: "" });
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      await login(form.email, form.password);
      navigate(location.state?.from?.pathname || "/", { replace: true });
    } catch (err) {
      setError(err?.response?.data?.detail || "Invalid email or password.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="auth-body">
      <div className="auth-layout">
        <div className="auth-panel auth-panel--brand">
          <div className="auth-brand">
            <p className="auth-brand__quote">
              "Rooted in Ayurvedic wisdom, crafted with love — sign in to pick up
              right where you left off."
            </p>
          </div>
        </div>

        <div className="auth-panel auth-panel--form">
          <div className="auth-card" role="main">
            <Link to="/" className="auth-card__logo-mobile" aria-label="GlowVeda – go to homepage">
              <img src={logo} alt="" />
              <span className="logo-text">Glow<span>Veda</span></span>
            </Link>

            <div className="auth-card__header">
              <h1>Welcome back</h1>
              <p>Sign in to your GlowVeda account</p>
            </div>

            <SocialLoginButtons />

            <div className="auth-divider" aria-hidden="true">
              <span>or sign in with email</span>
            </div>

            <form className="auth-form" onSubmit={handleSubmit} noValidate aria-label="Login form">
              <div className="auth-field">
                <label className="auth-label" htmlFor="loginEmail">Email address</label>
                <div className="auth-input-wrap">
                  <input
                    type="email"
                    id="loginEmail"
                    name="email"
                    className="auth-input"
                    placeholder="you@example.com"
                    autoComplete="email"
                    required
                    value={form.email}
                    onChange={handleChange}
                  />
                </div>
              </div>

              <div className="auth-field">
                <label className="auth-label" htmlFor="loginPassword">Password</label>
                <div className="auth-input-wrap">
                  <input
                    type="password"
                    id="loginPassword"
                    name="password"
                    className="auth-input"
                    placeholder="••••••••"
                    autoComplete="current-password"
                    required
                    value={form.password}
                    onChange={handleChange}
                  />
                </div>
              </div>

              {error && <span className="auth-error" role="alert">{error}</span>}

              <button type="submit" className="auth-submit" disabled={submitting}>
                {submitting ? "Signing in..." : "Sign In"}
              </button>
            </form>

            <p className="auth-card__footer">
              Don't have an account? <Link to="/register" className="auth-switch-link">Create one free</Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
