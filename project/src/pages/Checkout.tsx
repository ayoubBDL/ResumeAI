import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Button } from "../components/ui/button";
import { PayPalButtons, PayPalScriptProvider } from '@paypal/react-paypal-js';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { CheckCircle, ArrowLeft } from 'lucide-react';

export default function Checkout() {
  const location = useLocation();
  const navigate = useNavigate();
  const { user } = useAuth();
  const { showToast } = useToast();

  const [plan, setPlan] = useState<any>(null);
  const [currentSubscription, setCurrentSubscription] = useState<any>(null);
  const [credits, setCredits] = useState<number>(5);
  const [isProcessing, setIsProcessing] = useState(false);

  useEffect(() => {
    // Check if plan was passed via navigation state
    if (location.state) {
      setPlan(location.state.plan);
      setCurrentSubscription(location.state.currentSubscription);

      // If Pay As You Go, set minimum credits
      if (location.state.plan.type === 'payg') {
        setCredits(Math.max(5, credits));
      }
    } else {
      // If no state, redirect back to billing
      navigate('/billing');
    }
  }, [location.state, navigate]);

  const handleCreditsChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (plan.type === 'payg') {
      const inputCredits = parseInt(e.target.value);
      setCredits(Math.max(5, inputCredits));
    }
  };

  const handlePayPalCreateOrder = (data: any, actions: any) => {
    if (!plan) return;

    // For Pay As You Go, calculate total based on credits
    const totalAmount = plan.type === 'payg' 
      ? (credits * plan.pricePerCredit).toFixed(2)
      : plan.price.replace(/[^0-9.-]+/g,"");

    return actions.order.create({
      purchase_units: [{
        amount: {
          value: totalAmount,
          currency_code: "USD"
        },
        description: plan.type === 'payg' 
          ? `${credits} Credits at $1 each` 
          : `${plan.name} Plan`
      }]
    });
  };

  const handlePayPalApprove = async (data: any, actions: any) => {
    try {
      setIsProcessing(true);
      const order = await actions.order.capture();

      // Send subscription/credit purchase request to backend
      if (plan.type === 'payg') {
        // Credit purchase
        await axios.post('/api/credits/purchase', {
          orderId: order.id,
          credits: credits,
          amount: credits * plan.pricePerCredit
        }, {
          headers: { 'X-User-Id': user?.id }
        });
        showToast(`Successfully purchased ${credits} credits!`, 'success');
      } else {
        // Subscription purchase
        await axios.post('/api/subscriptions', 
          { 
            plan_type: plan.type,
            orderId: order.id 
          },
          { headers: { 'X-User-Id': user?.id } }
        );
        showToast(`Successfully subscribed to ${plan.name} plan!`, 'success');
      }

      navigate('/billing');
    } catch (error) {
      console.error('Purchase error:', error);
      showToast('Failed to complete purchase', 'error');
    } finally {
      setIsProcessing(false);
    }
  };

  if (!plan) return null;

  return (
    <div className="container mx-auto px-4 py-8">
      <Button 
        variant="outline" 
        className="mb-6"
        onClick={() => navigate('/billing')}
      >
        <ArrowLeft className="mr-2 h-4 w-4" /> Back to Plans
      </Button>

      <div className="max-w-2xl mx-auto bg-white rounded-lg shadow-lg p-8">
        <h1 className="text-3xl font-bold text-center mb-6">{plan.name} Plan Checkout</h1>
        
        <div className="grid md:grid-cols-2 gap-8">
          {/* Plan Details */}
          <div>
            <h2 className="text-xl font-semibold mb-4">Plan Details</h2>
            <div className="bg-gray-50 rounded-lg p-6">
              {plan.type === 'payg' ? (
                <>
                  <p className="text-2xl font-bold mb-4">
                    ${credits * plan.pricePerCredit} Total
                  </p>
                  <div className="mb-4">
                    <label className="block mb-2">Number of Credits</label>
                    <input 
                      type="number" 
                      value={credits} 
                      onChange={handleCreditsChange}
                      min={5}
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
          <div>
            <h2 className="text-xl font-semibold mb-4">Payment</h2>
            <PayPalScriptProvider 
              options={{ 
                clientId: import.meta.env.VITE_PAYPAL_CLIENT_ID || "",
                currency: "USD"
              }}
            >
              <PayPalButtons
                createOrder={handlePayPalCreateOrder}
                onApprove={handlePayPalApprove}
                disabled={isProcessing}
                style={{
                  layout: 'vertical',
                  color: 'blue',
                  shape: 'rect',
                  label: 'paypal'
                }}
              />
            </PayPalScriptProvider>
          </div>
        </div>
      </div>
    </div>
  );
}
