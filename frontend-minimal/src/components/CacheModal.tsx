import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { getAllCacheEntries, deleteCacheKey, CacheEntry } from '../services/cacheAPI';

interface CacheModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const CacheModal: React.FC<CacheModalProps> = ({ isOpen, onClose }) => {
  const [cacheEntries, setCacheEntries] = useState<CacheEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [deletingKey, setDeletingKey] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      fetchCacheEntries();
    }
  }, [isOpen]);

  const fetchCacheEntries = async () => {
    setLoading(true);
    setError('');
    try {
      const entries = await getAllCacheEntries();
      setCacheEntries(entries);
    } catch (err) {
      setError('Failed to fetch cache entries');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (key: string) => {
    if (!window.confirm('Are you sure you want to delete this cache entry?')) {
      return;
    }

    setDeletingKey(key);
    try {
      await deleteCacheKey(key);
      // Re-fetch the entries after deletion
      await fetchCacheEntries();
    } catch (err) {
      setError('Failed to delete cache entry');
    } finally {
      setDeletingKey(null);
    }
  };

  if (!isOpen) return null;

  return (
    <motion.div 
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.2 }}
    >
      <motion.div 
        className="bg-white rounded-lg shadow-xl w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col"
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        transition={{ duration: 0.2 }}
      >
        <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
          <h2 className="text-xl font-semibold text-gray-800">Cache Management</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-500 focus:outline-none"
          >
            <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        
        <div className="p-6 flex-grow overflow-auto">
          {error && (
            <motion.div 
              className="mb-4 rounded-md bg-red-50 p-4"
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.2 }}
            >
              <div className="text-sm text-red-700">{error}</div>
            </motion.div>
          )}
          
          {loading ? (
            <div className="flex justify-center items-center h-32">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
            </div>
          ) : (
            <div className="space-y-4">
              {cacheEntries.length === 0 ? (
                <motion.p 
                  className="text-gray-500 text-center py-8"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ duration: 0.2 }}
                >
                  No cache entries found.
                </motion.p>
              ) : (
                cacheEntries.map((entry) => (
                  <motion.div 
                    key={entry.key} 
                    className="border border-gray-200 rounded-lg p-4"
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.2 }}
                  >
                    <div className="flex justify-between items-start">
                      <div className="flex-1 min-w-0">
                        <h3 className="text-sm font-medium text-gray-900 truncate">{entry.key}</h3>
                        <p className="text-xs text-gray-500 mt-1">
                          {new Date(entry.timestamp).toLocaleString()}
                        </p>
                        <div className="mt-2">
                          <pre className="text-xs bg-gray-100 p-2 rounded overflow-x-auto">
                            {JSON.stringify(entry.value, null, 2)}
                          </pre>
                        </div>
                      </div>
                      <button
                        onClick={() => handleDelete(entry.key)}
                        disabled={deletingKey === entry.key}
                        className="ml-4 px-3 py-1 bg-red-500 text-white text-sm rounded hover:bg-red-600 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 disabled:opacity-50"
                      >
                        {deletingKey === entry.key ? 'Deleting...' : 'Delete'}
                      </button>
                    </div>
                  </motion.div>
                ))
              )}
            </div>
          )}
        </div>
        
        <div className="px-6 py-4 border-t border-gray-200 bg-gray-50 flex justify-end">
          <button
            onClick={fetchCacheEntries}
            disabled={loading}
            className="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 disabled:opacity-50"
          >
            Refresh
          </button>
        </div>
      </motion.div>
    </motion.div>
  );
};

export default CacheModal;
