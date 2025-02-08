import React, { useEffect, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { CheckCircle } from 'lucide-react';

const SuccessPage: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user } = useAuth();
  const { showToast } = useToast();
  const [isProcessing, setIsProcessing] = useState(true);

  useEffect(() => {
    const verifySubscription = async () => {
      try {
        // Get subscription details from navigation state
        const state = location.state as { 
          subscriptionId?: string
        };

        const subscriptionId = state?.subscriptionId;
        
        if (!subscriptionId) {
          showToast('No subscription details found', 'error');
          navigate('/billing');
          return;
        }

        // Show success toast
        showToast('Subscription successfully activated!', 'success');
      } catch (error) {
        console.error('Subscription verification error:', error);
        showToast('There was an issue processing your subscription', 'error');
        navigate('/billing');
      } finally {
        setIsProcessing(false);
      }
    };

    if (user) {
      if(location.state && location.state.subscriptionId){
        verifySubscription();
      }else{
        setIsProcessing(false);
      }
    }
  }, [user, location.state, navigate, showToast]);

  if (isProcessing) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-t-2 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-xl">Processing your {location.state.subscriptionId? "subscription" : "purchase"}...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100 flex items-center justify-center">
      <div className="bg-white p-8 rounded-lg shadow-xl text-center max-w-md w-full">
        <CheckCircle className="mx-auto h-24 w-24 text-green-500 mb-4" />
        <h1 className="text-3xl font-bold mb-4">{location.state.subscriptionId? "Subscription" : "Purchase"} Successful!</h1>
        <p className="text-gray-600 mb-6">
          Your {location.state.subscriptionId? "subscription has been activated." : "purchase has been completed."} Thank you for choosing our service.
        </p>
        <div className="flex justify-center space-x-4">
          <button 
            onClick={() => navigate('/billing')}
            className="bg-blue-500 text-white px-6 py-2 rounded-md hover:bg-blue-600 transition"
          >
            Go to Billing
          </button>
          <button 
            onClick={() => navigate('/dashboard')}
            className="bg-gray-200 text-gray-800 px-6 py-2 rounded-md hover:bg-gray-300 transition"
          >
            Dashboard
          </button>
        </div>
      </div>
    </div>
  );
};

export default SuccessPage;
