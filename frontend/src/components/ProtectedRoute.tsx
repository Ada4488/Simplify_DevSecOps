import React from 'react';
import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from '../authContext';

const ProtectedRoute: React.FC = () => {
  const auth = useAuth();

  if (!auth.isAuthenticated) {
    // If not authenticated, redirect to the login page
    // You can also pass the current location to redirect back after login:
    // return <Navigate to="/login" state={{ from: location }} replace />;
    return <Navigate to="/login" replace />;
  }

  // If authenticated, render the child routes
  // Outlet is used by react-router-dom to render nested routes
  return <Outlet />;
};

export default ProtectedRoute;
