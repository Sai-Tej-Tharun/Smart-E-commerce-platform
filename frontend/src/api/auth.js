import apiClient from "./client";

// Matches fastapi_backend/schemas/user.py + routes/auth.py exactly.

export const registerUser = ({ name, email, password }) =>
  apiClient.post("/auth/register", { name, email, password }).then((r) => r.data);

export const loginUser = ({ email, password }) =>
  apiClient.post("/auth/login", { email, password }).then((r) => r.data);

export const fetchCurrentUser = () => apiClient.get("/auth/me").then((r) => r.data);

export const socialLogin = (auth0IdToken) =>
  apiClient.post("/auth/social", { auth0_id_token: auth0IdToken }).then((r) => r.data);
