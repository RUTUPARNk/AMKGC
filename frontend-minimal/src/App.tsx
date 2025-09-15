import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import LoginPage from './pages/LoginPage';
import Dashboard from './pages/EnhancedDashboard';
import KnowledgeGapDashboard from './pages/KnowledgeGapDashboard';
import { ToastProvider } from './components/ToastContext';

const App: React.FC = () => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    // Check if user is already authenticated
    const token = localStorage.getItem('token');
    if (token) {
      setIsAuthenticated(true);
    }
  }, []);

  const handleLogin = (token: string) => {
    localStorage.setItem('token', token);
    setIsAuthenticated(true);
  };

  return (
    <ToastProvider>
      <Router>
        <div className="App">
          <Routes>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/login" element={isAuthenticated ? <Navigate to="/dashboard" replace /> : <LoginPage onLogin={handleLogin} />} />
            <Route path="/dashboard" element={isAuthenticated ? <Dashboard /> : <Navigate to="/login" replace />} />
            <Route path="/knowledge-gap" element={isAuthenticated ? <KnowledgeGapDashboard /> : <Navigate to="/login" replace />} />
          </Routes>
        </div>
      </Router>
    </ToastProvider>
  );
};

export default App;
