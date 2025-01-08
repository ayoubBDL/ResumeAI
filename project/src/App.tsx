import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { createClient } from '@supabase/supabase-js';
import Dashboard from './pages/Dashboard';
import SavedJobs from './pages/SavedJobs';
import MyResumes from './pages/MyResumes';
import Login from './pages/Login.tsx';
import SignUp from './pages/SignUp.tsx';
import LandingPage from './pages/LandingPage.tsx';
import { AuthProvider, useAuth } from './context/AuthContext';

const supabase = createClient(
  import.meta.env.VITE_SUPABASE_URL,
  import.meta.env.VITE_SUPABASE_ANON_KEY
);

function PrivateRoute({ children }) {
  const { session } = useAuth();
  return session ? children : <Navigate to="/login" />;
}

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<SignUp />} />
          <Route path="/dashboard" element={
            <PrivateRoute>
              <Dashboard />
            </PrivateRoute>
          } />
          <Route path="/saved-jobs" element={
            <PrivateRoute>
              <SavedJobs />
            </PrivateRoute>
          } />
          <Route path="/my-resumes" element={
            <PrivateRoute>
              <MyResumes />
            </PrivateRoute>
          } />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;