import { AppShell, Burger, Group, NavLink, Button, Text } from '@mantine/core';
import { useState } from 'react';
import { useNavigate, useLocation, Outlet } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';

export function MainLayout() {
  const [opened, setOpened] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const { isAuthenticated, username, logout } = useAuth();

  const handleLogout = async () => {
    await logout();
    navigate('/');
  };

  const navigation = [
    { label: 'Home', path: '/' },
    { label: 'Files', path: '/files' },
    ...(isAuthenticated ? [{ label: 'Upload', path: '/upload' }] : []),
    { label: 'About', path: '/about' },
  ];

  return (
    <AppShell
      header={{ height: 60 }}
      navbar={{
        width: 300,
        breakpoint: 'sm',
        // Hide navbar on desktop to avoid double menus; use burger on mobile
        collapsed: { mobile: !opened, desktop: true }
      }}
      padding="md"
    >
      <AppShell.Header>
        <Group h="100%" px="md">
          <Burger opened={opened} onClick={() => setOpened(!opened)} hiddenFrom="sm" size="sm" />
          <Group justify="space-between" style={{ flex: 1 }}>
            <h3 style={{ margin: 0 }}>Media Website</h3>
            <Group>
              <Group ml="xl" gap={0} visibleFrom="sm">
                {navigation.map((item) => (
                  <NavLink
                    key={item.path}
                    label={item.label}
                    active={location.pathname === item.path}
                    onClick={() => navigate(item.path)}
                  />
                ))}
              </Group>
              <Group ml="xl" visibleFrom="sm">
                {isAuthenticated ? (
                  <>
                    <Text size="sm">Welcome, {username}</Text>
                    <Button variant="light" onClick={handleLogout}>
                      Logout
                    </Button>
                  </>
                ) : (
                  <Button variant="light" onClick={() => navigate('/login')}>
                    Login
                  </Button>
                )}
              </Group>
            </Group>
          </Group>
        </Group>
      </AppShell.Header>

      <AppShell.Navbar p="md">
        {/* Navigation items for mobile */}
        {navigation.map((item) => (
          <NavLink
            key={item.path}
            label={item.label}
            active={location.pathname === item.path}
            onClick={() => {
              navigate(item.path);
              setOpened(false);
            }}
          />
        ))}
        {/* Auth status and buttons for mobile */}
        <NavLink
          label={isAuthenticated ? `Welcome, ${username}` : "You are not logged in"}
          disabled
          style={{ marginTop: '1rem' }}
        />
        {isAuthenticated ? (
          <NavLink
            label="Logout"
            onClick={() => {
              handleLogout();
              setOpened(false);
            }}
            style={{ marginTop: '0.5rem' }}
          />
        ) : (
          <NavLink
            label="Login"
            onClick={() => {
              navigate('/login');
              setOpened(false);
            }}
            style={{ marginTop: '0.5rem' }}
          />
        )}
      </AppShell.Navbar>

      <AppShell.Main>
        <Outlet />
      </AppShell.Main>
    </AppShell>
  );
}