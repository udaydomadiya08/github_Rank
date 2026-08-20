import { useEffect, useState } from 'react';
import api from '../api';

const cache = new Map<string, any>();

export function useApi<T>(endpoint: string, refreshInterval = 30000, deps: any[] = []) {
  const [data, setData] = useState<T | null>(cache.get(endpoint) || null);
  const [loading, setLoading] = useState(!cache.has(endpoint));
  const [error, setError] = useState<string | null>(null);

  const fetchData = async () => {
    try {
      const response = await api.get(endpoint);
      cache.set(endpoint, response.data);
      setData(response.data);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'An error occurred while fetching data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // If we have cached data, show it instantly
    if (cache.has(endpoint)) {
      setData(cache.get(endpoint));
      setLoading(false);
    } else {
      setLoading(true);
      setData(null);
    }
    
    // Always fetch fresh data in the background
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
