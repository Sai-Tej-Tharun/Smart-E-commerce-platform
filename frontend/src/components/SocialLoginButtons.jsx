import { useAuth0 } from "@auth0/auth0-react";
import { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";
import { useNavigate } from "react-router-dom";

// Renders "Continue with Google" / "Continue with Facebook". Both send the
// user through Auth0's hosted login page; once Auth0 redirects back here
// with a session, we grab the ID token and hand it to
// POST /auth/social on the FastAPI backend (see routes/auth.py).
export default function SocialLoginButtons() {
  const auth0Configured = Boolean(
    import.meta.env.VITE_AUTH0_DOMAIN && import.meta.env.VITE_AUTH0_CLIENT_ID
  );

  if (!auth0Configured) {
    return (
      <div className="auth-social">
        <button type="button" className="auth-social__btn" disabled title="Set VITE_AUTH0_DOMAIN and VITE_AUTH0_CLIENT_ID in .env to enable this">
          <GoogleIcon /> Continue with Google
        </button>
        <button type="button" className="auth-social__btn" disabled title="Set VITE_AUTH0_DOMAIN and VITE_AUTH0_CLIENT_ID in .env to enable this">
          <FacebookIcon /> Continue with Facebook
        </button>
      </div>
    );
  }

  return <ConfiguredSocialButtons />;
}

function ConfiguredSocialButtons() {
  const { loginWithRedirect, getIdTokenClaims, isAuthenticated, isLoading } = useAuth0();
  const { loginWithAuth0Token } = useAuth();
  const navigate = useNavigate();
  const [exchanging, setExchanging] = useState(false);
  const [error, setError] = useState("");

  // Once Auth0 finishes its redirect and reports an authenticated session,
  // pull the ID token and exchange it for this app's own JWT pair.
  useEffect(() => {
    async function exchange() {
      if (!isAuthenticated || exchanging) return;
      setExchanging(true);
      try {
        const claims = await getIdTokenClaims();
        await loginWithAuth0Token(claims.__raw);
        navigate("/");
      } catch (err) {
        setError(err?.response?.data?.detail || "Social login failed. Please try again.");
      } finally {
        setExchanging(false);
      }
    }
    exchange();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAuthenticated]);

  return (
    <>
      <div className="auth-social">
        <button
          type="button"
          className="auth-social__btn"
          disabled={isLoading || exchanging}
          onClick={() => loginWithRedirect({ authorizationParams: { connection: "google-oauth2" } })}
        >
          <GoogleIcon /> Continue with Google
        </button>
        <button
          type="button"
          className="auth-social__btn"
          disabled={isLoading || exchanging}
          onClick={() => loginWithRedirect({ authorizationParams: { connection: "facebook" } })}
        >
          <FacebookIcon /> Continue with Facebook
        </button>
      </div>
      {error && <span className="auth-error" role="alert">{error}</span>}
    </>
  );
}

function GoogleIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" aria-hidden="true">
      <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4" />
      <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853" />
      <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05" />
      <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335" />
    </svg>
  );
}

function FacebookIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="#1877F2" aria-hidden="true">
      <path d="M22 12.06C22 6.5 17.52 2 12 2S2 6.5 2 12.06c0 5 3.66 9.15 8.44 9.94v-7.03H7.9v-2.91h2.54V9.85c0-2.51 1.49-3.9 3.77-3.9 1.09 0 2.24.2 2.24.2v2.46h-1.26c-1.24 0-1.63.77-1.63 1.56v1.87h2.78l-.44 2.91h-2.34V22c4.78-.79 8.44-4.94 8.44-9.94z" />
    </svg>
  );
}
