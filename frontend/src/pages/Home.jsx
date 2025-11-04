import { Button, Text, Group, Stack, Image, Center } from '@mantine/core';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

export function HomePage() {
  const { isAuthenticated, username } = useAuth();

  return (
    <Stack spacing="md" align="center">
      <Center>
        <Image src="/penguin.svg" alt="EG Studios Penguin" width={200} height={200} />
      </Center>
      
      {isAuthenticated ? (
        <>
          <Text size="lg">Hi {username}!</Text>
          <Group>
            <Button component={Link} to="/files" variant="light">
              Files
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