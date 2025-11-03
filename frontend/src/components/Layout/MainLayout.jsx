import { AppShell, Burger, Group, NavLink } from '@mantine/core';
import { useState } from 'react';
import { useNavigate, useLocation, Outlet } from 'react-router-dom';

export function MainLayout() {
  const [opened, setOpened] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  const navigation = [
    { label: 'Home', path: '/' },
    { label: 'Files', path: '/files' },
    { label: 'Upload', path: '/upload' },
    { label: 'About', path: '/about' },
  ];

  return (
    <AppShell
      header={{ height: 60 }}
      navbar={{
        width: 300,
        breakpoint: 'sm',
        collapsed: { mobile: !opened }
      }}
      padding="md"
    >
      <AppShell.Header>
        <Group h="100%" px="md">
          <Burger opened={opened} onClick={() => setOpened(!opened)} hiddenFrom="sm" size="sm" />
          <Group justify="space-between" style={{ flex: 1 }}>
            <h3 style={{ margin: 0 }}>Media Website</h3>
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
          </Group>
        </Group>
      </AppShell.Header>

      <AppShell.Navbar p="md">
        {navigation.map((item) => (
          <NavLink
            key={item.path}
            label={item.label}
            active={location.pathname === item.path}
            onClick={() => navigate(item.path)}
          />
        ))}
      </AppShell.Navbar>

      <AppShell.Main>
        <Outlet />
      </AppShell.Main>
    </AppShell>
  );
}