import React, { useEffect, useState } from 'react';
import { Alert, AlertTitle, AlertDescription } from "../components/ui/alert";
import { Button } from "../components/ui/button";
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { CheckCircle } from 'lucide-react';

interface Subscription {
  credits: number;
  current_period_end: string;
  current_period_start: string;
  plan_type: 'free' | 'pro' | 'yearly' | 'payg';
  paypalSubscription?: {
    id: string;
    status: string;
    nextBillingTime: string;
    lastPayment: {
      amount: string;
      time: string;
    };
  };
}

interface Credits {
  credits_remaining: number;
}

const plans = [
  {
    name: 'Pro Monthly',
    price: '$19/month',
    credits: 50,
    features: [
      '50 Credits Monthly',
      'Advanced AI Resume Optimization',
      'Personalized Cover Letter Generation',
      'Basic Interview Preparation Insights',
      'Skill Gap Analysis',
      'Priority Email Support'
    ],
    plan_type: 'pro',
    planId: `${import.meta.env.VITE_PAYPAL_MONTHLY_PLAN}`
  },
  {
    name: 'Pro Yearly',
    price: '$209/year',
    credits: 'Unlimited',
    features: [
      'Unlimited Credits Annually',
      'Advanced AI Resume Optimization',
      'Comprehensive Cover Letter Generation',
      'Detailed Interview Preparation Strategy',
      'In-Depth Skill Mapping & Career Guidance',
      'AI-Powered Mock Interview Simulations',
      'Industry-Specific Interview Tips',
      'Priority + Live Chat Support',
      'Best Value Plan'
    ],
    plan_type: 'yearly',
    planId: `${import.meta.env.VITE_PAYPAL_ANNUALLY_PLAN}`
  },
  {
    name: 'Pay As You Go',
    price: '$1/credit',
    credits: 'Flexible',
    features: [
      'Minimum 5 Credits',
      'Basic Resume Optimization',
      'Standard Cover Letter Support',
      'Essential Interview Advice',
      'Buy Credits as Needed',
      'No Monthly Commitment',
      'Ideal for Occasional Use',
      '$1 per Credit'
    ],
    plan_type: 'payg',
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
  }, [user?.id]);

  const fetchSubscriptionAndCredits = async () => {
    try {
      setLoading(true);
      setError(null);

      // Check localStorage first
      const storedSubscription = localStorage.getItem('user_subscription');
      
      if (storedSubscription) {
        const parsedSubscription = JSON.parse(storedSubscription);
        
        // Check if subscription is still valid
        const currentTime = new Date();
        const periodEnd = new Date(parsedSubscription.current_period_end);
        
        if (currentTime < periodEnd) {
          setSubscription(parsedSubscription);
          
          // If stored subscription has credits, set them
          if (parsedSubscription.credits !== undefined) {
            setCredits(parsedSubscription.credits);
          }
          
          setLoading(false);
          return;
        }
      }

      // If no valid localStorage subscription, fetch from API
      try {
        const subResponse = await axios.get('/api/subscriptions', {
          headers: { 'X-User-Id': user?.id }
        });
        
        const { subscription, paypal_subscription: paypalSubscription, has_subscription } = subResponse.data;
        
        // If no subscription found, set to null
        if (!has_subscription) {
          setSubscription(null);
          setCredits(0);  // Explicitly set credits to 0
          setLoading(false);
          return;
        }

        // Set subscription first
        setSubscription(subscription);

        // Fetch credits
        const creditsResponse = await axios.get('/api/credits', {
          headers: { 'X-User-Id': user?.id }
        });
        
        const credits = creditsResponse.data.credits;
        setCredits(credits);

        // Save to localStorage
        localStorage.setItem('user_subscription', JSON.stringify({
          ...subscription,
          credits: subscription.plan_type === 'yearly' ? 9999 : credits,
          paypalSubscription: paypalSubscription ? {
            id: paypalSubscription.id,
            status: paypalSubscription.status,
            nextBillingTime: paypalSubscription.billing_info.next_billing_time,
            lastPayment: {
              amount: paypalSubscription.billing_info.last_payment.amount.value,
              time: paypalSubscription.billing_info.last_payment.time
            }
          } : undefined
        }));

      } catch (subErr: any) {
        console.error('Subscription fetch error:', subErr);
        setError(subErr.response?.data?.message || subErr.message);
        setSubscription(null);
        setCredits(0);
      }

    } catch (err: any) {
      console.error('General fetch error:', err);
      setError(err.response?.data?.message || err.message);
      setSubscription(null);
      setCredits(0);
    } finally {
      setLoading(false);
    }
  };

  const handlePlanSelect = (planType: string) => {
    // Navigate to checkout page with selected plan details
    navigate('/checkout', { 
      state: { 
        plan: plans.find(p => p.plan_type === planType),
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
          {!subscription ? (
            <div className="flex flex-col items-center justify-center text-center space-y-4">
              <svg 
                xmlns="http://www.w3.org/2000/svg" 
                className="h-16 w-16 text-gray-400" 
                fill="none" 
                viewBox="0 0 24 24" 
                stroke="currentColor"
              >
                <path 
                  strokeLinecap="round" 
                  strokeLinejoin="round" 
                  strokeWidth={2} 
                  d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z"
                />
              </svg>
              <div>
                <h3 className="text-xl font-semibold text-gray-800 mb-2">
                  No Active Subscription
                </h3>
                <p className="text-gray-600 mb-4">
                  You currently don't have an active subscription. 
                  Choose a plan to get started and unlock full features.
                </p>
                <p className="text-sm font-semibold text-indigo-700 mb-4">
                  Supercharge Your Resume Optimization Journey!
                  Upgrade Now and Get Unlimited AI-Powered Insights.
                </p>
                <Button 
                  onClick={() => window.scrollTo({ 
                    top: document.getElementById('plans-section')?.offsetTop, 
                    behavior: 'smooth' 
                  })}
                  className="bg-indigo-600 hover:bg-indigo-700 text-white"
                >
                  Explore Subscription Plans
                </Button>
              </div>
            </div>
          ) : (
            <div className="flex justify-between items-center">
              <div>
                <p className="text-lg font-semibold">
                  {subscription?.plan_type ? subscription.plan_type.toUpperCase() : 'Free'} Plan
                </p>
                <p className="text-gray-600">
                  {subscription?.plan_type === 'yearly' 
                    ? 'Unlimited credits' 
                    : (credits !== null && credits > 0
                      ? `${credits} credits remaining` 
                      : `No credits available (DEBUG: ${credits}, type: ${typeof credits})`)}
                </p>
                {subscription && (
                  <p className="text-sm text-gray-500">
                    Renews on {new Date(subscription.paypalSubscription?.nextBillingTime || subscription.current_period_end).toLocaleDateString()}
                  </p>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Pricing Plans */}
      <div className="mb-8">
        <h2 className="text-2xl font-bold mb-4">Available Plans</h2>
        <div id="plans-section" className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {plans.map((plan) => (
            <div 
              key={plan.name} 
              className={`bg-white rounded-lg shadow-lg p-6 flex flex-col ${
                plan.plan_type === 'yearly' ? 'border-2 border-indigo-600' : ''
              }`}
            >
              {plan.plan_type === 'yearly' && (
                <div className="flex justify-center mb-4">
                  <span className="bg-indigo-600 text-white text-xs font-bold px-3 py-1 rounded-full">
                    Best Value
                  </span>
                </div>
              )}
              <h3 className="text-2xl font-bold text-center mb-4">{plan.name}</h3>
              <p className="text-4xl font-extrabold text-center mb-6">{plan.price}</p>
              
              <ul className="space-y-2 mb-6 flex-grow">
                {plan.features.map((feature, index) => (
                  <li key={index} className="flex items-center">
                    <CheckCircle className="w-5 h-5 mr-2 text-green-500" />
                    {feature}
                  </li>
                ))}
              </ul>
              <Button
                className="w-full mt-auto"
                onClick={() => handlePlanSelect(plan.plan_type)}
                disabled={
                  subscription?.plan_type === plan.plan_type
                }
              >
                {subscription?.plan_type === plan.plan_type
                  ? 'Current Plan'
                  : 'Select Plan'}
              </Button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
