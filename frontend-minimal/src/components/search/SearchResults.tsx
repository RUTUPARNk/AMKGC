import React from 'react';
import { useSearchStore } from '../stores/searchStore';
import { ResultItem } from './ResultItem';

export const SearchResults: React.FC = () => {
  const { results, loading, error } = useSearchStore();
  
  if (loading) {
    return (
      <div className="py-4 text-center">
        <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500 mx-auto"></div>
        <p className="mt-2 text-sm text-gray-500">Searching...</p>
      </div>
    );
  }
  
  if (error) {
    return (
      <div className="py-4 text-center">
        <p className="text-sm text-red-500">Error: {error}</p>
        <button 
          className="mt-2 text-sm text-blue-500 hover:text-blue-700"
          onClick={() => window.location.reload()}
        >
          Try again
        </button>
      </div>
    );
  }
  
  if (results.length === 0 && !loading) {
    return (
      <div className="py-4 text-center">
        <p className="text-sm text-gray-500">No results found</p>
      </div>
    );
  }
  
  return (
    <div className="py-2">
      <h3 className="text-sm font-medium text-gray-900 mb-2">
        Search Results ({results.length})
      </h3>
      
      <div className="space-y-2">
        {results.map((result) => (
          <ResultItem key={result.nodeId} result={result} />
        ))}
      </div>
      
      {results.length > 0 && (
        <div className="mt-4 text-xs text-gray-500">
          Results sorted by relevance. Semantic search finds conceptually similar content.
        </div>
      )}
    </div>
  );
};
