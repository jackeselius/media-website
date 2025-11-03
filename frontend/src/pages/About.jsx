import { Card, Text, SimpleGrid, Button, Stack } from '@mantine/core';
import { Link } from 'react-router-dom';

export function AboutPage() {
  const team = [
    { name: 'Jack Eselius', path: '/about/jackeselius' },
    { name: 'Gage Condon', path: '/about/gagecondon' },
    { name: 'Diksha Thach', path: '/about/dikshathach' },
    { name: 'Kate Eselius', path: '/about/kateeselius' },
  ];

  return (
    <Stack spacing="md">
      <Text size="xl">About Us</Text>
      
      <SimpleGrid cols={{ base: 1, sm: 2 }} spacing="md">
        {team.map((member) => (
          <Card key={member.path} shadow="sm" padding="lg" radius="md" withBorder>
            <Stack>
              <Text fw={500}>{member.name}</Text>
              <Button 
                component={Link} 
                to={member.path}
                variant="light"
              >
                View Profile
              </Button>
            </Stack>
          </Card>
        ))}
      </SimpleGrid>
    </Stack>
  );
}