import { useEffect, useState } from 'react';
import { Table, Text, Stack, Badge, NumberFormatter, Group } from '@mantine/core';
import api from '../utils/api';

export function TradingDashboardPage() {
  const [trades, setTrades] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [totalCount, setTotalCount] = useState(null);
  const [lastTradeDate, setLastTradeDate] = useState(null);
  const [updatedAt, setUpdatedAt] = useState(null);

  useEffect(() => {
    loadTrades();
    // Optional: set up polling for real-time updates
    // const interval = setInterval(loadTrades, 30000); // refresh every 30s
    // return () => clearInterval(interval);
  }, []);

  const loadTrades = async () => {
    try {
      const response = await api.get('/api/trading/trades/', { params: { page_size: 100 } });
      const data = response.data;
      if (Array.isArray(data)) {
        setTrades(data);
        setTotalCount(data.length);
        const maxDate = data.reduce((acc, t) => (t.trade_date && (!acc || t.trade_date > acc) ? t.trade_date : acc), null);
        setLastTradeDate(maxDate);
      } else if (data && Array.isArray(data.results)) {
        setTrades(data.results);
        setTotalCount(typeof data.count === 'number' ? data.count : data.results.length);
        const maxDate = data.results.reduce((acc, t) => (t.trade_date && (!acc || t.trade_date > acc) ? t.trade_date : acc), null);
        setLastTradeDate(maxDate);
      } else {
        setTrades([]);
        setTotalCount(0);
        setLastTradeDate(null);
      }
      setError(null);
      setUpdatedAt(new Date().toISOString());
    } catch (err) {
      setError('Failed to load trades');
      console.error('Error loading trades:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <Text>Loading politician trades...</Text>;
  }

  if (error) {
    return <Text c="red">{error}</Text>;
  }

  return (
    <Stack spacing="md">
      <Text size="xl">Politician Trading Dashboard</Text>
      <Text size="sm" c="dimmed">
        Real-time view of politician stock trades. Copy trading feature coming soon.
      </Text>

      <Group gap="lg">
        <Text size="sm" c="dimmed">Total trades: {totalCount ?? '—'}</Text>
        <Text size="sm" c="dimmed">Last trade date: {lastTradeDate || '—'}</Text>
        <Text size="sm" c="dimmed">Updated: {updatedAt ? new Date(updatedAt).toLocaleString() : '—'}</Text>
      </Group>

      {trades.length === 0 ? (
        <Text c="dimmed">No trades available yet.</Text>
      ) : (
        <Table highlightOnHover>
          <Table.Thead>
            <Table.Tr>
              <Table.Th>Politician</Table.Th>
              <Table.Th>Ticker</Table.Th>
              <Table.Th>Action</Table.Th>
              <Table.Th>Trade Date</Table.Th>
              <Table.Th>Amount</Table.Th>
              <Table.Th>Disclosure Date</Table.Th>
            </Table.Tr>
          </Table.Thead>
          <Table.Tbody>
            {trades.map((trade) => (
              <Table.Tr key={trade.id ?? `${trade.politician_name}-${trade.ticker}-${trade.trade_date}`}>
                <Table.Td>{trade.politician_name}</Table.Td>
                <Table.Td>
                  <Text fw={700}>{trade.ticker}</Text>
                </Table.Td>
                <Table.Td>
                  <Badge color={trade.action === 'BUY' ? 'green' : 'red'} variant="light">
                    {trade.action}
                  </Badge>
                </Table.Td>
                <Table.Td>{trade.trade_date}</Table.Td>
                <Table.Td>
                  {trade.amount ? (
                    <NumberFormatter
                      value={trade.amount}
                      prefix="$"
                      thousandSeparator
                      decimalScale={2}
                    />
                  ) : (
                    <Text c="dimmed" size="sm">N/A</Text>
                  )}
                </Table.Td>
                <Table.Td>{trade.disclosure_date || '—'}</Table.Td>
              </Table.Tr>
            ))}
          </Table.Tbody>
        </Table>
      )}
    </Stack>
  );
}
