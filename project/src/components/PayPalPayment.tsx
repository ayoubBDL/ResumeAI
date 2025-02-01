import React, { useState } from 'react';
import { PayPalButtons, PayPalScriptProvider, ReactPayPalScriptOptions } from '@paypal/react-paypal-js';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';

interface PayPalPaymentProps {
  amount: number;
  credits: number;
  onSuccess?: () => void;
}

export function PayPalPayment({ amount, credits, onSuccess }: PayPalPaymentProps) {
  const { user } = useAuth();
  const { showToast } = useToast();
  const [isProcessing, setIsProcessing] = useState(false);

  const initialOptions: ReactPayPalScriptOptions = {
    clientId: import.meta.env.VITE_PAYPAL_CLIENT_ID || "",
    currency: "USD",
  };

  const createOrder = (data: any, actions: any) => {
    return actions.order.create({
      purchase_units: [{
        amount: {
          value: amount.toString(),
          currency_code: "USD"
        },
        description: `${credits} ResumeAI Credits`
      }]
    });
  };

  const onApprove = async (data: any, actions: any) => {
    try {
      setIsProcessing(true);
      const order = await actions.order.capture();

      // Send order confirmation to backend
      await axios.post('/api/credits/purchase', {
        orderId: order.id,
        amount: amount,
        credits: credits
      }, {
        headers: { 'X-User-Id': user?.id }
      });

      showToast(`Successfully purchased ${credits} credits!`, 'success');
      onSuccess?.();
    } catch (error) {
      console.error('Payment error:', error);
      showToast('Failed to process payment', 'error');
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <PayPalScriptProvider options={initialOptions}>
      <PayPalButtons
        createOrder={createOrder}
        onApprove={onApprove}
        disabled={isProcessing}
        style={{
          layout: 'vertical',
          color: 'blue',
          shape: 'rect',
          label: 'paypal'
        }}
      />
    </PayPalScriptProvider>
  );
}
