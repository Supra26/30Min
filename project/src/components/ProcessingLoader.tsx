import React, { useState, useEffect } from 'react';
import { Brain, FileText, Lightbulb, CheckCircle, AlertCircle } from 'lucide-react';
import { pdfAPI } from '../services/api';
import { usePricingStore } from '../stores/pricingStore';

interface ProcessingLoaderProps {
  onComplete: (data: any) => void;
  selectedFile: File;
  selectedTime: number;
  setIsProcessing: (processing: boolean) => void;
}

export const ProcessingLoader: React.FC<ProcessingLoaderProps> = ({ 
  onComplete, 
  selectedFile, 
  selectedTime, 
  setIsProcessing
}) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const { userQuota, fetchUserQuota } = usePricingStore();
  const [showSubscribeModal, setShowSubscribeModal] = useState(false);

  const steps = [
    {
      icon: FileText,
      title: 'Analyzing PDF Structure',
      description: 'Scanning headings, sections, and content hierarchy',
    },
    {
      icon: Brain,
      title: 'AI Content Processing',
      description: 'Identifying key concepts and important information',
    },
    {
      icon: Lightbulb,
      title: 'Generating Study Pack',
      description: 'Creating personalized summaries and takeaways',
    },
    {
      icon: CheckCircle,
      title: 'Ready to Study!',
      description: 'Your personalized study pack is complete',
    },
  ];

  useEffect(() => {
    setIsProcessing(true);
    const processPDF = async () => {
      setError(null);
      // Always check quota before processing
      await fetchUserQuota();
      if (
        userQuota &&
        userQuota.plan_type === 'free' &&
        userQuota.pdf_limit !== null &&
        userQuota.pdfs_used >= userQuota.pdf_limit
      ) {
        setShowSubscribeModal(true);
        setIsProcessing(false);
        return;
      }
      try {
        // Use the authenticated API service
        const data = await pdfAPI.processPDF(selectedFile, selectedTime);
        
        // Simulate progress completion
        setProgress(100);
        setCurrentStep(3);
        
        // Refresh quota after processing
        await fetchUserQuota();
        
        // Show subscribe modal if free user and at limit
        if (
          userQuota &&
          userQuota.plan_type === 'free' &&
          userQuota.pdf_limit !== null &&
          userQuota.pdfs_used >= userQuota.pdf_limit
        ) {
          setShowSubscribeModal(true);
        }
        
        // Call onComplete with the real data
        setTimeout(() => {
          onComplete(data);
          setIsProcessing(false);
        }, 1000);
        
      } catch (err: any) {
        if (err.response?.status === 403) {
          setShowSubscribeModal(true);
          setError(err.response?.data?.detail || 'You have used all your free PDFs. Please upgrade to continue.');
          setIsProcessing(false);
          return;
        }
        console.error('Error processing PDF:', err);
        setError(err.response?.data?.detail || err.message || 'Failed to process PDF');
        setIsProcessing(false);
      }
    };

    // Start processing after a short delay
    const timer = setTimeout(processPDF, 1000);
    return () => clearTimeout(timer);
  }, [selectedFile, selectedTime, onComplete, fetchUserQuota, userQuota]);

  useEffect(() => {
    const timer = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 90) {
          clearInterval(timer);
          return 90; // Stop at 90% until API call completes
        }
        return prev + 2;
      });
    }, 100);

    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    const stepTimer = setInterval(() => {
      setCurrentStep((prev) => {
        if (prev < steps.length - 2) { // Don't go to last step until API completes
          return prev + 1;
        }
        clearInterval(stepTimer);
        return prev;
      });
    }, 1500);

    return () => clearInterval(stepTimer);
  }, []);

  if (error) {
    return (
      <div className="w-full max-w-2xl mx-auto">
        <div className="bg-[#0B0F1A]/80 backdrop-blur-xl rounded-2xl p-8 shadow-2xl border border-[#2B3A55]">
          <div className="text-center">
            <div className="w-16 h-16 bg-red-900/20 rounded-full flex items-center justify-center mx-auto mb-4 border border-red-500/30">
              <AlertCircle className="w-8 h-8 text-red-400" />
            </div>
            <h2 className="text-2xl font-bold text-white mb-2">
              Processing Failed
            </h2>
            <p className="text-[#BFC9D9] mb-6">
              {error}
            </p>
            <button 
              onClick={() => window.location.reload()}
              className="px-6 py-3 bg-gradient-to-r from-[#7B61FF] to-[#5ED3F3] text-white rounded-lg hover:shadow-[0_0_15px_rgba(123,97,255,0.4)] transition-all duration-200"
            >
              Try Again
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <>
    <div className="w-full max-w-2xl mx-auto">
      <div className="bg-[#0B0F1A]/80 backdrop-blur-xl rounded-2xl p-8 shadow-2xl border border-[#2B3A55]">
        <div className="text-center mb-8">
          <h2 className="text-2xl font-bold text-white mb-2">
            Processing Your PDF
          </h2>
          <p className="text-[#BFC9D9]">
            Our AI is analyzing your document to create the perfect study pack
          </p>
        </div>

        {/* Progress Bar */}
        <div className="mb-8">
          <div className="flex justify-between text-sm text-[#BFC9D9] mb-2">
            <span>Progress</span>
            <span>{Math.round(progress)}%</span>
          </div>
          <div className="w-full bg-[#2B3A55] rounded-full h-3">
            <div
              className="bg-gradient-to-r from-[#7B61FF] to-[#5ED3F3] h-3 rounded-full transition-all duration-300 shadow-[0_0_10px_rgba(123,97,255,0.3)]"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>

        {/* Steps */}
        <div className="space-y-4">
          {steps.map((step, index) => {
            const Icon = step.icon;
            const isActive = index === currentStep;
            const isCompleted = index < currentStep;

            return (
              <div
                key={index}
                className={`flex items-center space-x-4 p-4 rounded-xl transition-all duration-300 backdrop-blur-xl ${
                  isActive
                    ? 'bg-[#7B61FF]/10 border border-[#7B61FF]/30 shadow-[0_0_15px_rgba(123,97,255,0.2)]'
                    : isCompleted
                    ? 'bg-[#3BE8B0]/10 border border-[#3BE8B0]/30'
                    : 'bg-[#2B3A55]/30 border border-[#2B3A55]'
                }`}
              >
                <div className={`w-12 h-12 rounded-xl flex items-center justify-center shadow-lg ${
                  isActive
                    ? 'bg-gradient-to-r from-[#7B61FF] to-[#5ED3F3] animate-pulse'
                    : isCompleted
                    ? 'bg-gradient-to-r from-[#3BE8B0] to-[#2BC8A0]'
                    : 'bg-[#2B3A55]'
                }`}>
                  <Icon className="w-6 h-6 text-white" />
                </div>
                <div className="flex-1">
                  <h3 className={`font-semibold ${
                    isActive ? 'text-white' : isCompleted ? 'text-[#3BE8B0]' : 'text-[#BFC9D9]'
                  }`}>
                    {step.title}
                  </h3>
                  <p className={`text-sm ${
                    isActive ? 'text-[#BFC9D9]' : isCompleted ? 'text-[#3BE8B0]/80' : 'text-[#BFC9D9]/70'
                  }`}>
                    {step.description}
                  </p>
                </div>
                {isCompleted && (
                  <CheckCircle className="w-6 h-6 text-[#3BE8B0]" />
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
      {/* Subscribe Modal */}
      {showSubscribeModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-60">
          <div className="bg-white rounded-xl shadow-lg p-8 max-w-md w-full text-center">
            <h2 className="text-2xl font-bold mb-4 text-purple-800">Out of Free PDFs</h2>
            <p className="mb-6 text-gray-700">{error || 'You have used all your free PDFs. Please purchase a plan to continue using SnapReads.'}</p>
            <button
              className="px-6 py-3 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-lg font-semibold text-lg hover:from-purple-700 hover:to-pink-700 transition-colors"
              onClick={() => window.location.href = '/pricing'}
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
      )}
    </>
  );
};