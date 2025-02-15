import React, { createContext, useContext, useState, useCallback, useEffect } from 'react';
import axios from 'axios';
import { useAuth } from './AuthContext';

interface CreditsContextType {
  credits: number | null;
  updateCredits: () => Promise<void>;
  forceUpdate: () => Promise<void>;
}

const CreditsContext = createContext<CreditsContextType | undefined>(undefined);

export function CreditsProvider({ children }: { children: React.ReactNode }) {
  const { user } = useAuth();
  
  // Initialize from localStorage if available
  const [credits, setCredits] = useState<number | null>(() => {
    const storedCredits = localStorage.getItem('user_credits');
    if (storedCredits) {
      try {
        const { credits, lastChecked } = JSON.parse(storedCredits);
        const now = new Date();
        const lastCheck = new Date(lastChecked);
        // Use cached credits if less than 5 minutes old
        if (now.getTime() - lastCheck.getTime() < 5 * 60 * 1000) {
          return credits;
        }
      } catch (error) {
        console.error('Error parsing stored credits:', error);
      }
    }
    return null;
  });

  const updateCredits = useCallback(async () => {
    if (!user?.id) return;
    
    try {
      const creditsResponse = await axios.get(`${import.meta.env.VITE_RESUME_API_URL}/api/credits`, {
        headers: { 'X-User-Id': user.id }
      });
      
      const userCredits = creditsResponse.data.credits;
      setCredits(userCredits);
      
      // Store credits with timestamp
      localStorage.setItem('user_credits', JSON.stringify({
        credits: userCredits,
        lastChecked: new Date().toISOString()
      }));
    } catch (error) {
      console.error('Error fetching credits:', error);
    }
  }, [user?.id]);

  // Force update bypasses cache and updates immediately
  const forceUpdate = useCallback(async () => {
    if (!user?.id) return;
    
    try {
      const creditsResponse = await axios.get(`${import.meta.env.VITE_RESUME_API_URL}/api/credits`, {
        headers: { 'X-User-Id': user.id }
      });
      
      const userCredits = creditsResponse.data.credits;
      setCredits(userCredits);
      
      // Store credits with timestamp
      localStorage.setItem('user_credits', JSON.stringify({
        credits: userCredits,
        lastChecked: new Date().toISOString()
      }));
    } catch (error) {
      console.error('Error fetching credits:', error);
    }
  }, [user?.id]);

  // Fetch credits only when:
  // 1. User is available AND
  // 2. We don't have credits in state OR cached credits are expired
  useEffect(() => {
    const checkAndUpdateCredits = async () => {
      if (!user?.id) return;
      
      const storedCredits = localStorage.getItem('user_credits');
      if (storedCredits) {
        try {
          const { credits: cachedCredits, lastChecked } = JSON.parse(storedCredits);
          const now = new Date();
          const lastCheck = new Date(lastChecked);
          
          // If cache is less than 5 minutes old, use it
          if (now.getTime() - lastCheck.getTime() < 5 * 60 * 1000) {
            setCredits(cachedCredits);
            return;
          }
        } catch (error) {
          console.error('Error checking stored credits:', error);
        }
      }
      
      // If we get here, either no cache or cache expired
      await updateCredits();
    };

    checkAndUpdateCredits();
  }, [user?.id, updateCredits]);

  return (
    <CreditsContext.Provider value={{ credits, updateCredits, forceUpdate }}>
      {children}
    </CreditsContext.Provider>
  );
}

export function useCredits() {
  const context = useContext(CreditsContext);
  if (context === undefined) {
    throw new Error('useCredits must be used within a CreditsProvider');
  }
  return context;
}
