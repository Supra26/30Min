import React, { useEffect, useState } from 'react';
import { usePricingStore, PricingPlan } from '../stores/pricingStore';
import { useAuthStore } from '../stores/authStore';
import Subscription from './Subscription';

declare global {
  interface Window {
    Razorpay: any;
  }
}

const Pricing: React.FC<{ onBackToHome: () => void }> = ({ onBackToHome }) => {
  const {
    plans,
    userQuota,
    subscriptionStatus,
    selectedPlan,
    couponCode,
    couponValidation,
    isLoading,
    error,
    fetchPlans,
    fetchUserQuota,
    fetchSubscriptionStatus,
    validateCoupon,
    createSubscription,
    verifySubscription,
    setSelectedPlan,
    setCouponCode,
    clearError
  } = usePricingStore();

  const { user } = useAuthStore();
  const [showCouponInput, setShowCouponInput] = useState(false);
  const [isProcessingPayment, setIsProcessingPayment] = useState(false);

  useEffect(() => {
    console.log('Pricing component mounted');
    fetchPlans();
    if (user) {
      fetchUserQuota();
      fetchSubscriptionStatus();
    }
  }, [fetchPlans, fetchUserQuota, fetchSubscriptionStatus, user]);

  useEffect(() => {
    console.log('Current state:', { plans, userQuota, subscriptionStatus, isLoading, error });
  }, [plans, userQuota, subscriptionStatus, isLoading, error]);

  useEffect(() => {
    // Load Razorpay script
    const script = document.createElement('script');
    script.src = 'https://checkout.razorpay.com/v1/checkout.js';
    script.async = true;
    document.body.appendChild(script);

    return () => {
      document.body.removeChild(script);
    };
  }, []);

  const handleCouponValidation = async () => {
    if (!couponCode.trim()) return;
    await validateCoupon(couponCode, user?.email);
  };

  const handlePlanSelection = (planId: string) => {
    setSelectedPlan(planId);
    setShowCouponInput(false);
    clearError();
  };

  const formatPrice = (priceInPaise: number) => {
    return `₹${priceInPaise / 100}`;
  };

  const handlePayment = async (plan: PricingPlan) => {
    if (!user) {
      alert('Please login to purchase a plan');
      return;
    }

    try {
      setIsProcessingPayment(true);
      clearError();

      // Create subscription
      const subscriptionData = await createSubscription(plan.id, couponCode || undefined);
      console.log('Subscription data:', subscriptionData);

      // Check if this is a free plan or free coupon
      if (subscriptionData.is_free) {
        alert(subscriptionData.message || 'Free plan activated successfully!');
        setSelectedPlan('');
        setCouponCode('');
        setShowCouponInput(false);
        // Refresh subscription status to show updated plan
        await fetchSubscriptionStatus();
        setIsProcessingPayment(false);
        return;
      }

      // Initialize Razorpay for paid plans (subscription flow)
      const options = {
        key: subscriptionData.key,
        subscription_id: subscriptionData.subscription_id,
        name: 'SnapReads',
        description: `${plan.name} - Monthly Subscription`,
        prefill: subscriptionData.prefill,
        handler: async (response: any) => {
          try {
            console.log('Razorpay response:', response);
            const payload = {
              payment_id: response.razorpay_payment_id,
              subscription_id: response.razorpay_subscription_id,
              signature: response.razorpay_signature,
              plan_type: plan.id
            };
            console.log('Payload to verifySubscription:', payload, 'Full Razorpay response:', response);
            await verifySubscription(
              payload.payment_id,
              payload.subscription_id,
              payload.signature,
              payload.plan_type
            );
            alert('Subscription activated successfully!');
            setSelectedPlan('');
            setCouponCode('');
            setShowCouponInput(false);
          } catch (error) {
            alert('Subscription verification failed. Please contact support.');
          }
        },
        modal: {
          ondismiss: () => {
            setIsProcessingPayment(false);
          }
        }
      };

      const razorpay = new window.Razorpay(options);
      razorpay.open();

    } catch (error) {
      console.error('Payment error:', error);
      alert('Failed to initiate payment. Please try again.');
    } finally {
      setIsProcessingPayment(false);
    }
  };

  const getCurrentPlan = () => {
    if (!userQuota) return null;
    return plans?.[userQuota.plan_type] || null;
  };

  const currentPlan = getCurrentPlan();

  // If user has an active subscription, show subscription management instead of pricing
  if (subscriptionStatus?.has_subscription) {
    return <Subscription onBackToHome={onBackToHome} />;
  }

  if (isLoading && !plans) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-400 mx-auto mb-4"></div>
          <p className="text-purple-200">Loading pricing plans...</p>
        </div>
      </div>
    );
  }

  // Show error state if there's an error and no plans
  if (error && !plans) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center">
        <div className="text-center max-w-md mx-auto p-8">
          <div className="bg-red-500/20 border border-red-400/30 rounded-lg p-6 mb-6">
            <h2 className="text-xl font-semibold text-red-300 mb-2">Unable to Load Pricing</h2>
            <p className="text-red-200 mb-4">{error}</p>
            <p className="text-sm text-red-200/70">Please make sure the backend server is running on {import.meta.env.VITE_API_URL || 'http://localhost:8000'}</p>
          </div>
          <button
            onClick={() => fetchPlans()}
            className="px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 py-12 px-4">
      <div className="max-w-7xl mx-auto">
        {/* Back to Home Button */}
        <div className="mb-6">
          <button
            onClick={onBackToHome}
            className="px-6 py-3 bg-white/10 text-white border border-white/20 rounded-lg hover:bg-white/20 transition-colors"
          >
            ← Back to Home
          </button>
        </div>

        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl md:text-5xl font-bold text-white mb-4">
            Choose Your Plan
          </h1>
          <p className="text-xl text-purple-200 max-w-2xl mx-auto">
            Unlock the full potential of SnapReads with our flexible subscription plans
          </p>
        </div>

        {/* Current Plan Status */}
        {userQuota && (
          <div className="mb-8 max-w-md mx-auto">
            <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-6 border border-white/20">
              <h3 className="text-lg font-semibold text-white mb-2">Current Plan</h3>
              <div className="flex items-center justify-between">
                <span className="text-purple-200">
                  {currentPlan?.name || 'Free Plan'}
                </span>
                <span className="text-sm text-purple-300">
                  {userQuota.pdfs_used}/{userQuota.pdf_limit || '∞'} PDFs used
                </span>
              </div>
              {userQuota.message && (
                <p className="text-amber-300 text-sm mt-2">{userQuota.message}</p>
              )}
            </div>
          </div>
        )}

        {/* Pricing Plans */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {/* Free Plan Card */}
          <div className="bg-white/10 rounded-2xl p-8 border border-white/20 flex flex-col items-center">
            <h2 className="text-2xl font-bold text-white mb-2">Free Plan</h2>
            <div className="text-4xl font-bold text-purple-400 mb-2">Free</div>
            <ul className="text-green-400 mb-6 text-left">
              <li>✔ 3 PDFs total (lifetime)</li>
              <li>✔ Basic summaries</li>
              <li>✔ No login required</li>
            </ul>
            {/* No Choose Plan button for Free Plan */}
          </div>
          {/* Starter Plan Card */}
          <div className="bg-white/10 rounded-2xl p-8 border border-white/20 flex flex-col items-center relative">
            <span className="absolute -top-4 left-1/2 -translate-x-1/2 bg-pink-500 text-white px-4 py-1 rounded-full text-xs font-semibold">Most Popular</span>
            <h2 className="text-2xl font-bold text-white mb-2">Starter Plan</h2>
            <div className="text-4xl font-bold text-purple-400 mb-2">₹49</div>
            <div className="text-white mb-2">per month</div>
            <ul className="text-green-400 mb-6 text-left">
              <li>✔ 15 PDFs per month</li>
              <li>✔ Advanced AI summaries</li>
              <li>✔ Quiz generation</li>
              <li>✔ Download study packs</li>
              <li>✔ User history</li>
            </ul>
            <button className="w-full px-6 py-3 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-lg font-semibold text-lg hover:from-purple-700 hover:to-pink-700 transition-colors" onClick={() => handlePlanSelection('starter')}>Choose Plan</button>
          </div>
          {/* Unlimited Plan Card */}
          <div className="bg-white/10 rounded-2xl p-8 border border-white/20 flex flex-col items-center">
            <h2 className="text-2xl font-bold text-white mb-2">Unlimited Plan</h2>
            <div className="text-4xl font-bold text-purple-400 mb-2">₹199</div>
            <div className="text-white mb-2">per month</div>
            <ul className="text-green-400 mb-6 text-left">
              <li>✔ Unlimited PDFs</li>
              <li>✔ Advanced AI summaries</li>
              <li>✔ Quiz generation</li>
              <li>✔ Download study packs</li>
              <li>✔ User history</li>
              <li>✔ Priority support</li>
            </ul>
            <button className="w-full px-6 py-3 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-lg font-semibold text-lg hover:from-purple-700 hover:to-pink-700 transition-colors" onClick={() => handlePlanSelection('unlimited')}>Choose Plan</button>
          </div>
        </div>

        {/* Coupon Section */}
        {selectedPlan && selectedPlan !== '' && plans && plans[selectedPlan] && plans[selectedPlan].price > 0 && (
          <div className="max-w-md mx-auto mb-8">
            <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-6 border border-white/20">
              <h3 className="text-lg font-semibold text-white mb-4">Have a Coupon?</h3>
              
              {!showCouponInput ? (
                <button
                  onClick={() => setShowCouponInput(true)}
                  className="w-full py-3 px-6 bg-white/10 text-white border border-white/20 rounded-xl hover:bg-white/20 transition-all duration-300"
                >
                  Apply Coupon Code
                </button>
              ) : (
                <div className="space-y-4">
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={couponCode}
                      onChange={(e) => setCouponCode(e.target.value)}
                      placeholder="Enter coupon code"
                      className="flex-1 bg-white/10 border border-white/20 rounded-lg px-4 py-3 text-white placeholder-purple-200 focus:outline-none focus:border-purple-400"
                    />
                    <button
                      onClick={handleCouponValidation}
                      disabled={!couponCode.trim()}
                      className="px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300"
                    >
                      Apply
                    </button>
                  </div>
                  
                  {couponValidation && (
                    <div className={`p-3 rounded-lg text-sm ${
                      couponValidation.valid 
                        ? 'bg-green-500/20 text-green-300 border border-green-400/30' 
                        : 'bg-red-500/20 text-red-300 border border-red-400/30'
                    }`}>
                      {couponValidation.message}
                    </div>
                  )}
                  
                  <button
                    onClick={() => {
                      setShowCouponInput(false);
                      setCouponCode('');
                      clearError();
                    }}
                    className="text-purple-300 hover:text-purple-200 text-sm"
                  >
                    Cancel
                  </button>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Payment Button */}
        {selectedPlan && selectedPlan !== '' && plans && plans[selectedPlan] && (
          <div className="text-center">
            <button
              onClick={() => handlePayment(plans[selectedPlan])}
              disabled={isProcessingPayment || (plans[selectedPlan].price > 0 && !user)}
              className={`px-8 py-4 rounded-xl font-semibold text-lg transition-all duration-300 ${
                isProcessingPayment
                  ? 'bg-gray-600 text-gray-300 cursor-not-allowed'
                  : 'bg-gradient-to-r from-purple-600 to-pink-600 text-white hover:from-purple-700 hover:to-pink-700 shadow-lg shadow-purple-500/25 hover:shadow-xl hover:shadow-purple-500/30'
              }`}
            >
              {isProcessingPayment ? (
                <div className="flex items-center justify-center">
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                  Processing...
                </div>
              ) : plans[selectedPlan].price === 0 ? (
                'Continue with Free Plan'
              ) : !user ? (
                'Login to Subscribe'
              ) : (
                `Subscribe to ${plans[selectedPlan].name}`
              )}
            </button>
          </div>
        )}

        {/* Error Display */}
        {error && (
          <div className="max-w-md mx-auto mt-6">
            <div className="bg-red-500/20 border border-red-400/30 rounded-lg p-4 text-red-300 text-center">
              {error}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Pricing; 