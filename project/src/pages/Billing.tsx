import { useEffect, useState } from 'react';
import { Alert, AlertTitle, AlertDescription } from "../components/ui/alert";
import { Button } from "../components/ui/button";
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import { CheckCircle } from 'lucide-react';
import { DollarSign } from 'lucide-react';
import { usePayPalScriptReducer } from "@paypal/react-paypal-js";
import { useToast } from '@/context/ToastContext';
import { subscriptionApi } from '@/api/subscription';

interface Subscription {
  has_subscription: boolean;
  subscription?: {
    status: string;
    plan_type: string;
  } | null;
  paypal_subscription?: PayPalSubscription;
}

interface PayPalSubscription {
  billing_info: {
    next_billing_time: string;
    last_payment: {
      amount: {
        currency_code: string;
        value: string;
      };
      time: string;
    };
  };
  id: string;
  status: string;
}

const plans = [
  {
    name: 'Pro Monthly',
    price: '$19.98/month',
    originalPrice: '$29.98',
    credits: 50,
    features: [
      '50 Resume Customizations Monthly',
      'Advanced AI Resume Optimization',
      'Smart Cover Letter Generation',
      'Interview Preparation Insights',
      'Skill Gap Analysis',
      'Priority Email Support',
      'Save $10/month'
    ],
    plan_type: 'pro',
    planId: `${import.meta.env.VITE_PAYPAL_MONTHLY_PLAN}`
  },
  {
    name: 'Pro Yearly',
    price: '$219.78/year',
    originalPrice: '$359.76',
    credits: 'Unlimited',
    features: [
      'Unlimited Credits',
      'Everything in Pro Monthly, plus:',
      'Premium AI Features',
      'Industry-specific Insights',
      '24/7 Priority Support',
      'Save $149.98/year'
    ],
    plan_type: 'yearly',
    planId: `${import.meta.env.VITE_PAYPAL_ANNUALLY_PLAN}`
  },
  {
    name: 'Pay As You Go',
    price: '$1/credit',
    credits: 'Flexible',
    features: [
      'Minimum $5 Purchase',
      'Full AI Optimization',
      'Cover Letter Generation',
      'No Monthly Commitment',
      'Buy Credits as Needed',
      'Perfect for Occasional Use'
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

  const { showToast } = useToast();
  const [] = usePayPalScriptReducer();

  useEffect(() => {
    const fetchData = async () => {
      if (!user?.id) return;
      setLoading(true);
      
      try {
        const subscriptionData = await subscriptionApi.getSubscription(user.id);
        setSubscription(subscriptionData);

        const userCredits = await subscriptionApi.getCredits(user.id);
        setCredits(userCredits);

      } catch (error) {
        console.error('Error fetching data:', error);
        showToast('Could not fetch subscription details', 'error');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  // Format the renewal date
  const getRenewalDate = () => {
    if (subscription?.paypal_subscription?.billing_info?.next_billing_time) {
      return formatRenewalDate(subscription.paypal_subscription.billing_info.next_billing_time);
    }
    return 'No renewal date';
  };

  const formatRenewalDate = (date: string) => {
    try {
      if (!date) return 'No renewal date';
      const dateObj = new Date(date);
      if (isNaN(dateObj.getTime())) return 'Invalid date';
      
      return dateObj.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      });
    } catch (error) {
      console.error('Error formatting date:', error);
      return 'Invalid date';
    }
  };

  const handlePlanSelect = (planType: string) => {
    navigate('/checkout', { 
      state: { 
        plan: plans.find(p => p.plan_type === planType),
        currentSubscription: subscription
      } 
    });
  };


  // Add these status checks at the top of the component
  const hasActiveSubscription = subscription?.subscription?.status === 'active' && 
    subscription?.paypal_subscription?.status === 'ACTIVE';

  return (
    <div className="container mx-auto px-4 py-8">
      {error && (
        <Alert variant="destructive" className="mb-4">
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Current Plan Section */}
      {subscription && (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mb-12">
          <div className="bg-gradient-to-r from-indigo-50 to-blue-50 rounded-2xl p-8 border border-indigo-100">
            <h2 className="text-2xl font-bold mb-6">Current Plan</h2>
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-xl font-semibold text-indigo-600 mb-2">
                  {hasActiveSubscription 
                    ? (subscription?.subscription?.plan_type === 'yearly' ? 'YEARLY Plan' : 'PRO Plan')
                    : 'Free Plan'}
                </h3>
                <p className="text-gray-600">
                  {subscription?.subscription?.plan_type === 'yearly' 
                    ? 'Unlimited credits':`${credits} credits remaining` 
                      
                  }
                </p>
                <p className="text-sm text-gray-500 mt-2">
                  {hasActiveSubscription ? `Renews on ${getRenewalDate()}` : 'No active subscription'}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Pricing Plans */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <h2 className="text-3xl font-bold text-center mb-12">Available Plans</h2>
        <div className="grid md:grid-cols-3 gap-8">
          {plans.map((plan) => (
            <div
              key={plan.name}
              className={`relative rounded-2xl p-8 transition-all duration-300 hover:shadow-xl ${
                subscription?.subscription?.plan_type === plan.plan_type
                  ? 'border-2 border-indigo-600 bg-gradient-to-b from-indigo-50 to-white'
                  : 'border border-gray-200 hover:border-indigo-300'
              }`}
            >
              {plan.name === 'Pro Yearly' && (
                <div className="absolute -top-4 left-1/2 transform -translate-x-1/2">
                  <span className="bg-indigo-600 text-white text-sm px-4 py-1 rounded-full font-medium">
                    Best Value
                  </span>
                </div>
              )}
              
              <div className="text-center mb-8">
                <h3 className="text-2xl font-bold mb-4">{plan.name}</h3>
                <div className="flex flex-col items-center justify-center mb-2">
                  <div className="text-4xl font-extrabold">
                    {plan.price.split('/')[0]}
                    <span className="text-lg font-normal text-gray-600">
                      /{plan.price.split('/')[1]}
                    </span>
                  </div>
                  {plan.originalPrice && (
                    <p className="text-gray-500 line-through mt-1">
                      {plan.originalPrice}
                    </p>
                  )}
                </div>
                <p className="text-sm text-gray-600">
                  {typeof plan.credits === 'number' 
                    ? `${plan.credits} credits`
                    : plan.credits}
                </p>
              </div>

              <ul className="space-y-4 mb-8">
                {plan.features.map((feature, index) => (
                  <li key={index} className="flex items-center gap-3">
                    <CheckCircle className={`h-5 w-5 flex-shrink-0 ${
                      feature.includes('Save') ? 'text-green-500' : 'text-indigo-500'
                    }`} />
                    <span className={`text-sm ${
                      feature.includes('Save') ? 'text-green-700 font-medium' : 'text-gray-600'
                    }`}>
                      {feature}
                    </span>
                  </li>
                ))}
              </ul>

              {
                plan.plan_type === 'payg' ? (
                  <Button
                    onClick={() => handlePlanSelect(plan.plan_type)}
                    className="w-full py-2.5 bg-indigo-600 text-white hover:bg-indigo-700 rounded-xl font-medium transition-colors flex items-center justify-center gap-2"
                  >
                    <DollarSign className="w-4 h-4" />
                    Buy More Credits
                  </Button>
                ) : (
                  <Button
                    className="w-full mt-auto"
                    onClick={() => handlePlanSelect(plan.plan_type)}
                    disabled={
                      subscription?.subscription?.plan_type === plan.plan_type
                    }
                  >
                    {subscription?.subscription?.plan_type === plan.plan_type
                      ? 'Current Plan'
                      : 'Select Plan'}

                  </Button>
                )
              }
            </div>
          ))}
        </div>
      </div>
    </div>

  );
}
