import React, { useState, useEffect } from 'react';
import { FileUpload } from './components/FileUpload';
import { TimeSelector } from './components/TimeSelector';
import { ProcessingLoader } from './components/ProcessingLoader';
import { StudyPack } from './components/StudyPack';
import GoogleLogin from './components/GoogleLogin';
import UserProfile from './components/UserProfile';
import History from './components/History';
import Pricing from './components/Pricing';
import Subscription from './components/Subscription';
import { GraduationCap, Sparkles, CreditCard } from 'lucide-react';
import { useAuthStore } from './stores/authStore';
import { useSettingsStore } from './stores/settingsStore';
import { usePricingStore } from './stores/pricingStore';
import { pdfAPI, historyAPI } from './services/api';
import type { UserQuota } from './stores/pricingStore';

type AppState = 'upload' | 'time-select' | 'processing' | 'results' | 'history' | 'history-item' | 'auth-required' | 'pricing' | 'subscription';

// Trick TypeScript into inferring all AppState values
const _allStates: AppState[] = ['upload', 'time-select', 'processing', 'results', 'history', 'history-item', 'auth-required', 'pricing', 'subscription'];

function App() {
  const { user, isAuthenticated, token, error, clearError } = useAuthStore();
  const { settings } = useSettingsStore();
  const [currentState, setCurrentState] = useState<AppState>('upload' as AppState);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [selectedTime, setSelectedTime] = useState<number | null>(null);
  const [processedData, setProcessedData] = useState<any>(null);
  const [currentHistoryId, setCurrentHistoryId] = useState<number | undefined>(undefined);
  const [loadingHistoryItem, setLoadingHistoryItem] = useState(false);
  const [historyItemData, setHistoryItemData] = useState<any>(null);
  const { subscriptionStatus, userQuota, fetchUserQuota } = usePricingStore();
  const [showSubscribeModal, setShowSubscribeModal] = useState(false);
  const [quotaError, setQuotaError] = useState<string | null>(null);

  // Apply theme settings
  useEffect(() => {
    const root = document.documentElement;
    
    // Apply font size
    root.style.fontSize = settings.fontSize === 'small' ? '14px' : 
                         settings.fontSize === 'large' ? '18px' : '16px';
    
    // Apply theme
    if (settings.theme === 'dark' || (settings.theme === 'auto' && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
      root.classList.add('dark');
    } else {
      root.classList.remove('dark');
    }
  }, [settings.theme, settings.fontSize]);

  // Debug state changes
  useEffect(() => {
    console.log('App: Current state changed to:', currentState);
  }, [currentState]);

  // Clear error when component unmounts
  useEffect(() => {
    return () => {
      clearError();
    };
  }, [clearError]);

  const handleFileSelect = async (file: File) => {
    try {
      // Fetch the latest quota and use the response directly
      const quota: UserQuota = await fetchUserQuota();
      if (
        quota &&
        quota.plan_type === 'free' &&
        quota.pdf_limit !== null &&
        quota.pdfs_used >= quota.pdf_limit
      ) {
        setQuotaError('You have used all 3 free PDFs. Please purchase a plan to continue.');
        setShowSubscribeModal(true);
        return;
      }
      console.log('App: handleFileSelect called with file:', file.name);
    if (!isAuthenticated) {
        console.log('App: User not authenticated, showing auth popup');
      // If not authenticated, show auth popup and store the file
      setSelectedFile(file);
      setCurrentState('auth-required');
      return;
    }
    
      console.log('App: User authenticated, proceeding to time select');
    setSelectedFile(file);
    setCurrentState('time-select');
    } catch (err: any) {
      setQuotaError('An error occurred. Please try again.');
      setShowSubscribeModal(true);
    }
  };

  const handleTimeSelect = (time: number) => {
    setSelectedTime(time);
    setCurrentState('processing');
  };

  const handleProcessingComplete = (data: any) => {
    setProcessedData(data);
    setCurrentState('results');
  };

  const handleStartOver = () => {
    setCurrentState('upload');
    setSelectedFile(null);
    setSelectedTime(null);
    setProcessedData(null);
    setCurrentHistoryId(undefined);
  };

  const handleShowHistory = () => {
    if (!isAuthenticated) {
      setCurrentState('auth-required');
      return;
    }
    setCurrentState('history');
  };

  const handleViewHistoryItem = (historyId: number) => {
    setCurrentHistoryId(historyId);
    setCurrentState('history-item');
  };

  const handleBackFromHistory = () => {
    setCurrentState('upload');
  };

  const handleAuthSuccess = () => {
    // After successful authentication, proceed with the stored file
    if (selectedFile) {
      setCurrentState('time-select');
    } else {
      setCurrentState('upload');
    }
  };

  const removeFile = () => {
    setSelectedFile(null);
    setCurrentState('upload');
  };

  useEffect(() => {
    if (currentState === 'history-item' && currentHistoryId) {
      loadHistoryItem();
    }
  }, [currentState, currentHistoryId]);

  const loadHistoryItem = async () => {
    if (!currentHistoryId) return;
    
    try {
      setLoadingHistoryItem(true);
      const data = await historyAPI.getHistoryItem(currentHistoryId);
      setHistoryItemData(data);
    } catch (err: any) {
      console.error('Failed to load history item:', err);
      alert('Failed to load history item');
      setCurrentState('history');
    } finally {
      setLoadingHistoryItem(false);
    }
  };

  const handleShowPricing = () => {
    setCurrentState('pricing');
  };

  const handleShowSubscription = () => {
    setCurrentState('subscription');
  };

  const handleBackFromPricing = () => {
    setCurrentState('upload');
  };

  const handleBackFromSubscription = () => {
    console.log('Back from subscription clicked');
    setCurrentState('upload');
  };

  const hasActiveSubscription = subscriptionStatus?.has_subscription;
  const handlePricingClick = () => {
    if (hasActiveSubscription) {
      handleShowSubscription();
    } else {
      handleShowPricing();
    }
  };

  let mainContent = null;

  if (currentState === 'auth-required') {
    console.log('App: Rendering auth-required state');
    mainContent = (
      <div className="min-h-screen bg-[#0B0F1A] flex items-center justify-center">
        <div className="max-w-md w-full mx-auto p-8">
          <div className="text-center mb-8">
            <div className="w-16 h-16 bg-gradient-to-br from-[#7B61FF] to-[#5ED3F3] rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-lg">
              <GraduationCap className="w-8 h-8 text-white" />
            </div>
            <h1 className="text-3xl font-bold bg-gradient-to-r from-[#7B61FF] to-[#5ED3F3] bg-clip-text text-transparent mb-2">
              Sign In Required
            </h1>
            <p className="text-[#BFC9D9]">Please sign in to process your PDF</p>
            {selectedFile && (
              <p className="text-sm text-[#BFC9D9]/70 mt-2">
                Selected file: {selectedFile.name}
              </p>
            )}
          </div>
          <div className="bg-[#0B0F1A]/80 backdrop-blur-xl rounded-2xl p-8 shadow-2xl border border-[#2B3A55]">
            <GoogleLogin onSuccess={handleAuthSuccess} />
            {error && (
              <div className="mt-4 p-3 bg-red-900/20 border border-red-500/30 rounded-lg">
                <p className="text-red-400 text-sm">{error}</p>
              </div>
            )}
            <button
              onClick={() => setCurrentState('upload')}
              className="mt-4 w-full px-4 py-2 text-[#BFC9D9] bg-[#2B3A55] rounded-lg hover:bg-[#2B3A55]/80 transition-colors"
            >
              Cancel
            </button>
          </div>
        </div>
      </div>
    );
  } else if (currentState === 'pricing') {
    mainContent = <Pricing onBackToHome={handleBackFromPricing} />;
  } else if (currentState === 'subscription') {
    mainContent = <Subscription onBackToHome={handleBackFromSubscription} />;
  } else {
    mainContent = (
    <div className="min-h-screen bg-[#0B0F1A]">
      {/* Header */}
      <header className="border-b border-[#2B3A55] bg-[#0B0F1A]/80 backdrop-blur-xl sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-gradient-to-br from-[#7B61FF] to-[#5ED3F3] rounded-xl flex items-center justify-center shadow-lg">
                <GraduationCap className="w-6 h-6 text-white" />
              </div>
              <button
                onClick={() => setCurrentState('upload')}
                className="text-left hover:opacity-80 transition-opacity"
              >
                <div>
                  <h1 className="text-2xl font-bold bg-gradient-to-r from-[#7B61FF] to-[#5ED3F3] bg-clip-text text-transparent">
                    SnapReads
                  </h1>
                  <p className="text-sm text-[#BFC9D9]">Smart study packs from any PDF</p>
                </div>
              </button>
            </div>
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2 text-sm text-[#BFC9D9]">
                <Sparkles className="w-4 h-4" />
                <span>AI-Powered Learning</span>
              </div>
              {isAuthenticated ? (
                <UserProfile onShowHistory={handleShowHistory} />
              ) : (
                <button
                    onClick={() => {
                      console.log('App: Login button clicked, setting state to auth-required');
                      setCurrentState('auth-required');
                    }}
                  className="flex items-center space-x-2 px-4 py-2 bg-gradient-to-r from-[#7B61FF] to-[#5ED3F3] text-white rounded-lg hover:from-[#6A52E8] hover:to-[#4EC2E3] transition-all duration-300 shadow-lg hover:shadow-xl"
                >
                  <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M3 3a1 1 0 011 1v12a1 1 0 11-2 0V4a1 1 0 011-1zm7.707 3.293a1 1 0 010 1.414L9.414 9H17a1 1 0 110 2H9.414l1.293 1.293a1 1 0 01-1.414 1.414l-3-3a1 1 0 010-1.414l3-3a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                  <span>Login</span>
                </button>
              )}
              <button
                  onClick={handlePricingClick}
                className="flex items-center space-x-2 px-4 py-2 bg-gradient-to-r from-[#7B61FF] to-[#5ED3F3] text-white rounded-lg hover:from-[#6A52E8] hover:to-[#4EC2E3] transition-all duration-300 shadow-lg hover:shadow-xl"
              >
                <CreditCard className="w-4 h-4" />
                  <span>{hasActiveSubscription ? 'Subscription' : 'Pricing'}</span>
              </button>
            </div>
          </div>
        </div>
        {/* Navigation */}
          {((currentState as string) !== 'pricing' && (currentState as string) !== 'subscription' && (currentState as string) !== 'auth-required') && (
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-2">
            <nav className="flex items-center space-x-6">
              <button
                onClick={() => setCurrentState('upload')}
                className={`text-sm font-medium transition-colors ${
                    (currentState as string) === 'upload' 
                    ? 'text-[#7B61FF]' 
                    : 'text-[#BFC9D9] hover:text-white'
                }`}
              >
                Home
              </button>
              {isAuthenticated && (
                <button
                  onClick={handleShowHistory}
                  className={`text-sm font-medium transition-colors ${
                      (currentState as string) === 'history' 
                      ? 'text-[#7B61FF]' 
                      : 'text-[#BFC9D9] hover:text-white'
                  }`}
                >
                  History
                </button>
              )}
              <button
                  onClick={handlePricingClick}
                className={`text-sm font-medium transition-colors ${
                    (currentState as string) === 'pricing' 
                    ? 'text-[#7B61FF]' 
                    : 'text-[#BFC9D9] hover:text-white'
                }`}
              >
                  {hasActiveSubscription ? 'Subscription' : 'Pricing'}
              </button>
            </nav>
          </div>
        )}
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {currentState === 'upload' && (
          <div className="text-center space-y-8">
            <div className="space-y-4">
              <h2 className="text-4xl font-bold text-white">
                Transform Any PDF Into a
                <span className="bg-gradient-to-r from-[#7B61FF] to-[#5ED3F3] bg-clip-text text-transparent">
                  {' '}Perfect Study Pack
                </span>
              </h2>
              <p className="text-xl text-[#BFC9D9] max-w-3xl mx-auto">
                Upload your textbooks, research papers, or class notes and get a personalized study experience 
                tailored to your available time. Whether you have 10 minutes or 30, we'll help you focus on what matters most.
              </p>
              {!isAuthenticated && (
                <p className="text-sm text-[#BFC9D9]/70">
                  You'll be prompted to sign in with Google when you upload your first PDF
                </p>
              )}
            </div>
            <FileUpload
              onFileSelect={handleFileSelect}
              selectedFile={selectedFile}
              onRemoveFile={removeFile}
            />
            <div className="grid md:grid-cols-3 gap-8 max-w-4xl mx-auto mt-12">
              <div className="text-center">
                <div className="w-16 h-16 bg-gradient-to-br from-[#3BE8B0] to-[#2BC8A0] rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-lg">
                  <span className="text-2xl font-bold text-white">1</span>
                </div>
                <h3 className="font-semibold text-white mb-2">Upload PDF</h3>
                <p className="text-[#BFC9D9] text-sm">Any size, any subject - we handle it all</p>
              </div>
              <div className="text-center">
                <div className="w-16 h-16 bg-gradient-to-br from-[#7AA0FF] to-[#5ED3F3] rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-lg">
                  <span className="text-2xl font-bold text-white">2</span>
                </div>
                <h3 className="font-semibold text-white mb-2">Choose Time</h3>
                <p className="text-[#BFC9D9] text-sm">10, 20, or 30 minutes - you decide</p>
              </div>
              <div className="text-center">
                <div className="w-16 h-16 bg-gradient-to-br from-[#D877F9] to-[#B85EF3] rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-lg">
                  <span className="text-2xl font-bold text-white">3</span>
                </div>
                <h3 className="font-semibold text-white mb-2">Study Smart</h3>
                <p className="text-[#BFC9D9] text-sm">Focus on key concepts and takeaways</p>
              </div>
            </div>
          </div>
        )}

        {currentState === 'time-select' && (
          <div className="space-y-8">
            <TimeSelector
              selectedTime={selectedTime}
              onTimeSelect={handleTimeSelect}
            />
          </div>
        )}

        {currentState === 'processing' && selectedFile && selectedTime && (
          <div className="space-y-8">
            <ProcessingLoader 
              onComplete={handleProcessingComplete}
              selectedFile={selectedFile}
              selectedTime={selectedTime}
            />
          </div>
        )}

        {currentState === 'results' && selectedFile && selectedTime && processedData && (
          <StudyPack
            timeLimit={selectedTime}
            fileName={selectedFile.name}
            onStartOver={handleStartOver}
            processedData={processedData}
            historyId={currentHistoryId}
          />
        )}

        {currentState === 'history' && (
          <History
            onBack={handleBackFromHistory}
            onViewItem={handleViewHistoryItem}
          />
        )}

        {currentState === 'history-item' && (
          <div className="space-y-6">
            {loadingHistoryItem ? (
              <div className="flex items-center justify-center min-h-64">
                <div className="text-center">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#7B61FF] mx-auto"></div>
                  <p className="mt-2 text-[#BFC9D9]">Loading study pack...</p>
                </div>
              </div>
            ) : historyItemData ? (
              <StudyPack
                timeLimit={historyItemData.total_reading_time_minutes}
                fileName={historyItemData.original_filename}
                onStartOver={() => setCurrentState('history')}
                processedData={historyItemData}
                historyId={currentHistoryId}
              />
            ) : null}
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-[#2B3A55] bg-[#0B0F1A]/80 backdrop-blur-xl mt-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="text-center">
            <p className="text-[#BFC9D9]">
              Built with AI to help you study smarter, not harder.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
  }

  if (showSubscribeModal) {
    mainContent = (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-60">
        <div className="bg-white rounded-xl shadow-lg p-8 max-w-md w-full text-center">
          <h2 className="text-2xl font-bold mb-4 text-purple-800">Out of Free PDFs</h2>
          <p className="mb-6 text-gray-700">{quotaError || 'You have used all your free PDFs. Please purchase a plan to continue using SnapReads.'}</p>
          <button
            className="px-6 py-3 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-lg font-semibold text-lg hover:from-purple-700 hover:to-pink-700 transition-colors"
            onClick={() => { setShowSubscribeModal(false); setCurrentState('pricing'); }}
          >
            View Subscription Plans
          </button>
          <button
            className="block mt-4 text-gray-500 underline"
            onClick={() => setShowSubscribeModal(false)}
          >
            Maybe Later
          </button>
        </div>
      </div>
    );
  }

  return mainContent;
}

export default App;