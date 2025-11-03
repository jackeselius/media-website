import { createContext, useContext, useState, useEffect } from 'react';
import api from '../utils/api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [username, setUsername] = useState(null);
  const [loading, setLoading] = useState(true);

  // Check authentication status on mount
  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      api.defaults.headers.common['Authorization'] = `Token ${token}`;
      // Try to get user info to verify token
      api.get('/api/auth/user/')
        .then(response => {
          setUsername(response.data.username);
          setIsAuthenticated(true);
        })
        .catch(() => {
          localStorage.removeItem('token');
          delete api.defaults.headers.common['Authorization'];
        })
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

  const login = async (credentials) => {
    const response = await api.post('/api/auth/login/', credentials);
    const token = response.data.token;
    localStorage.setItem('token', token);
    api.defaults.headers.common['Authorization'] = `Token ${token}`;
    setIsAuthenticated(true);
    setUsername(credentials.username);
  };

  const logout = async () => {
    try {
      await api.post('/api/auth/logout/');
    } finally {
      localStorage.removeItem('token');
      delete api.defaults.headers.common['Authorization'];
      setIsAuthenticated(false);
      setUsername(null);
    }
  };

  return (
    <AuthContext.Provider value={{ isAuthenticated, username, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);