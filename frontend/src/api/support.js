import apiClient from "./client";

// Matches POST /api/ai-support → { reply, timestamp }.
// Works whether or not the user is logged in — apiClient already attaches
// a bearer token when one exists and simply omits it otherwise.
export const sendSupportMessage = (message) =>
  apiClient.post("/api/ai-support", { message }).then((r) => r.data);