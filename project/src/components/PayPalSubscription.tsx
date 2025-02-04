import React from 'react';
import { PayPalButtons } from "@paypal/react-paypal-js";
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { useNavigate } from 'react-router-dom';

interface SubscriptionProps {
  plan: {
    name: string;
    price: string;
    planId?: string;
    plan_type: string;
  };
  onSuccess?: (details: any) => void;
  onError?: (error: any) => void;
}

const PayPalSubscription: React.FC<SubscriptionProps> = ({
  plan,
  onSuccess,
  onError
}) => {
  const { user } = useAuth();
  const { showToast } = useToast();
  const navigate = useNavigate();

  const createSubscription = (data: any, actions: any) => {
    // Ensure we have a valid plan ID for subscription plans
    if (!plan.planId) {
      throw new Error('No subscription plan ID available');
    }

    return actions.subscription.create({
      plan_id: plan.planId,
      application_context: {
        shipping_preference: 'NO_SHIPPING',
        return_url: window.location.origin + '/success',
        cancel_url: window.location.origin + '/cancel'
      }
    });
  };
  const onApprove = async (data: any, actions: any) => {
    try {
      // Capture subscription details
      console.log("plan", plan);
      const subscriptionDetails = await actions.subscription.get();
      
      // Send subscription details to backend
      await axios.post('/api/subscriptions', 
        { 
          plan_type: plan.plan_type,
          subscriptionId: data.subscriptionID,
          paypalDetails: subscriptionDetails
        },
        { headers: { 'X-User-Id': user?.id } }
      );

      showToast(`Successfully subscribed to ${plan.name} plan!`, 'success');
      
      // Navigate to billing page
      navigate('/billing');

      // Optional: call additional success handler
      if (onSuccess) {
        onSuccess(subscriptionDetails);
      }
    } catch (error) {
      console.error('Subscription approval error:', error);
      showToast('Failed to complete subscription', 'error');
      
      if (onError) {
        onError(error);
      }
    }
  };

  return (
    <div className="w-full max-w-md mx-auto p-4">
      <PayPalButtons
        createSubscription={createSubscription}
        onApprove={onApprove}
        onError={(err) => {
          console.error('PayPal Subscription Error:', err);
          showToast('Subscription failed', 'error');
          
          if (onError) {
            onError(err);
          }
        }}
        style={{
          shape: 'rect',
          color: 'blue',
          layout: 'vertical',
          label: 'subscribe'
        }}
      />
    </div>
  );
};

export default PayPalSubscription;
