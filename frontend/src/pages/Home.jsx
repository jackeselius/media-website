import { useEffect, useState } from 'react';
import { Button, Text, Group, Stack } from '@mantine/core';
import { Link } from 'react-router-dom';
import api from '../utils/api';

export function HomePage() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Fetch user info from Django
    api.get('/accounts/user-info/')
      .then(response => {
        setUser(response.data);
      })
      .catch(error => {
        console.error('Error fetching user:', error);
        setUser(null);
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  const handleLogout = async () => {
    try {
      await api.post('/accounts/logout/');
      setUser(null);
      // route to the SPA login page
      window.location.href = '/login';
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  if (loading) {
    return <Text>Loading...</Text>;
  }

  return (
    <Stack spacing="md">
      {user ? (
        <>
          <Text size="lg">Hi {user.username}!</Text>
          <Group>
            <Button component={Link} to="/files" variant="light">
              Files
            </Button>
            <Button onClick={handleLogout} color="red">
              Log Out
            </Button>
          </Group>
        </>
      ) : (
        <>
          <Text size="lg">You are not logged in</Text>
          <Group>
            <Button component={Link} to="/login" variant="light">
              Log In
            </Button>
            <Button component={Link} to="/about" variant="light">
              About Me
            </Button>
          </Group>
        </>
      )}
    </Stack>
  );
}