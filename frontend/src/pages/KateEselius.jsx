import { Text, Stack, Image, Grid } from '@mantine/core';

export function KateEseliusPage() {
  return (
    <Stack spacing="md">
      <Text size="xl">Kate Eselius</Text>
      
      <Grid>
        <Grid.Col span={{ base: 12, md: 4 }}>
          <Image
            radius="md"
            src="/profile-placeholder.jpg"
            alt="Kate Eselius"
          />
        </Grid.Col>
        <Grid.Col span={{ base: 12, md: 8 }}>
          <Stack spacing="md">
            <Text>Profile information coming soon.</Text>
          </Stack>
        </Grid.Col>
      </Grid>
    </Stack>
  );
}