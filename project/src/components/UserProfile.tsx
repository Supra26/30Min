import React, { useState } from 'react';
import { useAuthStore } from '../stores/authStore';
import { useSettingsStore } from '../stores/settingsStore';
import { 
  LogOut, 
  User, 
  History, 
  Settings, 
  Moon, 
  Sun, 
  Monitor, 
  BookOpen, 
  Download, 
  Bell, 
  Type, 
  ChevronDown,
  ChevronUp,
  RotateCcw,
  X
} from 'lucide-react';

interface UserProfileProps {
  onShowHistory: () => void;
}

const UserProfile: React.FC<UserProfileProps> = ({ onShowHistory }) => {
  const { user, logout } = useAuthStore();
  const { 
    settings, 
    toggleDarkMode, 
    setReadingSpeed, 
    setAutoDownload, 
    setShowNotifications, 
    setFontSize, 
    setTheme, 
    resetSettings 
  } = useSettingsStore();
  
  const [showProfile, setShowProfile] = useState(false);
  const [activeTab, setActiveTab] = useState<'profile' | 'settings'>('profile');

  if (!user) return null;

  const handleLogout = () => {
    logout();
    setShowProfile(false);
  };

  const getThemeIcon = () => {
    switch (settings.theme) {
      case 'dark':
        return <Moon className="w-4 h-4" />;
      case 'light':
        return <Sun className="w-4 h-4" />;
      default:
        return <Monitor className="w-4 h-4" />;
    }
  };

  const getFontSizeLabel = () => {
    switch (settings.fontSize) {
      case 'small':
        return 'Small';
      case 'large':
        return 'Large';
      default:
        return 'Medium';
    }
  };

  return (
    <div className="relative">
      {/* Profile Button */}
      <button
        onClick={() => setShowProfile(!showProfile)}
        className="flex items-center space-x-3 px-3 py-2 text-sm font-medium text-[#BFC9D9] bg-[#0B0F1A]/60 backdrop-blur-xl border border-[#2B3A55] rounded-lg hover:bg-[#0B0F1A]/80 hover:border-[#7B61FF]/50 focus:outline-none focus:ring-2 focus:ring-[#7B61FF]/50 transition-all duration-200"
      >
        {user.picture ? (
          <img
            src={user.picture}
            alt={user.name}
            className="w-8 h-8 rounded-full"
          />
        ) : (
          <div className="w-8 h-8 bg-gradient-to-br from-[#7B61FF] to-[#5ED3F3] rounded-full flex items-center justify-center shadow-lg">
            <User className="w-4 h-4 text-white" />
          </div>
        )}
        <div className="hidden md:block text-left">
          <div className="text-sm font-medium text-white">{user.name}</div>
          <div className="text-xs text-[#BFC9D9]/70">{user.email}</div>
        </div>
        {showProfile ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
      </button>

      {/* Profile Dropdown */}
      {showProfile && (
        <div className="absolute right-0 mt-2 w-80 bg-[#0B0F1A]/95 backdrop-blur-xl rounded-xl shadow-2xl border border-[#2B3A55] z-50">
          {/* Header */}
          <div className="p-4 border-b border-[#2B3A55]">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-white">Profile & Settings</h3>
              <button
                onClick={() => setShowProfile(false)}
                className="text-[#BFC9D9] hover:text-white transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
          </div>

          {/* Tabs */}
          <div className="flex border-b border-[#2B3A55]">
            <button
              onClick={() => setActiveTab('profile')}
              className={`flex-1 px-4 py-3 text-sm font-medium transition-colors ${
                activeTab === 'profile'
                  ? 'text-[#7B61FF] border-b-2 border-[#7B61FF]'
                  : 'text-[#BFC9D9] hover:text-white'
              }`}
            >
              Profile
            </button>
            <button
              onClick={() => setActiveTab('settings')}
              className={`flex-1 px-4 py-3 text-sm font-medium transition-colors ${
                activeTab === 'settings'
                  ? 'text-[#7B61FF] border-b-2 border-[#7B61FF]'
                  : 'text-[#BFC9D9] hover:text-white'
              }`}
            >
              Settings
            </button>
          </div>

          {/* Content */}
          <div className="p-4 max-h-96 overflow-y-auto">
            {activeTab === 'profile' && (
              <div className="space-y-4">
                {/* User Info */}
                <div className="flex items-center space-x-3">
                  {user.picture ? (
                    <img
                      src={user.picture}
                      alt={user.name}
                      className="w-16 h-16 rounded-full"
                    />
                  ) : (
                    <div className="w-16 h-16 bg-gradient-to-br from-[#7B61FF] to-[#5ED3F3] rounded-full flex items-center justify-center shadow-lg">
                      <User className="w-8 h-8 text-white" />
                    </div>
                  )}
                  <div>
                    <h4 className="text-lg font-semibold text-white">{user.name}</h4>
                    <p className="text-sm text-[#BFC9D9]">{user.email}</p>
                    <p className="text-xs text-[#BFC9D9]/60">Member since {new Date(user.created_at).toLocaleDateString()}</p>
                  </div>
                </div>

                {/* Quick Actions */}
                <div className="space-y-2">
                  <button
                    onClick={onShowHistory}
                    className="w-full flex items-center space-x-3 px-3 py-2 text-sm text-[#BFC9D9] bg-[#2B3A55]/50 rounded-lg hover:bg-[#2B3A55] hover:text-white transition-colors"
                  >
                    <History className="w-4 h-4" />
                    <span>View History</span>
                  </button>
                </div>
              </div>
            )}

            {activeTab === 'settings' && (
              <div className="space-y-6">
                {/* Theme Settings */}
                <div>
                  <h4 className="text-sm font-medium text-white mb-3">Appearance</h4>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        {getThemeIcon()}
                        <span className="text-sm text-[#BFC9D9]">Theme</span>
                      </div>
                      <select
                        value={settings.theme}
                        onChange={(e) => setTheme(e.target.value as 'light' | 'dark' | 'auto')}
                        className="text-sm border border-[#2B3A55] rounded-md px-2 py-1 bg-[#0B0F1A] text-white focus:border-[#7B61FF] focus:outline-none"
                      >
                        <option value="auto">Auto</option>
                        <option value="light">Light</option>
                        <option value="dark">Dark</option>
                      </select>
                    </div>

                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <Type className="w-4 h-4" />
                        <span className="text-sm text-[#BFC9D9]">Font Size</span>
                      </div>
                      <select
                        value={settings.fontSize}
                        onChange={(e) => setFontSize(e.target.value as 'small' | 'medium' | 'large')}
                        className="text-sm border border-[#2B3A55] rounded-md px-2 py-1 bg-[#0B0F1A] text-white focus:border-[#7B61FF] focus:outline-none"
                      >
                        <option value="small">Small</option>
                        <option value="medium">Medium</option>
                        <option value="large">Large</option>
                      </select>
                    </div>
                  </div>
                </div>

                {/* Reading Preferences */}
                <div>
                  <h4 className="text-sm font-medium text-white mb-3">Reading Preferences</h4>
                  <div className="space-y-3">
                    <div>
                      <label className="text-sm text-[#BFC9D9]">Reading Speed (words per minute)</label>
                      <div className="flex items-center space-x-2 mt-1">
                        <input
                          type="range"
                          min="150"
                          max="400"
                          step="25"
                          value={settings.readingSpeed}
                          onChange={(e) => setReadingSpeed(Number(e.target.value))}
                          className="flex-1 accent-[#7B61FF]"
                        />
                        <span className="text-sm text-[#BFC9D9] w-12">{settings.readingSpeed}</span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Behavior Settings */}
                <div>
                  <h4 className="text-sm font-medium text-white mb-3">Behavior</h4>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <Download className="w-4 h-4" />
                        <span className="text-sm text-[#BFC9D9]">Auto-download PDFs</span>
                      </div>
                      <button
                        onClick={() => setAutoDownload(!settings.autoDownload)}
                        className={`w-10 h-6 rounded-full transition-colors ${
                          settings.autoDownload ? 'bg-gradient-to-r from-[#7B61FF] to-[#5ED3F3]' : 'bg-[#2B3A55]'
                        }`}
                      >
                        <div className={`w-4 h-4 bg-white rounded-full transition-transform ${
                          settings.autoDownload ? 'translate-x-4' : 'translate-x-0'
                        }`} />
                      </button>
                    </div>

                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <Bell className="w-4 h-4" />
                        <span className="text-sm text-[#BFC9D9]">Show notifications</span>
                      </div>
                      <button
                        onClick={() => setShowNotifications(!settings.showNotifications)}
                        className={`w-10 h-6 rounded-full transition-colors ${
                          settings.showNotifications ? 'bg-gradient-to-r from-[#7B61FF] to-[#5ED3F3]' : 'bg-[#2B3A55]'
                        }`}
                      >
                        <div className={`w-4 h-4 bg-white rounded-full transition-transform ${
                          settings.showNotifications ? 'translate-x-4' : 'translate-x-0'
                        }`} />
                      </button>
                    </div>
                  </div>
                </div>

                {/* Reset Settings */}
                <div className="pt-4 border-t border-[#2B3A55]">
                  <button
                    onClick={resetSettings}
                    className="flex items-center space-x-2 text-sm text-[#BFC9D9] hover:text-white transition-colors"
                  >
                    <RotateCcw className="w-4 h-4" />
                    <span>Reset to defaults</span>
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="p-4 border-t border-[#2B3A55]">
            <button
              onClick={handleLogout}
              className="w-full flex items-center justify-center space-x-2 px-4 py-2 text-sm font-medium text-red-400 bg-red-900/20 rounded-lg hover:bg-red-900/30 transition-colors"
            >
              <LogOut className="w-4 h-4" />
              <span>Sign Out</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default UserProfile; 