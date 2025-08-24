import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { ThemeProvider } from './contexts/ThemeContext';

import ProtectedRoute from './components/ProtectedRoute';
import {
  Login,
  Register,
  Dashboard,
  Credentials,
  ApiKeys,
  Usage,
} from './pages';
import './App.css';

function App() {
  return (
    <ThemeProvider>
      <Router>
        <AuthProvider>
          <div className="min-h-screen bg-background text-foreground">
            <Routes>
              {/* Public routes */}
              <Route path="/login" element={<Login />} />
              <Route path="/register" element={<Register />} />
              
              {/* Protected routes */}
              <Route path="/" element={
                <ProtectedRoute>
                  <Navigate to="/dashboard" replace />
                </ProtectedRoute>
              } />
              <Route path="/dashboard" element={
                <ProtectedRoute>
                  <Dashboard />
                </ProtectedRoute>
              } />
              <Route path="/credentials" element={
                <ProtectedRoute>
                  <Credentials />
                </ProtectedRoute>
              } />
              <Route path="/api-keys" element={
                <ProtectedRoute>
                  <ApiKeys />
                </ProtectedRoute>
              } />
              <Route path="/usage" element={
                <ProtectedRoute>
                  <Usage />
                </ProtectedRoute>
              } />
              
              {/* Catch all route */}
              <Route path="*" element={<Navigate to="/dashboard" replace />} />
            </Routes>
          </div>
        </AuthProvider>
      </Router>
    </ThemeProvider>
  );
}

export default App;
