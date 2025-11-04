import React from 'react';
import ReactDOM from 'react-dom/client';
import { createBrowserRouter, RouterProvider } from 'react-router-dom';
import { MantineProvider, createTheme } from '@mantine/core';
import App from './App';
import './index.css';
import '@mantine/core/styles.css';

// Import pages
import { HomePage } from './pages/Home';
import { FileListPage } from './pages/FileList';
import { UploadPage } from './pages/Upload';
import { AboutPage } from './pages/About';
import { JackEseliusPage } from './pages/JackEselius';
import { GageCondonPage } from './pages/GageCondon';
import { DikshaThachPage } from './pages/DikshaThach';
import { KateEseliusPage } from './pages/KateEselius';
import { LoginPage } from './pages/Login';
// Signup is disabled; keep route redirected to login to avoid dead links
import { Navigate } from 'react-router-dom';
import ProtectedRoute from './components/Auth/ProtectedRoute';

const router = createBrowserRouter([
  {
    path: '/',
    element: <App />,
    children: [
      {
        index: true,
        element: <HomePage />,
      },
      {
        path: 'files',
        element: (
          <ProtectedRoute>
            <FileListPage />
          </ProtectedRoute>
        ),
      },
      {
        path: 'upload',
        element: (
          <ProtectedRoute>
            <UploadPage />
          </ProtectedRoute>
        ),
      },
      {
        path: 'about',
        element: <AboutPage />,
      },
      {
        path: 'about/jackeselius',
        element: <JackEseliusPage />,
      },
      {
        path: 'about/gagecondon',
        element: <GageCondonPage />,
      },
      {
        path: 'about/dikshathach',
        element: <DikshaThachPage />,
      },
      {
        path: 'about/kateeselius',
        element: <KateEseliusPage />,
      },
      {
        path: 'login',
        element: <LoginPage />,
      },
      {
        path: 'signup',
        element: <Navigate to="/login" replace />,
      },
    ],
  },
]);

const theme = createTheme({
  colorScheme: 'dark',
  primaryColor: 'green',
  colors: {
    // Neon green custom palette
    green: [
      '#e6ffe6',
      '#ccffcc',
      '#99ff99',
      '#66ff66',
      '#33ff33',
      '#00ff00', // neon green base
      '#00cc00',
      '#009900',
      '#006600',
      '#003300',
    ],
  },
  defaultRadius: 'md',
  components: {
    Button: {
      defaultProps: {
        color: 'green',
      },
    },
    NavLink: {
      styles: {
        root: {
          '&[data-active]': {
            backgroundColor: 'rgba(0, 255, 0, 0.1)',
            borderLeft: '3px solid #00ff00',
          },
          '&:hover': {
            backgroundColor: 'rgba(0, 255, 0, 0.05)',
          },
        },
      },
    },
  },
});

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <MantineProvider theme={theme} defaultColorScheme="dark">
      <RouterProvider router={router} />
    </MantineProvider>
  </React.StrictMode>,
);
