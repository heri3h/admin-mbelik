import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || '';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor for JWT auth token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
}, (error) => Promise.reject(error));

// Interceptor for handling 401 response
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      localStorage.removeItem('token');
      if (window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export const authService = {
  login: async (username, password) => {
    const res = await api.post('/api/auth/login', { username, password });
    if (res.data.access_token) {
      localStorage.setItem('token', res.data.access_token);
    }
    return res.data;
  },
  logout: () => {
    localStorage.removeItem('token');
    window.location.href = '/login';
  },
  getMe: async () => {
    const res = await api.get('/api/auth/me');
    return res.data;
  },
  changePassword: async (currentPassword, newPassword) => {
    const res = await api.post('/api/auth/change-password', {
      current_password: currentPassword,
      new_password: newPassword
    });
    return res.data;
  },
  isAuthenticated: () => {
    return !!localStorage.getItem('token');
  }
};

export const dashboardService = {
  getSummary: async (startDate, endDate) => {
    const params = { _t: Date.now() };
    if (startDate) params.start_date = startDate;
    if (endDate) params.end_date = endDate;
    const res = await api.get('/api/dashboard/summary', { params });
    return res.data;
  },
  getTrend: async (startDate, endDate) => {
    const params = { _t: Date.now() };
    if (startDate) params.start_date = startDate;
    if (endDate) params.end_date = endDate;
    const res = await api.get('/api/dashboard/trend', { params });
    return res.data;
  },
  getAccounts: async (startDate, endDate) => {
    const params = { _t: Date.now() };
    if (startDate) params.start_date = startDate;
    if (endDate) params.end_date = endDate;
    const res = await api.get('/api/dashboard/accounts', { params });
    return res.data;
  },
  getSites: async (startDate, endDate) => {
    const params = { _t: Date.now() };
    if (startDate) params.start_date = startDate;
    if (endDate) params.end_date = endDate;
    const res = await api.get('/api/dashboard/sites', { params });
    return res.data;
  },
  getSiteCountries: async (domain, startDate, endDate) => {
    const params = { _t: Date.now() };
    if (startDate) params.start_date = startDate;
    if (endDate) params.end_date = endDate;
    const res = await api.get(`/api/dashboard/sites/${encodeURIComponent(domain)}/countries`, { params });
    return res.data;
  },
  getSiteCountryPlacements: async (domain, country, startDate, endDate) => {
    const params = { _t: Date.now() };
    if (startDate) params.start_date = startDate;
    if (endDate) params.end_date = endDate;
    const res = await api.get(`/api/dashboard/sites/${encodeURIComponent(domain)}/countries/${encodeURIComponent(country)}/placements`, { params });
    return res.data;
  },
  getPlacements: async (startDate, endDate) => {
    const params = { _t: Date.now() };
    if (startDate) params.start_date = startDate;
    if (endDate) params.end_date = endDate;
    const res = await api.get('/api/dashboard/placements', { params });
    return res.data;
  },
  getDomains: async (startDate, endDate) => {
    const params = { _t: Date.now() };
    if (startDate) params.start_date = startDate;
    if (endDate) params.end_date = endDate;
    const res = await api.get('/api/dashboard/domains', { params });
    return res.data;
  },
  triggerSync: async (startDate, endDate) => {
    const params = {};
    if (startDate) params.start_date = startDate;
    if (endDate) params.end_date = endDate;
    const res = await api.post('/api/sync/trigger', null, { params });
    return res.data;
  },
  clearCache: async () => {
    const res = await api.post('/api/sync/clear-cache');
    return res.data;
  },
  getSettingsStatus: async () => {
    const res = await api.get('/api/settings/status');
    return res.data;
  },
  getGoogleAdsAccounts: async () => {
    const res = await api.get('/api/settings/google-ads-accounts');
    return res.data;
  },
  addGoogleAdsAccount: async (data) => {
    const res = await api.post('/api/settings/google-ads-accounts', data);
    return res.data;
  },
  updateGoogleAdsAccount: async (id, data) => {
    const res = await api.put(`/api/settings/google-ads-accounts/${id}`, data);
    return res.data;
  },
  deleteGoogleAdsAccount: async (id) => {
    const res = await api.delete(`/api/settings/google-ads-accounts/${id}`);
    return res.data;
  },
  getAvailableDomains: async () => {
    const res = await api.get('/api/settings/available-domains');
    return res.data;
  },
  getExportTargets: async () => {
    const res = await api.get('/api/settings/export-targets');
    return res.data;
  },
  addExportTarget: async (data) => {
    const res = await api.post('/api/settings/export-targets', data);
    return res.data;
  },
  updateExportTarget: async (id, data) => {
    const res = await api.put(`/api/settings/export-targets/${id}`, data);
    return res.data;
  },
  deleteExportTarget: async (id) => {
    const res = await api.delete(`/api/settings/export-targets/${id}`);
    return res.data;
  },
  testExportTarget: async (id) => {
    const res = await api.post(`/api/settings/export-targets/${id}/test`);
    return res.data;
  }
};

export default api;


