import React, { useEffect, useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { FileText, BookmarkCheck, Layout as LayoutIcon, LogOut, Coins, CreditCard, Home } from 'lucide-react';
import { getUserCredits } from '../services/api';
import logo from '../assets/logo.png';

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

export default function Layout({ children }: LayoutProps) {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, signOut } = useAuth();
  const [credits, setCredits] = useState<number | null>(null);

  useEffect(() => {
    const loadCredits = async () => {
      if (user?.id) {
        try {
          const userCredits = await getUserCredits();
          setCredits(userCredits);
        } catch (error) {
          console.error('Error loading credits:', error);
        }
      }
    };
    loadCredits();
  }, [user?.id]);

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
                {credits === null ? (
                  "Loading credits..."
                ) : (
                  <>{credits} Credits</>
                )}
              </span>
            </div>
            {credits !== null && credits <= 2 && (
              <Link
                to="/billing"
                className="w-full inline-flex justify-center items-center px-3 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
              >
                Purchase Credits
              </Link>
            )}
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