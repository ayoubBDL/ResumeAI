import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { 
  User, 
  CreditCard, 
  CheckCircle2, 
  XCircle,
  Bell,
  Lock,
  Shield,
  Mail,
  Coins} from 'lucide-react';
import { useAuth } from '@/context/AuthContext';
import { useCredits } from '@/context/CreditsContext';
import axios from 'axios';
import { useToast } from '@/context/ToastContext';
import { subscriptionApi } from '@/api/subscription';
import { Link } from 'react-router-dom';

import { AlertDialog } from '@/components/AlertDialog';

type NotificationSettings = {
  emailUpdates: boolean;
  securityAlerts: boolean;
  marketingEmails: boolean;
};

// Add this SVG component for Google logo
const GoogleIcon = () => (
  <svg 
    className="h-5 w-5" 
    viewBox="0 0 24 24" 
    xmlns="http://www.w3.org/2000/svg"
  >
    <path
      d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
      fill="#4285F4"
    />
    <path
      d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
      fill="#34A853"
    />
    <path
      d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
      fill="#FBBC05"
    />
    <path
      d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
      fill="#EA4335"
    />
  </svg>
);

// Add this type for better type safety
type SubscriptionData = {
  has_subscription: boolean;
  subscription: {
    status: string;
    plan_type: string;
  } | null;
  paypal_subscription?: any;
};

export default function Settings() {
  const { user, setUser } = useAuth();
  const { credits, updateCredits } = useCredits();
  const { showToast } = useToast();
  const [subscription, setSubscription] = useState<SubscriptionData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isCancelling, setIsCancelling] = useState(false);
  const [showConfirmation, setShowConfirmation] = useState(false);
  const [email, setEmail] = useState(user?.email || '');
  const [name, setName] = useState(
    user?.user_metadata?.name ||
    user?.user_metadata?.full_name ||
    ''
  );
  const [notifications, setNotifications] = useState<NotificationSettings>({
    emailUpdates: true,
    securityAlerts: true,
    marketingEmails: false
  });
  const provider = user?.app_metadata?.provider || 'email';
  const [cancelError, setCancelError] = useState<any>(null);

  useEffect(() => {
    const fetchSubscriptionData = async () => {
      try {
        if (!user?.id) return;
        
        const subscriptionData = await subscriptionApi.getSubscription(user.id);
        setSubscription(subscriptionData);
      } catch (error) {
        console.error('Error fetching subscription:', error);
        showToast('Could not fetch subscription details', 'error');
      } finally {
        setIsLoading(false);
      }
    };

    fetchSubscriptionData();
  }, [user?.id]);

  // Check localStorage directly if subscription is not set
  useEffect(() => {
    if (!subscription) {
      const cachedSubscription = localStorage.getItem('user_subscription');
      if (cachedSubscription) {
        try {
          const parsed = JSON.parse(cachedSubscription);
          setSubscription(parsed);
        } catch (error) {
          console.error('Error parsing localStorage subscription:', error);
        }
      }
    }

    // Check localStorage for credits
    const cachedCredits = localStorage.getItem('user_credits');
    if (cachedCredits) {
      try {
        const parsed = JSON.parse(cachedCredits);
      } catch (error) {
        console.error('Error parsing localStorage credits:', error);
      }
    }
  }, [subscription]);

  // Add these status checks at the top of the component
  const hasActiveSubscription = subscription?.has_subscription && 
    subscription?.subscription?.status === 'active' &&
    subscription?.paypal_subscription?.status === 'ACTIVE';

  // Update the subscription status display
  const currentPlan = (() => {
    if (!hasActiveSubscription) return 'Free Plan';
    if (subscription?.subscription?.plan_type === 'yearly') return 'Yearly Pro Plan';
    return 'Monthly Pro Plan';
  })();

  // Simplified cancel button logic 
  const showCancelButton = (() => {
    const hasActiveSubscription = subscription?.subscription?.status === 'active';
    // Always show cancel button if subscription is active
    return hasActiveSubscription;
  })();

  const handleCancelSubscription = async () => {
    setIsCancelling(true);
    try {
      if (!user?.id) return;

      await subscriptionApi.cancelSubscription(user.id);
      
      // Refresh subscription data
      const subscriptionData = await subscriptionApi.getSubscription(user.id);
      setSubscription(subscriptionData);
      
      showToast('Your subscription has been successfully cancelled.', 'success');
    } catch (error) {
      console.error('Error cancelling subscription:', error);
      setCancelError({
        error: 'Cancellation Failed',
        message: 'Could not cancel subscription. Please try again.',
        action: 'retry'
      });
    } finally {
      setIsCancelling(false);
      setShowConfirmation(false);
    }
  };

  const handleUpdateProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (!user) return;

      const response = await axios.put(`${import.meta.env.VITE_RESUME_API_URL}/api/users/profile`, {
        full_name: name
      }, {
        headers: { 'X-User-Id': user.id }
      });

      if (response.data.success) {
        showToast('Profile updated successfully', 'success');
        
        // Update the user state with the response data
        if (response.data.data) {
          // Make sure we preserve the existing metadata structure
          const updatedMetadata = {
            ...response.data.data.user_metadata,
            name: response.data.data.user_metadata.name,
            full_name: response.data.data.user_metadata.name // Keep both fields in sync
          };

          setUser({
            ...user,
            user_metadata: updatedMetadata,
            app_metadata: response.data.data.app_metadata
          });
        }
      }
    } catch (error) {
      console.error('Error updating profile:', error);
      showToast('Failed to update profile', 'error');
    }
  };

  // Type-safe notification toggle
  const toggleNotification = (key: keyof NotificationSettings) => {
    setNotifications(prev => ({
      ...prev,
      [key]: !prev[key]
    }));
  };

  // Add this helper function to get all providers
  const getProviders = () => {
    const providers = [];
    if (user?.app_metadata?.provider === 'google') {
      providers.push('google');
    } else if (user?.email) {
      providers.push('email');
    }
    return providers;
  };

  return (
    <div className="container mx-auto px-4 py-8">
      {isLoading ? (
        <div className="text-center py-12 bg-white shadow overflow-hidden sm:rounded-md">
          <div className="mx-auto h-12 w-12 text-gray-400">
            <svg className="animate-spin h-12 w-12" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
          </div>
          <h3 className="mt-2 text-sm font-medium text-gray-900">Loading settings...</h3>
        </div>
      ) : (
        <div className="max-w-7xl mx-auto">
          <h1 className="text-2xl font-bold text-gray-900 mb-6">Settings</h1>
          
          <div className="bg-white shadow rounded-lg divide-y divide-gray-200">
            {/* Profile Section */}
            <div className="p-6">
              <div className="flex items-center mb-4">
                <User className="h-5 w-5 text-gray-500 mr-2" />
                <h2 className="text-lg font-medium text-gray-900">Profile Settings</h2>
              </div>
              
              <form onSubmit={handleUpdateProfile} className="space-y-4">
                <div>
                  <label htmlFor="name" className="block text-sm font-medium text-gray-700">
                    Full Name
                  </label>
                  <div className="mt-1">
                    <input
                      type="text"
                      id="name"
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                    />
                  </div>
                </div>

                <div>
                  <label htmlFor="email" className="block text-sm font-medium text-gray-700">
                    Email Address
                  </label>
                  <div className="mt-1">
                    <input
                      type="email"
                      id="email"
                      value={email}
                      disabled
                      className="shadow-sm block w-full sm:text-sm border-gray-300 rounded-md bg-gray-50 cursor-not-allowed"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Connected With
                  </label>
                  <div className="mt-1 space-y-2">
                    {getProviders().map((providerType) => (
                      <div key={providerType} className="flex items-center space-x-2">
                        {providerType === 'google' && (
                          <>
                            <GoogleIcon />
                            <span className="text-sm text-gray-600">Google Account</span>
                          </>
                        )}
                        {providerType === 'email' && (
                          <>
                            <Mail className="h-5 w-5 text-gray-500" />
                            <span className="text-sm text-gray-600">Email & Password</span>
                          </>
                        )}
                      </div>
                    ))}
                  </div>
                </div>

                <button
                  type="submit"
                  className="inline-flex justify-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                >
                  Update Profile
                </button>
              </form>
            </div>

            {/* Notifications Section */}
            <div className="p-6">
              <div className="flex items-center mb-4">
                <Bell className="h-5 w-5 text-gray-500 mr-2" />
                <h2 className="text-lg font-medium text-gray-900">Notification Preferences</h2>
              </div>
              
              <div className="space-y-4">
                {Object.entries(notifications).map(([key, value]) => (
                  <div key={key} className="flex items-center justify-between">
                    <span className="text-sm text-gray-700">
                      {key === 'emailUpdates' && 'Email Updates'}
                      {key === 'securityAlerts' && 'Security Alerts'}
                      {key === 'marketingEmails' && 'Marketing Emails'}
                    </span>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input
                        type="checkbox"
                        checked={value}
                        onChange={() => toggleNotification(key as keyof NotificationSettings)}
                        className="sr-only peer"
                      />
                      <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-indigo-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-indigo-600"></div>
                    </label>
                  </div>
                ))}
              </div>
            </div>

            {/* Security Section */}
            <div className="p-6">
              <div className="flex items-center mb-4">
                <Shield className="h-5 w-5 text-gray-500 mr-2" />
                <h2 className="text-lg font-medium text-gray-900">Security</h2>
              </div>
              
              <button
                className="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
              >
                <Lock className="h-4 w-4 mr-2" />
                Change Password
              </button>
            </div>

            {/* Subscription Section */}
            <div className="p-6">
              <div className="flex items-center mb-4">
                <CreditCard className="h-5 w-5 text-gray-500 mr-2" />
                <h2 className="text-lg font-medium text-gray-900">Subscription</h2>
              </div>

              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-900">Current Plan</p>
                    <p className="text-sm text-gray-500">{currentPlan}</p>
                  </div>
                  <div className="flex items-center">
                    {hasActiveSubscription ? (
                      <CheckCircle2 className="h-5 w-5 text-green-500 mr-2" />
                    ) : (
                      <XCircle className="h-5 w-5 text-red-500 mr-2" />
                    )}
                    <span className="text-sm text-gray-700">
                      {hasActiveSubscription ? 'Active' : 'No active subscription'}
                    </span>
                  </div>
                </div>

                {/* Credits Display */}
                <div className="pt-4 border-t border-gray-200">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center">
                      <Coins className="h-5 w-5 text-yellow-500 mr-2" />
                      <p className="text-sm font-medium text-gray-900">
                        {subscription?.subscription?.plan_type === 'yearly' 
                          ? "Unlimited Credits"
                          : `${credits} Credits Available`}
                      </p>
                    </div>
                    {credits !== null && credits <= 2 && (
                      <Link
                        to="/billing"
                        className="inline-flex justify-center items-center px-3 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                      >
                        Purchase Credits
                      </Link>
                    )}
                  </div>
                </div>

                {/* Only show cancel button if there's an active subscription */}
                {hasActiveSubscription && (
                  <Button 
                    variant="destructive"
                    onClick={() => setShowConfirmation(true)}
                  >
                    Cancel Subscription
                  </Button>
                )}
              </div>
            </div>
          </div>

          {/* Put AlertDialog at the bottom of the page component, before the final closing div */}
          {showConfirmation && (
            <AlertDialog
              error="Cancel Subscription"
              message="Are you sure you want to cancel your subscription? Your access will continue until the end of your current billing period."
              action="confirm"
              onAction={handleCancelSubscription}
              onClose={() => setShowConfirmation(false)}
              disabled={isCancelling}
              actionLabel={isCancelling ? 'Cancelling...' : 'Yes, Cancel'}
            />
          )}

          {cancelError && (
            <AlertDialog
              error={cancelError.error}
              message={cancelError.message}
              action="retry"
              onClose={() => setCancelError(null)}
            />
          )}
        </div>
      )}
    </div>
  );
}
