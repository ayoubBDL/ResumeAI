import React, { useEffect, useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useCredits } from '../context/CreditsContext';
import { FileText, BookmarkCheck, LogOut, Coins, CreditCard, Home, Settings } from 'lucide-react';
import logo from '../assets/logo.png';
import axios from 'axios';

const navigation = [
  {
    name: 'Dashboard',
    href: '/dashboard',
    icon: Home,
  },
  {
    name: 'My Resumes',
    href: '/my-resumes',
    icon: FileText,
  },
  {
    name: 'Saved Jobs',
    href: '/saved-jobs',
    icon: BookmarkCheck,
  },
  {
    name: 'Credits & Plans',
    href: '/billing',
    icon: CreditCard,
  }
];

interface LayoutProps {
  children: React.ReactNode;
}

interface Subscription {
  plan_type: string;
  subscription?: {
    plan_type: string;
  };
}

export default function Layout({ children }: LayoutProps) {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, signOut } = useAuth();
  const { credits, updateCredits } = useCredits();
  const [subscription, setSubscription] = useState<Subscription | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;

    const fetchData = async () => {
      try {
        if (!user) {
          navigate('/login');
          return;
        }

        // Check if we have cached subscription data
        const cachedSubscription = localStorage.getItem('user_subscription');
        if (cachedSubscription) {
          const parsed = JSON.parse(cachedSubscription);
          const lastChecked = new Date(parsed.lastChecked);
          const now = new Date();
          // Only use cache if it's less than 5 minutes old
          if (now.getTime() - lastChecked.getTime() < 5 * 60 * 1000) {
            if (isMounted) {
              setSubscription(parsed);
              setLoading(false);
            }
            return;
          }
        }

        // Fetch subscription data if no cache or cache expired
        const response = await axios.get('/api/subscriptions', {
          headers: { 'X-User-Id': user.id }
        });

        const subscriptionData = response.data;
        
        if (!subscriptionData) {
          if (isMounted) {
            navigate('/billing');
          }
          return;
        }
        
        // Set subscription only if component is still mounted
        if (isMounted) {
          setSubscription(subscriptionData);
          
          // Update localStorage with timestamp
          localStorage.setItem('user_subscription', JSON.stringify({
            ...subscriptionData,
            lastChecked: new Date().toISOString()
          }));
        }
      } catch (error) {
        console.error('Error:', error);
        if (isMounted && axios.isAxiosError(error) && error.response?.status === 404) {
          navigate('/billing');
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    // Initial fetch
    fetchData();

    // Cleanup function
    return () => {
      isMounted = false;
    };
  }, [user, navigate]); // Only re-run when user or navigate changes

  const handleSignOut = async () => {
    try {
      await signOut();
      navigate('/login');
    } catch (error) {
      console.error('Error signing out:', error);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Sidebar */}
      <div className="fixed inset-y-0 left-0 w-64 bg-white border-r">
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="flex items-center justify-center h-24 px-4 border-b">
            <Link to="/dashboard" className="flex items-center">
              <img
                src={logo}
                alt="ResumeAI Logo"
                className="h-[100px] w-[100px] object-contain"
              />
            </Link>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-2 py-4 space-y-1">
            {navigation.map((item) => {
              const Icon = item.icon;
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  className={`flex items-center px-3 py-2 text-sm font-medium rounded-md ${
                    location.pathname === item.href
                      ? 'bg-gray-100 text-gray-900'
                      : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                  }`}
                >
                  <Icon className="h-5 w-5 mr-3" />
                  {item.name}
                </Link>
              );
            })}
          </nav>

          {/* Footer */}
          <div className="flex-shrink-0 p-4 border-t">
            <div className="flex items-center mb-4 px-2 py-2 text-sm text-gray-600">
              <Coins className="h-5 w-5 mr-3 text-yellow-500" />
              <span>
                {subscription?.subscription?.plan_type === 'yearly' || subscription?.plan_type === 'yearly'
                  ? "Unlimited Credits"
                  : (credits !== null && credits > 0
                    ? `${credits} Credits`
                    : "No credits available")}
              </span>
            </div>
            {credits !== null && credits <= 2 && subscription?.plan_type !== 'yearly' && subscription?.subscription?.plan_type !== 'yearly' && (
              <Link
                to="/billing"
                className="w-full inline-flex justify-center items-center px-3 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
              >
                Purchase Credits
              </Link>
            )}
            <button
              onClick={() => navigate('/settings')}
              className="flex items-center w-full px-2 py-2 text-sm font-medium text-gray-600 rounded-md hover:bg-gray-50 hover:text-gray-900"
            >
              <Settings className="h-5 w-5 mr-3" />
              Settings
            </button>
            <button
              onClick={handleSignOut}
              className="flex items-center w-full px-2 py-2 text-sm font-medium text-gray-600 rounded-md hover:bg-gray-50 hover:text-gray-900"
            >
              <LogOut className="h-5 w-5 mr-3" />
              Logout
            </button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div>
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          {children}
        </main>
      </div>
    </div>
  );
}