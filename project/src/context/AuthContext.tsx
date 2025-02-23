import { createContext, useContext, useEffect, useState } from 'react';
import { User, AuthResponse, Session } from '@supabase/supabase-js';
import { supabase } from '../lib/supabaseClient';

interface AuthContextType {
  session: Session | null;
  loading: boolean;
  signUp: (email: string, password: string) => Promise<AuthResponse>;
  signIn: (email: string, password: string) => Promise<AuthResponse>;
  signInWithGoogle: () => Promise<void>;
  signOut: () => Promise<void>;
  user: User | null;
  setUser: (user: User | null) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [session, setSession] = useState<Session | null>(null);

  useEffect(() => {
    // Aggressive session restoration
    const restoreSession = async () => {
      try {
        // First, check Supabase session
        const { data: supabaseSession } = await supabase.auth.getSession();
        
        if (supabaseSession.session) {
          setSession(supabaseSession.session);
          setUser(supabaseSession.session.user);
        }
      } catch (error) {
        console.error(' Session restoration failed:', error);
        localStorage.removeItem('supabase_session');
      } finally {
        setLoading(false);
      }
    };

    // Initial session restoration
    restoreSession();

    // Subscribe to auth state changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange(async (event, session) => {
      
      if (session) {
        localStorage.setItem('supabase_session', JSON.stringify(session));
        setSession(session);
        setUser(session.user);
      } else {
        localStorage.removeItem('supabase_session');
        setSession(null);
        setUser(null);
      }
    });

    // Periodic session refresh
    const refreshInterval = setInterval(async () => {
      if (session) {
        try {
          const { data } = await supabase.auth.refreshSession({ 
            refresh_token: session.refresh_token 
          });
          
          if (data.session) {
            setSession(data.session);
            localStorage.setItem('supabase_session', JSON.stringify(data.session));
          }
        } catch (error) {
          console.error(' Session Refresh Error:', error);
        }
      }
    }, 30 * 60 * 1000); // Refresh every 30 minutes

    return () => {
      subscription.unsubscribe();
      clearInterval(refreshInterval);
    };
  }, []);

  const signUp = async (email: string, password: string) => {
    const response = await supabase.auth.signUp({
      email,
      password,
      options: {
        data: {
          name: email.split('@')[0], // Set initial name from email
        }
      }
    });
    return response;
  };

  const signIn = async (email: string, password: string) => {
    const response = await supabase.auth.signInWithPassword({
      email,
      password,
    });
    return response;
  };

  const signInWithGoogle = async () => {
    const { error } = await supabase.auth.signInWithOAuth({
      provider: 'google',
      options: {
        redirectTo: `${window.location.origin}/`, // Changed this line
        queryParams: {
          access_type: 'offline',
          prompt: 'consent'
        }
      }
    });
    
    if (error) {
      console.error('Google Sign In Error:', error.message);
      throw error;
    }
  };

  const signOut = async () => {
    const { error } = await supabase.auth.signOut();
    localStorage.removeItem('supabase_session');
    if (error) throw error;
  };

  const value = {
    session,
    user,
    loading,
    signUp,
    signIn,
    signInWithGoogle,
    signOut,
    setUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}