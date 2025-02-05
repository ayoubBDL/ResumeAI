import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Button } from "../components/ui/button";
import { PayPalButtons, PayPalScriptProvider } from '@paypal/react-paypal-js';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { CheckCircle, ArrowLeft } from 'lucide-react';
import PaypalButton from '@/components/PaypalButton';
import axios from 'axios';
import { useCredits } from '../context/CreditsContext';

export default function Checkout() {
  const location = useLocation();
  const navigate = useNavigate();
  const { user } = useAuth();
  const { showToast } = useToast();
  const { updateCredits } = useCredits();
  const [plan, setPlan] = useState<any>(null);
  const [currentSubscription, setCurrentSubscription] = useState<any>(null);
  const [credits, setCredits] = useState<number>(5);
  const [isProcessing, setIsProcessing] = useState(false);

  useEffect(() => {
    // Check if plan was passed via navigation state
    if (location.state) {
      setPlan(location.state.plan);
      setCurrentSubscription(location.state.currentSubscription);
      console.log("location.state", location.state, location.state.currentSubscription);
      // If Pay As You Go, set minimum credits
      if (location.state.plan.plan_type === 'payg') {
        setCredits(Math.max(5, credits));
      }
    } else {
      // If no state, redirect back to billing
      navigate('/billing');
    }
  }, [location.state, navigate]);

  const handleCreditsChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (plan?.plan_type === 'payg') {
      const inputCredits = parseInt(e.target.value) || 0;
      setCredits(inputCredits);
    }
  };

  const handleCreditsBlur = (e: React.FocusEvent<HTMLInputElement>) => {
    if (plan?.plan_type === 'payg') {
      const inputCredits = parseInt(e.target.value) || 0;
      setCredits(Math.max(5, inputCredits));
    }
  };

  const creditPrice = plan?.plan_type === 'payg' 
    ? (credits * 1).toFixed(2)  // $1 per credit
    : plan?.price?.replace(/[^0-9.-]+/g,"") || "0";

  const createOrder = (data: any, actions: any) => {
    const totalAmount = plan?.plan_type === 'payg' 
      ? (credits * 1).toFixed(2)  // $1 per credit
      : plan?.price?.replace(/[^0-9.-]+/g,"") || "0";

    return actions.order.create({
      purchase_units: [{
        amount: {
          value: totalAmount,
          currency_code: "USD"
        },
        description: plan?.plan_type === 'payg' 
          ? `${credits} Credits at $1 each` 
          : `${plan?.name || 'Plan'} Plan`
      }]
    });
  };

  const onCancel = (data: any) => {
    navigate('/cancel');
  };
  const onApprove = async (data: any, actions: any) => {
    try {
      setIsProcessing(true);
      // Send subscription/credit purchase request to backend
      if (plan.plan_type === 'payg') {
        // Credit purchase
        const response = await axios.post('/api/credits/purchase', {
          orderId: data.orderID,
          credits: credits
        }, {
          headers: { 'X-User-Id': user?.id }
        });

        // Update credits in context and localStorage
        await updateCredits();
        
        showToast(`Successfully purchased ${credits} credits!`, 'success');
      } else {
        // Subscription purchase
        console.log("Subscription data:", data);
        await axios.post('/api/subscriptions', 
          { 
            plan_type: plan.plan_type,
            orderId: data.orderID,
            subscriptionId: data.subscriptionID
          },
          { headers: { 'X-User-Id': user?.id } }
        );
        showToast(`Successfully subscribed to ${plan.name} plan!`, 'success');
      }

      navigate('/success', { 
        state: { 
          subscriptionId: data.subscriptionID,
          orderId: data.orderID,
          planType: plan.plan_type,
          credits: plan.plan_type === 'payg' ? credits : undefined
        } 
      });
    } catch (error) {
      console.error('Payment error:', error);
      showToast('Failed to complete purchase', 'error');
    } finally {
      setIsProcessing(false);
    }
  };

  if (!plan) {
    return <div>Loading plan details...</div>;
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <Button 
        variant="outline" 
        className="mb-6"
        onClick={() => navigate('/billing')}
      >
        <ArrowLeft className="mr-2 h-4 w-4" /> Back to Plans
      </Button>

      <div className="max-w-4xl mx-auto bg-white rounded-lg shadow-lg p-8">
        <h1 className="text-3xl font-bold text-center mb-6">{plan.name} Plan Checkout</h1>
        
        <div className="grid md:grid-cols-2 gap-8">
          {/* Plan Details */}
          <div>
            <h2 className="text-xl font-semibold mb-4">Plan Details</h2>
            <div className="bg-gray-50 rounded-lg p-6">
              {plan.plan_type === 'payg' ? (
                <>
                  <p className="text-2xl font-bold mb-4">
                    ${credits * 1} Total
                  </p>
                  <div className="mb-4">
                    <label className="block mb-2">Number of Credits</label>
                    <input 
                      type="number" 
                      value={credits} 
                      onChange={handleCreditsChange}
                      onBlur={handleCreditsBlur}
                      min="1"
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    />
                  </div>
                </>
              ) : (
                <p className="text-2xl font-bold mb-4">{plan.price}</p>
              )}
              
              <ul className="space-y-2">
                {plan.features.map((feature: string, index: number) => (
                  <li key={index} className="flex items-center">
                    <CheckCircle className="w-5 h-5 mr-2 text-green-500" />
                    {feature}
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {/* Payment Section */}
          <div className="bg-gray-50 rounded-lg p-6">
            <h2 className="text-xl font-semibold mb-4">Payment</h2>
            <div className="border border-gray-300 p-4 rounded-lg">
              <PaypalButton 
                onApprove={onApprove} 
                onCancel={onCancel} 
                plan_id={plan.plan_type !== 'payg' ? plan.planId : undefined}
                isSubscription={plan.plan_type !== 'payg'}
                amount={creditPrice}
                description={plan.plan_type === 'payg' 
                  ? `${credits} Credits at $1 each` 
                  : `${plan.name} Plan`}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
