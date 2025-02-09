import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { FileText, BookmarkCheck, LogOut, Home, Settings, CreditCard, Menu, X } from 'lucide-react';
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
  const { signOut } = useAuth();
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

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
      {/* Mobile Menu Button */}
      <button
        onClick={() => setIsSidebarOpen(!isSidebarOpen)}
        className="lg:hidden fixed top-4 left-4 p-2 rounded-md text-gray-600 z-50 bg-white shadow-sm"
      >
        {isSidebarOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
      </button>

      {/* Backdrop for mobile */}
      {isSidebarOpen && (
        <div
          className="fixed inset-0 bg-black/50 lg:hidden z-40"
          onClick={() => setIsSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <div
        className={`fixed inset-y-0 left-0 w-64 bg-white border-r transform transition-transform duration-300 ease-in-out z-50 ${
          isSidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        }`}
      >
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="flex items-center justify-center h-24 px-4 border-b">
            <Link to="/dashboard" className="flex items-center">
              <img
                src={logo}
                alt="ResumeAI Logo"
                className="h-[150px] w-[150px]  object-contain"
              />
            </Link>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-2 py-4 space-y-1 overflow-y-auto">
            {navigation.map((item) => {
              const Icon = item.icon;
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  className="flex items-center px-3 py-3 text-base font-medium rounded-lg text-gray-600 hover:bg-gray-50 hover:text-gray-900"
                  onClick={() => setIsSidebarOpen(false)}
                >
                  <Icon className="h-6 w-6 mr-3" />
                  {item.name}
                </Link>
              );
            })}
          </nav>

          {/* Footer */}
          <div className="flex-shrink-0 p-4 border-t">
            <button
              onClick={() => {
                navigate('/settings');
                setIsSidebarOpen(false);
              }}
              className="flex items-center w-full px-3 py-3 text-base font-medium text-gray-600 rounded-lg hover:bg-gray-50 hover:text-gray-900"
            >
              <Settings className="h-6 w-6 mr-3" />
              Settings
            </button>
            <button
              onClick={handleSignOut}
              className="flex items-center w-full px-3 py-3 text-base font-medium text-gray-600 rounded-lg hover:bg-gray-50 hover:text-gray-900"
            >
              <LogOut className="h-6 w-6 mr-3" />
              Logout
            </button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className={`lg:ml-64 transition-all duration-300 ${isSidebarOpen ? 'ml-64' : 'ml-0'}`}>
        <main className="p-6">
            <div className="w-full p-6">
              {children}
            </div>
        </main>
      </div>
    </div>
  );
}