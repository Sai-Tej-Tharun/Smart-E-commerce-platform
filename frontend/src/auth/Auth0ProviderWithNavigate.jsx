import { Auth0Provider } from "@auth0/auth0-react";
import { useNavigate } from "react-router-dom";

// Wraps the app with Auth0's SDK so <SocialLoginButtons /> can trigger the
// Google/Facebook hosted-login redirect. If Auth0 env vars aren't set yet,
// this simply renders children with no Auth0 context (the social buttons
// show a friendly "not configured" message instead of crashing).
export default function Auth0ProviderWithNavigate({ children }) {
  const navigate = useNavigate();

  const domain = import.meta.env.VITE_AUTH0_DOMAIN;
  const clientId = import.meta.env.VITE_AUTH0_CLIENT_ID;

  const onRedirectCallback = (appState) => {
    navigate(appState?.returnTo || "/");
  };

  if (!domain || !clientId) {
    return children;
  }

  return (
    <Auth0Provider
      domain={domain}
      clientId={clientId}
      authorizationParams={{ redirect_uri: window.location.origin }}
      onRedirectCallback={onRedirectCallback}
      cacheLocation="localstorage"
    >
      {children}
    </Auth0Provider>
  );
}
