import React, { useEffect } from 'react';
import { useAuthStore } from '../stores/authStore';
import { authAPI } from '../services/api';

declare global {
  interface Window {
    google: any;
  }
}

interface GoogleLoginProps {
  onSuccess?: () => void;
}

const GoogleLogin: React.FC<GoogleLoginProps> = ({ onSuccess }) => {
  const { login, setLoading, setError, isLoading } = useAuthStore();

  useEffect(() => {
    console.log('GoogleLogin: Component mounted, loading Google Identity Services...');
    
    // Load Google Identity Services
    const script = document.createElement('script');
    script.src = 'https://accounts.google.com/gsi/client';
    script.async = true;
    script.defer = true;
    document.head.appendChild(script);

    script.onload = () => {
      console.log('GoogleLogin: Google Identity Services loaded successfully');
      
      try {
        window.google.accounts.id.initialize({
          client_id: '109935582557-kjer5mjb7u3qrscjdls5h4iklfjlj592.apps.googleusercontent.com',
          callback: handleCredentialResponse,
          auto_select: false,
          cancel_on_tap_outside: true,
        });

        console.log('GoogleLogin: Google Identity Services initialized');

        const buttonElement = document.getElementById('google-login-button');
        if (buttonElement) {
          window.google.accounts.id.renderButton(
            buttonElement,
            {
              theme: 'outline',
              size: 'large',
              type: 'standard',
              text: 'signin_with',
              shape: 'rectangular',
              logo_alignment: 'left',
            }
          );
          console.log('GoogleLogin: Google button rendered successfully');
        } else {
          console.error('GoogleLogin: Button element not found');
          setError('Failed to render login button');
        }
      } catch (error) {
        console.error('GoogleLogin: Error initializing Google Identity Services:', error);
        setError('Failed to initialize Google login');
      }
    };

    script.onerror = (error) => {
      console.error('GoogleLogin: Failed to load Google Identity Services script:', error);
      setError('Failed to load Google login service');
    };

    return () => {
      console.log('GoogleLogin: Component unmounting, cleaning up...');
      try {
        if (script.parentNode) {
          document.head.removeChild(script);
        }
      } catch (error) {
        console.warn('GoogleLogin: Error removing script:', error);
      }
    };
  }, []);

  const handleCredentialResponse = async (response: any) => {
    console.log('GoogleLogin: Received credential response');
    try {
      setLoading(true);
      setError(null);
      
      console.log('GoogleLogin: Calling backend auth API...');
      const result = await authAPI.googleAuth(response.credential);
      console.log('GoogleLogin: Backend auth successful:', result);
      
      login(result.user, result.access_token);
      console.log('GoogleLogin: User logged in successfully');
      
      // Call onSuccess callback if provided
      if (onSuccess) {
        console.log('GoogleLogin: Calling onSuccess callback');
        onSuccess();
      }
      
    } catch (error: any) {
      console.error('GoogleLogin: Google auth error:', error);
      setError(error.response?.data?.detail || 'Authentication failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col items-center space-y-4">
      <div id="google-login-button"></div>
      {isLoading && (
        <div className="text-sm text-gray-600">Signing in...</div>
      )}
      {!isLoading && (
        <div className="text-xs text-gray-500">Click the button above to sign in with Google</div>
      )}
      
      {/* Fallback button for debugging */}
      <button
        onClick={() => {
          console.log('GoogleLogin: Fallback button clicked');
          alert('Google OAuth button clicked - this is a fallback for debugging');
        }}
        className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
        style={{ display: 'none' }} // Hidden by default, show if needed
      >
        Debug: Test Login
      </button>
    </div>
  );
};

export default GoogleLogin; 