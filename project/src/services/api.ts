import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    try {
      const authStorage = localStorage.getItem('auth-storage');
      console.log('Raw auth storage:', authStorage); // Debug log
      
      if (authStorage) {
        const authData = JSON.parse(authStorage);
        console.log('Parsed auth storage data:', authData); // Debug log
        
        // Zustand stores data in state property
        const token = authData.state?.token;
        console.log('Extracted token:', token ? token.substring(0, 20) + '...' : 'No token'); // Debug log
        
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
          console.log('Token added to request headers'); // Debug log
        } else {
          console.log('No token found in auth storage'); // Debug log
        }
      } else {
        console.log('No auth storage found'); // Debug log
      }
    } catch (error) {
      console.error('Error retrieving auth token:', error);
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Import and use auth store to handle token expiration
      import('../stores/authStore').then(({ useAuthStore }) => {
        const { handleTokenExpiration } = useAuthStore.getState();
        handleTokenExpiration();
      });
    }
    return Promise.reject(error);
  }
);

// Auth API
export const authAPI = {
  googleAuth: async (idToken: string) => {
    const response = await api.post('/auth/google', { id_token: idToken });
    return response.data;
  },
  
  getCurrentUser: async () => {
    const response = await api.get('/auth/me');
    return response.data;
  }
};

// History API
export const historyAPI = {
  getUserHistory: async () => {
    const response = await api.get('/history');
    return response.data;
  },
  
  getHistoryItem: async (historyId: number) => {
    const response = await api.get(`/history/${historyId}`);
    return response.data;
  },
  
  downloadPDF: async (historyId: number) => {
    const response = await api.get(`/download-pdf/${historyId}`, {
      responseType: 'blob'
    });
    return response.data;
  }
};

// PDF Processing API
export const pdfAPI = {
  processPDF: async (file: File, timeLimit: number) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('time_limit', timeLimit.toString());
    
    const response = await api.post('/process-pdf', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  }
};

export default api; 