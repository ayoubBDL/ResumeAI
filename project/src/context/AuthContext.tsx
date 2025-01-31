import { createContext, useContext, useEffect, useState } from 'react';
import { User, AuthResponse } from '@supabase/supabase-js';
import { supabase } from '../lib/supabaseClient';

interface AuthContextType {
  session: User | null;
  loading: boolean;
  signUp: (email: string, password: string) => Promise<AuthResponse>;
  signIn: (email: string, password: string) => Promise<AuthResponse>;
  signInWithGoogle: () => Promise<void>;
  signOut: () => Promise<void>;
  user: User | null;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [session, setSession] = useState<User | null>(null);

  useEffect(() => {
    // Check active sessions and subscribe to auth changes
    supabase.auth.getSession().then(({ data: { session } }) => {
      if (session?.user) {
        setSession(session.user);
        setUser(session.user);
      }
      setLoading(false);
    });

    const { data: { subscription } } = supabase.auth.onAuthStateChange(async (_event, session) => {
      if (session?.user) {
        setSession(session.user);
        setUser(session.user);

        // Initialize credits for new OAuth users
        if (_event === 'SIGNED_IN' && session.user.app_metadata?.provider === 'google') {
          try {
            await new Promise(resolve => setTimeout(resolve, 1000)); // Small delay to ensure auth is complete
            const initResponse = await fetch(`${import.meta.env.VITE_API_URL}/api/credits/initialize`, {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
                'X-User-Id': session.user.id
              }
            });
            
            if (!initResponse.ok) {
              console.error('Failed to initialize credits for Google user');
            }
          } catch (error) {
            console.error('Error initializing credits for Google user:', error);
          }
        }
      } else {
        setSession(null);
        setUser(null);
      }
      setLoading(false);
    });

    return () => subscription.unsubscribe();
  }, []);

  const signUp = async (email: string, password: string) => {
    const response = await supabase.auth.signUp({
      email,
      password,
    });

    // If signup was successful, initialize credits through backend
    if (response.data?.user) {
      try {
        const initResponse = await fetch(`${import.meta.env.VITE_API_URL}/api/credits/initialize`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-User-Id': response.data.user.id
          }
        });
        
        if (!initResponse.ok) {
          console.error('Failed to initialize credits');
        }
      } catch (error) {
        console.error('Error initializing credits:', error);
      }
    }

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
        redirectTo: `${window.location.origin}/auth/callback`,
        queryParams: {
          access_type: 'offline',
          prompt: 'consent'
        }
      }
    });
    
    if (error) {
      console.error('Error signing in with Google:', error.message);
      throw error;
    }
  };

  const signOut = async () => {
    const { error } = await supabase.auth.signOut();
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