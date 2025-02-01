import React, { useEffect, useState } from 'react';
import { Alert, AlertTitle, AlertDescription } from "../components/ui/alert";
import { Button } from "../components/ui/button";
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { CheckCircle } from 'lucide-react';

interface Subscription {
  id: string;
  plan_type: 'free' | 'pro' | 'yearly' | 'payg';
  status: 'active' | 'cancelled';
  current_period_end: string;
}

interface Credits {
  credits_remaining: number;
}

const plans = [
  {
    name: 'Free',
    price: '$0',
    credits: 2,
    features: ['2 Free Credits', 'Basic Resume Optimization', 'Job Description Analysis'],
    type: 'free'
  },
  {
    name: 'Pro Monthly',
    price: '$29/month',
    credits: 50,
    features: [
      '50 Credits Monthly',
      'Advanced Resume Optimization',
      'Cover Letter Generation',
      'Priority Support'
    ],
    type: 'pro'
  },
  {
    name: 'Pro Yearly',
    price: '$290/year',
    credits: 'Unlimited',
    features: [
      'Unlimited Credits Annually',
      'Advanced Resume Optimization',
      'Cover Letter Generation',
      'Priority Support',
      'Best Value Plan'
    ],
    type: 'yearly'
  },
  {
    name: 'Pay As You Go',
    price: '$1/credit',
    credits: 'Flexible',
    features: [
      'Minimum 5 Credits',
      'Buy Credits as Needed',
      'No Monthly Commitment',
      'Ideal for Occasional Use',
      '$1 per Credit'
    ],
    type: 'payg',
    minCredits: 5,
    pricePerCredit: 1
  }
];

export default function Billing() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [subscription, setSubscription] = useState<Subscription | null>(null);
  const [credits, setCredits] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchSubscriptionAndCredits();
  }, [user]);

  const fetchSubscriptionAndCredits = async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch subscription
      const subResponse = await axios.get('/api/subscriptions', {
        headers: { 'X-User-Id': user?.id }
      });
      setSubscription(subResponse.data.subscription);

      // Fetch credits
      const creditsResponse = await axios.get('/api/credits', {
        headers: { 'X-User-Id': user?.id }
      });
      setCredits(creditsResponse.data.credits);

    } catch (err: any) {
      setError(err.response?.data?.message || err.message);
    } finally {
      setLoading(false);
    }
  };

  const handlePlanSelect = (planType: string) => {
    // Navigate to checkout page with selected plan details
    navigate('/checkout', { 
      state: { 
        plan: plans.find(p => p.type === planType),
        currentSubscription: subscription
      } 
    });
  };

  return (
    <div className="container mx-auto px-4 py-8">
      {error && (
        <Alert variant="destructive" className="mb-4">
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Current Plan & Credits */}
      <div className="mb-8">
        <h2 className="text-2xl font-bold mb-4">Current Plan</h2>
        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="flex justify-between items-center">
            <div>
              <p className="text-lg font-semibold">
                {subscription ? subscription.plan_type.toUpperCase() : 'Free'} Plan
              </p>
              <p className="text-gray-600">
                {credits !== null ? `${credits} credits remaining` : 'Loading credits...'}
              </p>
              {subscription && (
                <p className="text-sm text-gray-500">
                  Renews on {new Date(subscription.current_period_end).toLocaleDateString()}
                </p>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Pricing Plans */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {plans.map((plan) => (
          <div 
            key={plan.name} 
            className={`bg-white rounded-lg shadow-lg p-6 ${
              plan.type === 'yearly' ? 'border-2 border-indigo-600' : ''
            }`}
          >
            {plan.type === 'yearly' && (
              <div className="flex justify-center mb-4">
                <span className="bg-indigo-600 text-white text-xs font-bold px-3 py-1 rounded-full">
                  Best Value
                </span>
              </div>
            )}
            <h3 className="text-2xl font-bold text-center mb-4">{plan.name}</h3>
            <p className="text-4xl font-extrabold text-center mb-6">{plan.price}</p>
            
            <ul className="space-y-2 mb-6 min-h-[200px]">
              {plan.features.map((feature, index) => (
                <li key={index} className="flex items-center">
                  <CheckCircle className="w-5 h-5 mr-2 text-green-500" />
                  {feature}
                </li>
              ))}
            </ul>
            <Button
              className="w-full"
              onClick={() => handlePlanSelect(plan.type)}
              disabled={
                subscription?.status === 'active' &&
                subscription?.plan_type === plan.type
              }
            >
              {subscription?.status === 'active' &&
              subscription?.plan_type === plan.type
                ? 'Current Plan'
                : 'Select Plan'}
            </Button>
          </div>
        ))}
      </div>
    </div>
  );
}
