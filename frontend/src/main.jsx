import React from 'react';
import ReactDOM from 'react-dom/client';
import { createBrowserRouter, RouterProvider } from 'react-router-dom';
import { MantineProvider } from '@mantine/core';
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
import { SignupPage } from './pages/Signup';
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
        element: <FileListPage />,
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
        element: <SignupPage />,
      },
    ],
  },
]);

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <MantineProvider>
      <RouterProvider router={router} />
    </MantineProvider>
  </React.StrictMode>,
);
