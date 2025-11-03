import { TextInput, PasswordInput, Button, Stack, Text } from '@mantine/core';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../utils/api';

export function SignupPage() {
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    confirmPassword: '',
  });
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    try {
      await api.post('/api/auth/signup/', {
        username: formData.username,
        email: formData.email,
        password: formData.password,
      });
      navigate('/login');
    } catch (err) {
      setError(err.response?.data?.message || 'Error creating account');
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <Stack spacing="md" maw={400} mx="auto" mt={30}>
        <Text size="xl">Sign Up</Text>
        
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

        <TextInput
          label="Email"
          type="email"
          required
          value={formData.email}
          onChange={(e) => setFormData({ ...formData, email: e.target.value })}
        />

        <PasswordInput
          label="Password"
          required
          value={formData.password}
          onChange={(e) => setFormData({ ...formData, password: e.target.value })}
        />

        <PasswordInput
          label="Confirm Password"
          required
          value={formData.confirmPassword}
          onChange={(e) => setFormData({ ...formData, confirmPassword: e.target.value })}
        />

        <Button type="submit">Sign Up</Button>
      </Stack>
    </form>
  );
}