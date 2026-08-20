import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { useAuth0 } from "@auth0/auth0-react";
import { fetchCurrentUser, loginUser, registerUser, socialLogin } from "../api/auth";
import { tokenStore } from "../api/client";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const { logout: auth0Logout } = useAuth0();

  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const loadCurrentUser = useCallback(async () => {
    if (!tokenStore.getAccess()) {
      setUser(null);
      setLoading(false);
      return;
    }

    try {
      const me = await fetchCurrentUser();
      setUser(me);
    } catch {
      tokenStore.clear();
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadCurrentUser();
  }, [loadCurrentUser]);

  const login = async (email, password) => {
    const tokens = await loginUser({ email, password });

    tokenStore.setTokens(
      tokens.access_token,
      tokens.refresh_token
    );

    const me = await fetchCurrentUser();
    setUser(me);

    return me;
  };

  const register = async (name, email, password) => {
    await registerUser({ name, email, password });
    return login(email, password);
  };

  const loginWithAuth0Token = async (auth0IdToken) => {
    const tokens = await socialLogin(auth0IdToken);

    tokenStore.setTokens(
      tokens.access_token,
      tokens.refresh_token
    );

    const me = await fetchCurrentUser();
    setUser(me);

    return me;
  };

  const logout = () => {
    // Logout from your FastAPI application
    tokenStore.clear();
    setUser(null);

    // Logout from Auth0
    auth0Logout({
      logoutParams: {
        returnTo: window.location.origin,
      },
    });
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        login,
        register,
        logout,
        loginWithAuth0Token,
        isAuthenticated: !!user,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);

  if (!ctx) {
    throw new Error("useAuth must be used inside <AuthProvider>");
  }

  return ctx;
}