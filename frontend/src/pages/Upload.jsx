import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button, TextInput, Stack, Text, FileInput } from '@mantine/core';
import { useForm } from '@mantine/form';
import api from '../utils/api';

export function UploadPage() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);

  const form = useForm({
    initialValues: {
      file: null,
      description: '',
    },
    validate: {
      file: (value) => !value ? 'File is required' : null,
    },
  });

  const handleSubmit = async (values) => {
    setLoading(true);
    try {
      const formData = new FormData();
      formData.append('file', values.file);
      formData.append('description', values.description);

      await api.post('/media/upload/', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      navigate('/files');
    } catch (error) {
      console.error('Upload failed:', error);
      alert('Failed to upload file');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Stack spacing="md">
      <Text size="xl">Upload General File</Text>

      <form onSubmit={form.onSubmit(handleSubmit)}>
        <Stack spacing="md">
          <FileInput
            required
            label="File"
            placeholder="Choose file"
            {...form.getInputProps('file')}
          />

          <TextInput
            label="Description"
            placeholder="File description"
            {...form.getInputProps('description')}
          />

          <Button type="submit" loading={loading}>
            Upload File
          </Button>
        </Stack>
      </form>
    </Stack>
  );
}