import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import SocialLoginButtons from "../components/SocialLoginButtons";
import logo from "../assets/logo.svg";

export default function Register() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ name: "", email: "", password: "" });
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    if (form.password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }
    setSubmitting(true);
    try {
      await register(form.name, form.email, form.password);
      navigate("/", { replace: true });
    } catch (err) {
      setError(err?.response?.data?.detail || "Could not create your account. Try a different email.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="auth-body">
      <div className="auth-layout auth-layout--register">
        <div className="auth-panel auth-panel--form">
          <div className="auth-card" role="main">
            <Link to="/" className="auth-card__logo-mobile" aria-label="GlowVeda – go to homepage">
              <img src={logo} alt="" />
              <span className="logo-text">Glow<span>Veda</span></span>
            </Link>

            <div className="auth-card__header">
              <h1>Create your account</h1>
              <p>Join GlowVeda — every new account starts as a customer</p>
            </div>

            <SocialLoginButtons />

            <div className="auth-divider" aria-hidden="true">
              <span>or sign up with email</span>
            </div>

            <form className="auth-form" onSubmit={handleSubmit} noValidate aria-label="Register form">
              <div className="auth-field">
                <label className="auth-label" htmlFor="registerName">Full name</label>
                <div className="auth-input-wrap">
                  <input
                    type="text"
                    id="registerName"
                    name="name"
                    className="auth-input"
                    placeholder="Alice Customer"
                    autoComplete="name"
                    required
                    value={form.name}
                    onChange={handleChange}
                  />
                </div>
              </div>

              <div className="auth-field">
                <label className="auth-label" htmlFor="registerEmail">Email address</label>
                <div className="auth-input-wrap">
                  <input
                    type="email"
                    id="registerEmail"
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
                <label className="auth-label" htmlFor="registerPassword">Password</label>
                <div className="auth-input-wrap">
                  <input
                    type="password"
                    id="registerPassword"
                    name="password"
                    className="auth-input"
                    placeholder="At least 8 characters"
                    autoComplete="new-password"
                    required
                    minLength={8}
                    value={form.password}
                    onChange={handleChange}
                  />
                </div>
              </div>

              {error && <span className="auth-error" role="alert">{error}</span>}

              <button type="submit" className="auth-submit" disabled={submitting}>
                {submitting ? "Creating account..." : "Create Account"}
              </button>
            </form>

            <p className="auth-card__footer">
              Already have an account? <Link to="/login" className="auth-switch-link">Sign in</Link>
            </p>
          </div>
        </div>

        <div className="auth-panel auth-panel--brand">
          <div className="auth-brand">
            <p className="auth-brand__quote">
              "New accounts always start as a customer — admin access is granted
              separately, never through self sign-up."
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
