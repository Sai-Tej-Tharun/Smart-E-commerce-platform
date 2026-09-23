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

// Matches GET /posts?page=&limit=&search=
// Returns: { items, total, page, limit, total_pages }

export const listPosts = ({
  page = 1,
  limit = 10,
  search = "",
} = {}) => {
  const params = { page, limit };

  if (search) {
    params.search = search;
  }

  return apiClient
    .get("/posts", { params })
    .then((r) => r.data);
};

// Get a single post

export const getPost = (postId) =>
  apiClient
    .get(`/posts/${postId}`)
    .then((r) => r.data);

// Get comments for a post

export const listComments = (postId) =>
  apiClient
    .get(`/posts/${postId}/comments`)
    .then((r) => r.data);

// Add a comment to a post

export const addComment = (postId, text) =>
  apiClient
    .post(`/posts/${postId}/comments`, { text })
    .then((r) => r.data);

// Like a post

export const likePost = (postId) =>
  apiClient
    .post(`/posts/${postId}/like`)
    .then((r) => r.data);

// Unlike a post

export const unlikePost = (postId) =>
  apiClient
    .delete(`/posts/${postId}/like`);