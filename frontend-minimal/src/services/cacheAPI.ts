import api from './api';

export interface CacheEntry {
  key: string;
  value: any;
  timestamp: string;
}

export const getAllCacheEntries = async (): Promise<CacheEntry[]> => {
  try {
    const response = await api.get('/api/cache');
    return response.data;
  } catch (error) {
    console.error('Failed to fetch cache entries:', error);
    throw error;
  }
};

export const deleteCacheKey = async (key: string): Promise<void> => {
  try {
    await api.delete(`/api/cache/${key}`);
  } catch (error) {
    console.error(`Failed to delete cache key ${key}:`, error);
    throw error;
  }
};
