import axios from 'axios';

// Create axios instance with common config
const api = axios.create({
  baseURL: import.meta.env.PROD ? '' : 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // Required for CSRF token
});

// Add response interceptor for handling common errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized (redirect to login)
      window.location.href = '/accounts/login/';
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