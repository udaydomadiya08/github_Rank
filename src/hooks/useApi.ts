import { useEffect, useState } from 'react';
import api from '../api';

export function useApi<T>(endpoint: string, refreshInterval = 30000, deps: any[] = []) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = async () => {
    try {
      const response = await api.get(endpoint);
      setData(response.data);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'An error occurred while fetching data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    setLoading(true);
    fetchData();

    let intervalId: any;
    if (refreshInterval > 0) {
      intervalId = setInterval(fetchData, refreshInterval);
    }

    return () => {
      if (intervalId) clearInterval(intervalId);
    };
  }, deps);

  return { data, loading, error, refetch: fetchData };
}
