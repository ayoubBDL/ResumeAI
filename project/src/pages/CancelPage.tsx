import React from 'react';
import { useNavigate } from 'react-router-dom';
import { XCircle } from 'lucide-react';

const CancelPage: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-gray-100 flex items-center justify-center">
      <div className="bg-white p-8 rounded-lg shadow-xl text-center max-w-md w-full">
        <XCircle className="mx-auto h-24 w-24 text-red-500 mb-4" />
        <h1 className="text-3xl font-bold mb-4">Subscription Canceled</h1>
        <p className="text-gray-600 mb-6">
          Your subscription process was canceled. If this was unintentional, please try again.
        </p>
        <div className="flex justify-center space-x-4">
          <button 
            onClick={() => navigate('/billing')}
            className="bg-blue-500 text-white px-6 py-2 rounded-md hover:bg-blue-600 transition"
          >
            Back to Plans
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

export default CancelPage;
