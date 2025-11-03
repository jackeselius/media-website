import { useEffect, useState } from 'react';
import { Table, Button, Image, Group, Text, Stack } from '@mantine/core';
import { Link } from 'react-router-dom';
import api from '../utils/api';

export function FileListPage() {
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadFiles();
  }, []);

  const loadFiles = async () => {
    try {
      // Use JSON API instead of HTML template endpoint
      const response = await api.get('/api/media/files/');
      // support both direct arrays and paginated responses with `results`
      const data = response.data;
      if (Array.isArray(data)) {
        setFiles(data);
      } else if (data && Array.isArray(data.results)) {
        setFiles(data.results);
      } else {
        // Unexpected shape (e.g., HTML error/redirect) — show error instead of breaking .map
        setFiles([]);
        setError('Unexpected response from server while loading files.');
        console.error('Unexpected files payload:', data);
      }
      setError(null);
    } catch (err) {
      setError('Failed to load files');
      console.error('Error loading files:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (fileId) => {
    if (!window.confirm('Are you sure you want to delete this file?')) {
      return;
    }

    try {
      await api.delete(`/api/media/files/${fileId}/`);
      await loadFiles(); // Reload the list
    } catch (err) {
      console.error('Error deleting file:', err);
      alert('Failed to delete file');
    }
  };

  if (loading) {
    return <Text>Loading files...</Text>;
  }

  if (error) {
    return <Text color="red">{error}</Text>;
  }

  return (
    <Stack spacing="md">
      <Group position="apart">
        <Text size="xl">General Files</Text>
        <Button component={Link} to="/upload">
          Upload File
        </Button>
      </Group>

      <Table>
        <Table.Thead>
          <Table.Tr>
            <Table.Th>Icon</Table.Th>
            <Table.Th>File Name</Table.Th>
            <Table.Th>Description</Table.Th>
            <Table.Th>Owner</Table.Th>
            <Table.Th>Actions</Table.Th>
          </Table.Tr>
        </Table.Thead>
        <Table.Tbody>
          {files.map((file) => (
            <Table.Tr key={file.id}>
              <Table.Td>
                {file.icon ? (
                  <Image src={file.icon} alt={file.filename} width={100} />
                ) : (
                  <Text c="dimmed">No Icon</Text>
                )}
              </Table.Td>
              <Table.Td>{file.filename}</Table.Td>
              <Table.Td>{file.description}</Table.Td>
              <Table.Td>{file.owner}</Table.Td>
              <Table.Td>
                <Group>
                  <Button 
                    component="a"
                    href={file.file}
                    target="_blank"
                    variant="light"
                  >
                    Download
                  </Button>
                  <Button 
                    onClick={() => handleDelete(file.id)}
                    color="red"
                    variant="light"
                  >
                    Delete
                  </Button>
                </Group>
              </Table.Td>
            </Table.Tr>
          ))}
        </Table.Tbody>
      </Table>
    </Stack>
  );
}