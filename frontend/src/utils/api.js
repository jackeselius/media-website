import axios from 'axios';

// Prefer an explicit API base URL when provided (helps mobile dev and non-standard setups)
const explicitBase = import.meta.env.VITE_API_BASE_URL;

// Default behavior:
// - Production: same-origin (empty base URL)
// - Development: http://localhost:8000 unless VITE_API_BASE_URL overrides
const baseURL = explicitBase ?? (import.meta.env.PROD ? '' : 'http://localhost:8000');

// Create axios instance with common config
const api = axios.create({
  baseURL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // Kept for CSRF with session endpoints (not required for token auth)
});

// Add response interceptor for handling common errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized (redirect to SPA login). Keep it simple and explicit so it works outside React tree.
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Request interceptor to get CSRF token
api.interceptors.request.use((config) => {
  // Get CSRF token from cookie if it exists
  const csrfToken = document.cookie
    .split('; ')
    .find(row => row.startsWith('csrftoken='))
    ?.split('=')[1];

  if (csrfToken) {
    config.headers['X-CSRFToken'] = csrfToken;
  }
  return config;
});

export default api;