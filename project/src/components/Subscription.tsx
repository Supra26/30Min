import React, { useEffect, useState } from 'react';
import { usePricingStore, SubscriptionStatus } from '../stores/pricingStore';
import { useAuthStore } from '../stores/authStore';

interface SubscriptionProps {
  onBackToHome: () => void;
}

const Subscription: React.FC<SubscriptionProps> = ({ onBackToHome }) => {
  const {
    subscriptionStatus,
    isLoading,
    error,
    fetchSubscriptionStatus,
    cancelSubscription,
    clearError
  } = usePricingStore();

  const { user } = useAuthStore();
  const [showCancelConfirm, setShowCancelConfirm] = useState(false);

  useEffect(() => {
    if (user) {
      fetchSubscriptionStatus();
    }
  }, [fetchSubscriptionStatus, user]);

  const handleCancelSubscription = async (cancelAtPeriodEnd: boolean = true) => {
    try {
      await cancelSubscription(cancelAtPeriodEnd);
      setShowCancelConfirm(false);
      alert(cancelAtPeriodEnd 
        ? 'Subscription will be cancelled at the end of the current period.' 
        : 'Subscription cancelled immediately.');
    } catch (error) {
      alert('Failed to cancel subscription. Please try again.');
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  const getPlanDisplayName = (planType: string) => {
    switch (planType) {
      case 'free': return 'Free Plan';
      case 'starter': return 'Starter Plan';
      case 'unlimited': return 'Unlimited Plan';
      default: return planType;
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-400 mx-auto mb-4"></div>
          <p className="text-purple-200">Loading subscription status...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center">
        <div className="text-center max-w-md mx-auto p-8">
          <div className="bg-red-500/20 border border-red-400/30 rounded-lg p-6 mb-6">
            <h2 className="text-xl font-semibold text-red-300 mb-2">Error Loading Subscription</h2>
            <p className="text-red-200 mb-4">{error}</p>
          </div>
          <button
            onClick={() => {
              clearError();
              fetchSubscriptionStatus();
            }}
            className="px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!subscriptionStatus) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center">
        <div className="text-center">
          <p className="text-purple-200">No subscription data available</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 py-12 px-4">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl md:text-5xl font-bold text-white mb-4">
            Your Subscription
          </h1>
          <p className="text-xl text-purple-200 max-w-2xl mx-auto">
            Manage your SnapReads subscription and billing
          </p>
        </div>

        {/* Subscription Status Card */}
        <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-8 border border-white/20 mb-8">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-2xl font-bold text-white mb-2">
                {getPlanDisplayName(subscriptionStatus.plan_type)}
              </h2>
              <p className="text-purple-200">{subscriptionStatus.message}</p>
            </div>
            <div className="text-right">
              <span className={`px-4 py-2 rounded-full text-sm font-semibold ${
                subscriptionStatus.has_subscription 
                  ? 'bg-green-500/20 text-green-300 border border-green-400/30'
                  : 'bg-blue-500/20 text-blue-300 border border-blue-400/30'
              }`}>
                {subscriptionStatus.has_subscription ? 'Active' : 'Free Plan'}
              </span>
            </div>
          </div>

          {subscriptionStatus.has_subscription && (
            <div className="grid md:grid-cols-2 gap-6 mb-6">
              <div className="bg-white/5 rounded-lg p-4">
                <h3 className="text-lg font-semibold text-white mb-2">Billing Period</h3>
                <p className="text-purple-200 text-sm">
                  <span className="block">Start: {subscriptionStatus.current_period_start && formatDate(subscriptionStatus.current_period_start)}</span>
                  <span className="block">End: {subscriptionStatus.current_period_end && formatDate(subscriptionStatus.current_period_end)}</span>
                </p>
              </div>
              
              <div className="bg-white/5 rounded-lg p-4">
                <h3 className="text-lg font-semibold text-white mb-2">Status</h3>
                <p className="text-purple-200 text-sm">
                  <span className="block">Status: {subscriptionStatus.status}</span>
                  {subscriptionStatus.days_remaining !== undefined && (
                    <span className="block">Days Remaining: {subscriptionStatus.days_remaining}</span>
                  )}
                  {subscriptionStatus.cancel_at_period_end && (
                    <span className="block text-amber-300">⚠️ Cancels at period end</span>
                  )}
                </p>
              </div>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex flex-col sm:flex-row gap-4">
            {subscriptionStatus.has_subscription && !subscriptionStatus.cancel_at_period_end && (
              <button
                onClick={() => setShowCancelConfirm(true)}
                className="px-6 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
              >
                Cancel Subscription
              </button>
            )}
            
            {subscriptionStatus.has_subscription && subscriptionStatus.cancel_at_period_end && (
              <button
                onClick={() => handleCancelSubscription(false)}
                className="px-6 py-3 bg-orange-600 text-white rounded-lg hover:bg-orange-700 transition-colors"
              >
                Cancel Immediately
              </button>
            )}
            
            <button
              onClick={() => {
                console.log('Back button clicked');
                onBackToHome();
              }}
              className="px-6 py-3 bg-white/10 text-white border border-white/20 rounded-lg hover:bg-white/20 transition-colors"
            >
              Back
            </button>
          </div>
        </div>

        {/* Cancel Confirmation Modal */}
        {showCancelConfirm && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-8 border border-white/20 max-w-md mx-4">
              <h3 className="text-xl font-bold text-white mb-4">Cancel Subscription</h3>
              <p className="text-purple-200 mb-6">
                Are you sure you want to cancel your subscription? You can choose to:
              </p>
              
              <div className="space-y-4 mb-6">
                <button
                  onClick={() => handleCancelSubscription(true)}
                  className="w-full px-4 py-3 bg-orange-600 text-white rounded-lg hover:bg-orange-700 transition-colors"
                >
                  Cancel at Period End (Recommended)
                </button>
                
                <button
                  onClick={() => handleCancelSubscription(false)}
                  className="w-full px-4 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
                >
                  Cancel Immediately
                </button>
              </div>
              
              <button
                onClick={() => setShowCancelConfirm(false)}
                className="w-full px-4 py-3 bg-white/10 text-white border border-white/20 rounded-lg hover:bg-white/20 transition-colors"
              >
                Keep Subscription
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Subscription; 