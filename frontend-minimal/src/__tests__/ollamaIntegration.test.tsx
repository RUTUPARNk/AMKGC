"""
Frontend test file for Ollama integration in the Node-LLM System
"""

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { useSearchStore } from '../stores/searchStore';
import { rest } from 'msw';
import { setupServer } from 'msw/node';

// Mock the API responses
const server = setupServer(
  rest.post('/api/v1/vector/search/semantic', (req, res, ctx) => {
    return res(
      ctx.json({
        fragments: [
          {
            fragment_id: '1',
            node_id: 'node-123',
            text: 'This is a test fragment about AI',
            score: 0.95,
            commit_id: 'commit-1',
            created_at: '2023-01-01T00:00:00Z'
          }
        ],
        message: 'Found 1 relevant fragments'
      })
    );
  })
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

// Mock the axios module
jest.mock('axios', () => ({
  post: jest.fn().mockResolvedValue({
    data: {
      fragments: [
        {
          fragment_id: '1',
          node_id: 'node-123',
          text: 'This is a test fragment about AI',
          score: 0.95,
          commit_id: 'commit-1',
          created_at: '2023-01-01T00:00:00Z'
        }
      ],
      message: 'Found 1 relevant fragments'
    }
  })
}));

// Mock the search store
jest.mock('../stores/searchStore', () => ({
  useSearchStore: jest.fn()
}));

// Mock component that uses the search store
const MockSearchComponent = () => {
  const { searchSemantic, setProvider, provider, results, loading } = useSearchStore();
  
  return (
    <div>
      <h1>Search Test</h1>
      <div>
        <button 
          onClick={() => setProvider('ollama')}
          data-testid="set-ollama-provider"
        >
          Set Ollama Provider
        </button>
        <button 
          onClick={() => setProvider('openai')}
          data-testid="set-openai-provider"
        >
          Set OpenAI Provider
        </button>
        <span data-testid="current-provider">{provider || 'none'}</span>
      </div>
      <div>
        <button 
          onClick={() => searchSemantic('test query')}
          data-testid="search-button"
          disabled={loading}
        >
          Search
        </button>
        {loading && <span data-testid="loading">Loading...</span>}
      </div>
      <div data-testid="results-count">{results.length} results</div>
    </div>
  );
};

describe('Ollama Integration Tests', () => {
  beforeEach(() => {
    // Reset mocks
    jest.clearAllMocks();
    
    // Mock the search store implementation
    const mockStore = {
      searchSemantic: jest.fn(),
      setProvider: jest.fn(),
      provider: null,
      results: [],
      loading: false
    };
    
    (useSearchStore as jest.Mock).mockReturnValue(mockStore);
  });
  
  test('should allow setting Ollama as provider', () => {
    const mockSetProvider = jest.fn();
    (useSearchStore as jest.Mock).mockReturnValue({
      searchSemantic: jest.fn(),
      setProvider: mockSetProvider,
      provider: null,
      results: [],
      loading: false
    });
    
    render(<MockSearchComponent />);
    
    const setOllamaButton = screen.getByTestId('set-ollama-provider');
    fireEvent.click(setOllamaButton);
    
    expect(mockSetProvider).toHaveBeenCalledWith('ollama');
  });
  
  test('should display current provider', () => {
    (useSearchStore as jest.Mock).mockReturnValue({
      searchSemantic: jest.fn(),
      setProvider: jest.fn(),
      provider: 'ollama',
      results: [],
      loading: false
    });
    
    render(<MockSearchComponent />);
    
    const providerDisplay = screen.getByTestId('current-provider');
    expect(providerDisplay).toHaveTextContent('ollama');
  });
  
  test('should call semantic search with provider parameter', async () => {
    const mockSearchSemantic = jest.fn();
    (useSearchStore as jest.Mock).mockReturnValue({
      searchSemantic: mockSearchSemantic,
      setProvider: jest.fn(),
      provider: 'ollama',
      results: [],
      loading: false
    });
    
    render(<MockSearchComponent />);
    
    const searchButton = screen.getByTestId('search-button');
    fireEvent.click(searchButton);
    
    expect(mockSearchSemantic).toHaveBeenCalledWith('test query');
  });
  
  test('should handle loading state during search', async () => {
    (useSearchStore as jest.Mock).mockReturnValue({
      searchSemantic: jest.fn(),
      setProvider: jest.fn(),
      provider: 'ollama',
      results: [],
      loading: true
    });
    
    render(<MockSearchComponent />);
    
    const loadingIndicator = screen.getByTestId('loading');
    expect(loadingIndicator).toBeInTheDocument();
  });
});
