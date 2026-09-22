import apiClient from "./client";

// Matches fastapi_backend routes/blog.py's POST /posts, which expects
// multipart/form-data (title, content, images[]) because it accepts file
// uploads — not a JSON body. Build the FormData in the page component and
// pass it straight through here.
export const createPost = (formData) =>
  apiClient
    .post("/posts", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    })
    .then((r) => r.data);