import { Text, Stack, Image, Grid } from '@mantine/core';

export function JackPage() {
  return (
    <Stack spacing="md">
      <Text size="xl">Jack Eselius</Text>
      
      <Grid>
        <Grid.Col span={{ base: 12, md: 4 }}>
          <Image
            radius="md"
            src="/profile-placeholder.jpg"
            alt="Jack Eselius"
          />
        </Grid.Col>
        <Grid.Col span={{ base: 12, md: 8 }}>
          <Stack spacing="md">
            <Text>
              Hi, I'm Jack Eselius, a software developer and technology enthusiast.
              This website serves as a platform for sharing and managing media files
              within our team.
            </Text>
            
            <Text>
              I specialize in full-stack development, with expertise in:
            </Text>
            
            <ul>
              <li>Python/Django</li>
              <li>React/JavaScript</li>
              <li>Database Design</li>
              <li>Cloud Architecture</li>
            </ul>
          </Stack>
        </Grid.Col>
      </Grid>
    </Stack>
  );
}