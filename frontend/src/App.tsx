import React from 'react';
import { Routes, Route, Link, Navigate, useNavigate } from 'react-router-dom';
import { useAuth } from './authContext';
import LoginPage from './components/LoginPage';
import RegisterPage from './components/RegisterPage';
import DashboardPage from './components/DashboardPage';
import NotFoundPage from './components/NotFoundPage';
import ProtectedRoute from './components/ProtectedRoute';

function App() {
  const auth = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    auth.logout();
    navigate('/login'); // Redirect to login after logout
  };

  return (
    <div>
      <nav style={{ padding: '1rem', backgroundColor: '#f0f0f0', marginBottom: '1rem' }}>
        <Link to="/" style={{ marginRight: '1rem' }}>Home</Link>
        {!auth.isAuthenticated && <Link to="/login" style={{ marginRight: '1rem' }}>Login</Link>}
        {!auth.isAuthenticated && <Link to="/register" style={{ marginRight: '1rem' }}>Register</Link>}
        {auth.isAuthenticated && <Link to="/dashboard" style={{ marginRight: '1rem' }}>Dashboard</Link>}
        {auth.isAuthenticated && (
          <button onClick={handleLogout} style={{ marginLeft: 'auto' }}>
            Logout
          </button>
        )}
      </nav>

      <div style={{ padding: '1rem' }}>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          
          {/* Protected Routes */}
          <Route element={<ProtectedRoute />}>
            <Route path="/dashboard" element={<DashboardPage />} />
          </Route>
          
          <Route 
            path="/" 
            element={auth.isAuthenticated ? <Navigate to="/dashboard" /> : <Navigate to="/login" />} 
          />
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </div>
    </div>
  );
}

export default App;
