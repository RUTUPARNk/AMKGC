import React from 'react';
import LoginForm from '../components/LoginForm';

interface LoginPageProps {
  onLogin: (token: string) => void;
}

const LoginPage: React.FC<LoginPageProps> = ({ onLogin }) => {
  return (
    <div className="min-h-screen bg-gray-100">
      <LoginForm onLogin={onLogin} />
    </div>
  );
};

export default LoginPage;
