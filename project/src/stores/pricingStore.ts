import { create } from 'zustand';
import api from '../services/api';
import { useAuthStore } from './authStore';

export interface PricingPlan {
  id: string;
  name: string;
  price: number; // in paise
  pdf_limit: number | null;
  features: string[];
  popular: boolean;
}

export interface UserQuota {
  plan_type: 'free' | 'starter' | 'unlimited';
  pdfs_used: number;
  pdf_limit: number | null;
  can_process: boolean;
  message: string;
}

export interface SubscriptionStatus {
  has_subscription: boolean;
  plan_type: string;
  status?: string;
  current_period_start?: string;
  current_period_end?: string;
  cancel_at_period_end?: boolean;
  days_remaining?: number;
  message: string;
}

export interface CouponValidation {
  valid: boolean;
  discount_amount: number;
  message: string;
}

export interface SubscriptionOrder {
  subscription_id?: string;
  customer_id?: string;
  plan_id?: string;
  status?: string;
  current_start?: number;
  current_end?: number;
  key?: string;
  prefill?: {
    email: string;
    name: string;
  };
  is_free?: boolean; // Optional property for free plans or coupons
  order_id?: string;
  message?: string; // Optional message for free/coupon responses
}

interface PricingStore {
  plans: Record<string, PricingPlan> | null;
  userQuota: UserQuota | null;
  subscriptionStatus: SubscriptionStatus | null;
  selectedPlan: string;
  couponCode: string;
  couponValidation: CouponValidation | null;
  isLoading: boolean;
  error: string | null;
  
  // Actions
  fetchPlans: () => Promise<void>;
  fetchUserQuota: () => Promise<UserQuota>;
  fetchSubscriptionStatus: () => Promise<void>;
  validateCoupon: (couponCode: string, userEmail?: string) => Promise<void>;
  createSubscription: (planType: string, couponCode?: string) => Promise<SubscriptionOrder>;
  verifySubscription: (paymentId: string, subscriptionId: string, signature: string, planType: string) => Promise<void>;
  cancelSubscription: (cancelAtPeriodEnd?: boolean) => Promise<void>;
  setSelectedPlan: (plan: string) => void;
  setCouponCode: (code: string) => void;
  clearError: () => void;
}

export const usePricingStore = create<PricingStore>((set, get) => ({
  plans: null,
  userQuota: null,
  subscriptionStatus: null,
  selectedPlan: '',
  couponCode: '',
  couponValidation: null,
  isLoading: false,
  error: null,

  fetchPlans: async () => {
    try {
      console.log('Fetching pricing plans...');
      set({ isLoading: true, error: null });
      const response = await api.get('/pricing/plans');
      console.log('Pricing plans response:', response.data);
      set({ plans: response.data.plans, isLoading: false });
    } catch (error) {
      console.error('Error fetching plans:', error);
      set({ 
        error: 'Failed to load pricing plans', 
        isLoading: false 
      });
    }
  },

  fetchUserQuota: async (): Promise<UserQuota> => {
    try {
      set({ isLoading: true, error: null });
      const response = await api.get('/pricing/user-quota');
      set({ userQuota: response.data, isLoading: false });
      return response.data;
    } catch (error) {
      console.error('Error fetching user quota:', error);
      set({ 
        error: 'Failed to load user quota', 
        isLoading: false 
      });
      throw error;
    }
  },

  fetchSubscriptionStatus: async () => {
    try {
      set({ isLoading: true, error: null });
      const response = await api.get('/pricing/subscription');
      set({ subscriptionStatus: response.data, isLoading: false });
    } catch (error) {
      console.error('Error fetching subscription status:', error);
      set({ 
        error: 'Failed to load subscription status', 
        isLoading: false 
      });
    }
  },

  validateCoupon: async (couponCode: string, userEmail?: string) => {
    try {
      set({ isLoading: true, error: null });
      const response = await api.post('/pricing/validate-coupon', {
        coupon_code: couponCode,
        user_email: userEmail
      });
      set({ 
        couponValidation: response.data, 
        isLoading: false 
      });
    } catch (error) {
      console.error('Error validating coupon:', error);
      set({ 
        error: 'Failed to validate coupon', 
        isLoading: false 
      });
    }
  },

  createSubscription: async (planType: string, couponCode?: string) => {
    try {
      set({ isLoading: true, error: null });
      const { user } = useAuthStore.getState();
      const response = await api.post('/pricing/create-subscription', {
        plan_type: planType,
        coupon_code: couponCode
      });
      set({ isLoading: false });
      
      // Handle both subscription orders and free plan responses
      if (response.data.is_free) {
        return response.data; // Return the free plan response as-is
      } else {
        return response.data as SubscriptionOrder; // Return as SubscriptionOrder for paid plans
      }
    } catch (error) {
      console.error('Error creating subscription:', error);
      set({ 
        error: 'Failed to create subscription', 
        isLoading: false 
      });
      throw error;
    }
  },

  verifySubscription: async (paymentId: string, subscriptionId: string, signature: string, planType: string) => {
    try {
      set({ isLoading: true, error: null });
      await api.post('/pricing/verify-subscription', {
        payment_id: paymentId,
        subscription_id: subscriptionId,
        signature: signature,
        plan_type: planType
      });
      // Refresh subscription status after successful payment
      await get().fetchSubscriptionStatus();
      set({ isLoading: false });
    } catch (error) {
      console.error('Error verifying subscription:', error);
      set({ 
        error: 'Failed to verify subscription', 
        isLoading: false 
      });
      throw error;
    }
  },

  cancelSubscription: async (cancelAtPeriodEnd: boolean = true) => {
    try {
      set({ isLoading: true, error: null });
      await api.post('/pricing/cancel-subscription', {
        cancel_at_period_end: cancelAtPeriodEnd
      });
      
      // Refresh subscription status after cancellation
      await get().fetchSubscriptionStatus();
      set({ isLoading: false });
    } catch (error) {
      console.error('Error cancelling subscription:', error);
      set({ 
        error: 'Failed to cancel subscription', 
        isLoading: false 
      });
      throw error;
    }
  },

  setSelectedPlan: (plan: string) => {
    set({ selectedPlan: plan });
  },

  setCouponCode: (code: string) => {
    set({ couponCode: code });
  },

  clearError: () => {
    set({ error: null });
  }
})); 