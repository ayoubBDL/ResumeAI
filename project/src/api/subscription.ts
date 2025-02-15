import axios from 'axios';

export const subscriptionApi = {
  getSubscription: async (userId: string) => {
    try {
      const response = await axios.get(`${import.meta.env.VITE_RESUME_API_URL}/api/subscriptions`, {
        headers: { 'X-User-Id': userId }
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching subscription:', error);
      throw error;
    }
  },

  getCredits: async (userId: string) => {
    try {
      const response = await axios.get(`${import.meta.env.VITE_RESUME_API_URL}/api/credits`, {
        headers: { 'X-User-Id': userId }
      });
      return response.data.credits;
    } catch (error) {
      console.error('Error fetching credits:', error);
      throw error;
    }
  },

  cancelSubscription: async (userId: string) => {
    try {
      const response = await axios.post(`${import.meta.env.VITE_RESUME_API_URL}/api/cancel-subscription`, {}, {
        headers: { 'X-User-Id': userId }
      });
      return response.data;
    } catch (error) {
      console.error('Error cancelling subscription:', error);
      throw error;
    }
  }
}; 