import React, { useEffect, useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { FileText, BookmarkCheck, Layout as LayoutIcon, LogOut, Coins } from 'lucide-react';
import { getUserCredits } from '../services/api';
import logo from '../assets/logo.png';

const Layout = ({ children }: { children: React.ReactNode }) => {
  const { signOut, user } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
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
    await signOut();
    navigate('/login');
  };

  const navigation = [
    { name: 'Dashboard', href: '/dashboard', icon: LayoutIcon },
    { name: 'My Resumes', href: '/my-resumes', icon: FileText },
    { name: 'Saved Jobs', href: '/saved-jobs', icon: BookmarkCheck },
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Sidebar */}
      <div className="fixed inset-y-0 left-0 w-64 bg-white border-r">
        <div className="flex flex-col h-full">
          <div className="flex items-center justify-center h-24 px-4 border-b">
            <Link to="/dashboard" className="flex items-center">
              <img
                src={logo}
                alt="ResumeAI Logo"
                className="h-[100px] w-[100px] object-contain"
              />
            </Link>
          </div>
          <nav className="flex-1 px-4 py-4 space-y-1">
            {navigation.map((item) => {
              const Icon = item.icon;
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  className={`flex items-center px-2 py-2 rounded-md ${
                    location.pathname === item.href
                      ? 'bg-indigo-50 text-indigo-600'
                      : 'text-gray-600 hover:bg-gray-50'
                  }`}
                >
                  <Icon className="h-5 w-5 mr-3" />
                  {item.name}
                </Link>
              );
            })}
          </nav>

          <div className="px-4 py-4 border-t space-y-2">
            <div className="flex items-center px-2 py-2 text-gray-600">
              <Coins className="h-5 w-5 mr-3 text-yellow-500" />
              <span>
                {credits === null ? (
                  "Loading credits..."
                ) : (
                  <>{credits} credits remaining</>
                )}
              </span>
            </div>
            <button
              onClick={handleSignOut}
              className="flex items-center w-full px-2 py-2 text-gray-600 rounded-md hover:bg-gray-50"
            >
              <LogOut className="h-5 w-5 mr-3" />
              Sign Out
            </button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="pl-64">
        <main className="py-6">
          {children}
        </main>
      </div>
    </div>
  );
};

export default Layout;