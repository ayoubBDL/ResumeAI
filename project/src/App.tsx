import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { createClient } from '@supabase/supabase-js';
import { PayPalScriptProvider } from "@paypal/react-paypal-js";
import Dashboard from './pages/Dashboard';
import SavedJobs from './pages/SavedJobs';
import MyResumes from './pages/MyResumes';
import Login from './pages/Login';
import SignUp from './pages/SignUp';
import LandingPage from './pages/LandingPage';
import AuthCallback from './pages/AuthCallback';
import Billing from './pages/Billing';
import Checkout from './pages/Checkout';
import SuccessPage from './pages/SuccessPage';
import CancelPage from './pages/CancelPage';
import Layout from './components/Layout';
import { AuthProvider, useAuth } from './context/AuthContext';
import { ToastProvider } from './context/ToastContext';
import { CreditsProvider } from './context/CreditsContext';

const supabase = createClient(
  import.meta.env.VITE_SUPABASE_URL,
  import.meta.env.VITE_SUPABASE_ANON_KEY
);

interface PrivateRouteProps {
  children: React.ReactNode;
}

const PrivateRoute: React.FC<PrivateRouteProps> = ({ children }) => {
  const { user, session, loading } = useAuth();
  
  if (loading) {
    return <div>Loading...</div>; // Or a loading spinner
  }

  if (!user) {
    return <Navigate to="/login" />;
  }

  return <Layout>{children}</Layout>;
};

function App() {
  return (
    <PayPalScriptProvider
      options={{
        clientId: import.meta.env.VITE_PAYPAL_CLIENT_ID || "",
        vault: true,
        intent: "capture"
      }}
    >
      <AuthProvider>
        <CreditsProvider>
          <ToastProvider>
            <BrowserRouter>
              <Routes>
                <Route path="/" element={<LandingPage />} />
                <Route path="/login" element={<Login />} />
                <Route path="/signup" element={<SignUp />} />
                <Route path="/auth/callback" element={<AuthCallback />} />
                <Route path="/success" element={<SuccessPage />} />
                <Route path="/cancel" element={<CancelPage />} />
                
                {/* Protected Routes */}
                <Route path="/dashboard" element={
                  <PrivateRoute>
                    <Dashboard />
                  </PrivateRoute>
                } />
                <Route path="/my-resumes" element={
                  <PrivateRoute>
                    <MyResumes />
                  </PrivateRoute>
                } />
                <Route path="/saved-jobs" element={
                  <PrivateRoute>
                    <SavedJobs />
                  </PrivateRoute>
                } />
                <Route path="/billing" element={
                  <PrivateRoute>
                    <Billing />
                  </PrivateRoute>
                } />
                <Route path="/checkout" element={
                  <PrivateRoute>
                    <Checkout />
                  </PrivateRoute>
                } />
              </Routes>
            </BrowserRouter>
          </ToastProvider>
        </CreditsProvider>
      </AuthProvider>
    </PayPalScriptProvider>
  );
}

export default App;