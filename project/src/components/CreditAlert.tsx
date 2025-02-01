import React from 'react';
import { Button } from "@/components/ui/button";
import { useNavigate } from 'react-router-dom';

interface CreditAlertProps {
  error: string;
  message: string;
  action?: 'purchase_required' | 'renew_subscription';
  onClose?: () => void;
}

export function CreditAlert({ error, message, action, onClose }: CreditAlertProps) {
  const navigate = useNavigate();

  const handleAction = () => {
    navigate('/billing');
    onClose?.();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div className="bg-white rounded-lg shadow-xl p-6 max-w-sm w-full">
        <div className="text-center">
          <h2 className="text-xl font-bold text-red-600 mb-4">{error}</h2>
          <p className="text-gray-600 mb-6">{message}</p>
          <div className="flex justify-center space-x-4">
            <Button 
              variant="outline" 
              onClick={onClose}
              className="px-4 py-2"
            >
              Cancel
            </Button>
            <Button 
              onClick={handleAction}
              className="px-4 py-2 bg-indigo-600 text-white hover:bg-indigo-700"
            >
              {action === 'renew_subscription' ? 'Renew Subscription' : 'Purchase Credits'}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
