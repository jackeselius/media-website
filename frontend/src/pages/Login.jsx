import { TextInput, PasswordInput, Button, Stack, Text } from '@mantine/core';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../utils/api';

export function LoginPage() {
  const [formData, setFormData] = useState({
    username: '',
    password: '',
  });
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const response = await api.post('/api/auth/login/', formData);
      if (response.data.token) {
        localStorage.setItem('token', response.data.token);
        navigate('/');
      }
    } catch (err) {
      setError('Invalid username or password');
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <Stack spacing="md" maw={400} mx="auto" mt={30}>
        <Text size="xl">Login</Text>
        
        {error && (
          <Text c="red" size="sm">
            {error}
          </Text>
        )}

        <TextInput
          label="Username"
          required
          value={formData.username}
          onChange={(e) => setFormData({ ...formData, username: e.target.value })}
        />

        <PasswordInput
          label="Password"
          required
          value={formData.password}
          onChange={(e) => setFormData({ ...formData, password: e.target.value })}
        />

        <Button type="submit">Login</Button>
      </Stack>
    </form>
  );
}