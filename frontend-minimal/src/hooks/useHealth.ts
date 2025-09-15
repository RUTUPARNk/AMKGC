import { useState, useEffect } from 'react';

interface HealthService {
  id: string;
  name: string;
  status: 'healthy' | 'unhealthy' | 'unknown';
  latency: number;
  lastUpdated: string;
}

interface HealthState {
  health: HealthService[] | null;
  loading: boolean;
  error: string | null;
}

export const useHealth = (): HealthState => {
  const [health, setHealth] = useState<HealthService[] | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchHealth = async () => {
      try {
        const response = await fetch('/health');
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        setHealth(data);
        setError(null);
      } catch (err) {
        setError('Failed to fetch health status');
        setHealth(null);
      } finally {
        setLoading(false);
      }
    };

    // Fetch immediately
    fetchHealth();

    // Poll every 5 seconds
    const interval = setInterval(fetchHealth, 5000);

    // Clean up interval on unmount
    return () => clearInterval(interval);
  }, []);

  return { health, loading, error };
};
