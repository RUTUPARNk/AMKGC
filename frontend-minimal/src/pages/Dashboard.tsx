import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import SearchBar from '../components/SearchBar';
import ChatWindow from '../components/ChatWindow';
import CacheModal from '../components/CacheModal';
import { GraphView } from '../components/GraphView';
import { fetchOllamaModels } from '../hooks/useSessionWS';

const Dashboard: React.FC = () => {
  const [isCacheModalOpen, setIsCacheModalOpen] = useState(false);
  const [viewMode, setViewMode] = useState<'chat' | 'graph'>('chat');
  const [selectedSessionId, setSelectedSessionId] = useState<string>('default-session');
  const [provider, setProvider] = useState<'qwen' | 'ollama'>('qwen');
  const [model, setModel] = useState<string>('llama2');
  const [ollamaModels, setOllamaModels] = useState<string[]>([]);
  const [isLoadingModels, setIsLoadingModels] = useState<boolean>(false);
  const navigate = useNavigate();

  const handleLogout = () => {
    localStorage.removeItem('token');
    navigate('/login');
  };

  const handleSearch = (query: string) => {
    console.log('Searching for:', query);
    // Implement search functionality
  };

  // Fetch Ollama models when provider changes to Ollama
  useEffect(() => {
    if (provider === 'ollama') {
      const loadModels = async () => {
        setIsLoadingModels(true);
        try {
          const models = await fetchOllamaModels();
          setOllamaModels(models);
          // Set default model if available
          if (models.length > 0 && !models.includes(model)) {
            setModel(models[0]);
          } else if (models.length === 0) {
            // No models available
            setModel('');
          }
        } catch (error) {
          console.error('Error fetching Ollama models:', error);
          setOllamaModels([]);
          setModel('');
        } finally {
          setIsLoadingModels(false);
        }
      };
      loadModels();
    }
  }, [provider]);

  const handleCacheIconClick = () => {
    setIsCacheModalOpen(true);
  };

  const chatSessions = [
    { id: 'default-session', title: 'General Chat' },
    { id: 'project-session', title: 'Project Discussion' },
    { id: 'support-session', title: 'Technical Support' },
  ];

  return (
    <div className="flex flex-col h-screen bg-gray-100">
      {/* Top Navbar */}
      <nav className="bg-white shadow-sm">
        <div className="px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <div className="flex-shrink-0 flex items-center">
                <div className="h-8 w-8 rounded-full bg-indigo-500 flex items-center justify-center text-white font-bold">
                  N
                </div>
                <span className="ml-2 text-xl font-semibold text-gray-900">Node LLM System</span>
              </div>
            </div>
            <div className="flex items-center">
              <div className="ml-3 relative">
                <div className="flex items-center space-x-4">
                  <div className="flex-shrink-0">
                    <div className="h-8 w-8 rounded-full bg-gray-200 flex items-center justify-center text-gray-500">
                      U
                    </div>
                  </div>
                  <button
                    onClick={handleLogout}
                    className="px-3 py-1 text-sm font-medium text-gray-700 hover:text-gray-900 focus:outline-none"
                  >
                    Logout
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </nav>

      <div className="flex flex-1 overflow-hidden">
        {/* Left Sidebar */}
        <div className="w-64 bg-white shadow-md overflow-y-auto">
          <div className="p-4">
            <h2 className="text-lg font-semibold text-gray-800 mb-4">Chat Sessions</h2>
            <ul className="space-y-2">
              {chatSessions.map((session) => (
                <li key={session.id}>
                  <button 
                    onClick={() => setSelectedSessionId(session.id)}
                    className={`w-full text-left px-3 py-2 rounded-md ${selectedSessionId === session.id ? 'bg-indigo-100 text-indigo-700' : 'text-gray-700 hover:bg-gray-100'}`}
                  >
                    {session.title}
                  </button>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Main Content */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Search Bar */}
          <div className="bg-white shadow-sm p-4">
            <div className="flex items-center justify-between">
              <SearchBar onSearch={handleSearch} onCacheIconClick={handleCacheIconClick} />
              <div className="flex items-center space-x-4">
                <div className="flex flex-col space-y-2">
                  <select
                    value={provider}
                    onChange={(e) => setProvider(e.target.value as 'qwen' | 'ollama')}
                    className="border p-2 rounded"
                  >
                    <option value="qwen">Qwen (Cloud)</option>
                    <option value="ollama">Ollama (Local)</option>
                  </select>
                  
                  {provider === 'ollama' && (
                    <select
                      value={model}
                      onChange={(e) => setModel(e.target.value)}
                      className="border p-2 rounded"
                      disabled={isLoadingModels}
                    >
                      {isLoadingModels ? (
                        <option>Loading models...</option>
                      ) : (
                        ollamaModels.map((m) => (
                          <option key={m} value={m}>
                            {m}
                          </option>
                        ))
                      )}
                    </select>
                  )}
                </div>
                
                <div className="flex rounded-md shadow-sm">
                  <button
                    type="button"
                    onClick={() => setViewMode('chat')}
                    className={`px-4 py-2 text-sm font-medium rounded-l-md ${viewMode === 'chat' ? 'bg-indigo-600 text-white' : 'bg-white text-gray-700 hover:bg-gray-50'}`}
                  >
                    Chat View
                  </button>
                  <button
                    type="button"
                    onClick={() => setViewMode('graph')}
                    className={`px-4 py-2 text-sm font-medium rounded-r-md ${viewMode === 'graph' ? 'bg-indigo-600 text-white' : 'bg-white text-gray-700 hover:bg-gray-50'}`}
                  >
                    Graph View
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* Dynamic Content Area */}
          <div className="flex-1 overflow-hidden">
            {viewMode === 'chat' ? <ChatWindow sessionId={selectedSessionId} provider={provider} model={model} /> : <GraphView sessionId={selectedSessionId} />}
          </div>
        </div>
      </div>

      {/* Cache Management Modal */}
      <CacheModal isOpen={isCacheModalOpen} onClose={() => setIsCacheModalOpen(false)} />
    </div>
  );
};

export default Dashboard;
