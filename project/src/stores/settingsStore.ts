import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface UserSettings {
  darkMode: boolean;
  readingSpeed: number; // words per minute
  autoDownload: boolean;
  showNotifications: boolean;
  fontSize: 'small' | 'medium' | 'large';
  theme: 'light' | 'dark' | 'auto';
}

interface SettingsState {
  settings: UserSettings;
  
  // Actions
  toggleDarkMode: () => void;
  setReadingSpeed: (speed: number) => void;
  setAutoDownload: (enabled: boolean) => void;
  setShowNotifications: (enabled: boolean) => void;
  setFontSize: (size: 'small' | 'medium' | 'large') => void;
  setTheme: (theme: 'light' | 'dark' | 'auto') => void;
  resetSettings: () => void;
}

const defaultSettings: UserSettings = {
  darkMode: false,
  readingSpeed: 250,
  autoDownload: false,
  showNotifications: true,
  fontSize: 'medium',
  theme: 'auto'
};

export const useSettingsStore = create<SettingsState>()(
  persist(
    (set, get) => ({
      settings: defaultSettings,

      toggleDarkMode: () => set((state) => ({
        settings: {
          ...state.settings,
          darkMode: !state.settings.darkMode
        }
      })),

      setReadingSpeed: (speed: number) => set((state) => ({
        settings: {
          ...state.settings,
          readingSpeed: speed
        }
      })),

      setAutoDownload: (enabled: boolean) => set((state) => ({
        settings: {
          ...state.settings,
          autoDownload: enabled
        }
      })),

      setShowNotifications: (enabled: boolean) => set((state) => ({
        settings: {
          ...state.settings,
          showNotifications: enabled
        }
      })),

      setFontSize: (size: 'small' | 'medium' | 'large') => set((state) => ({
        settings: {
          ...state.settings,
          fontSize: size
        }
      })),

      setTheme: (theme: 'light' | 'dark' | 'auto') => set((state) => ({
        settings: {
          ...state.settings,
          theme: theme
        }
      })),

      resetSettings: () => set({
        settings: defaultSettings
      })
    }),
    {
      name: 'user-settings',
      partialize: (state) => ({
        settings: state.settings
      })
    }
  )
); 