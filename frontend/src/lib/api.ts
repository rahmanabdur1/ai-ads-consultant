import axios, {
  InternalAxiosRequestConfig,
  AxiosError,
  AxiosResponse,
} from 'axios';

// ==============================
// Base API Instance
// ==============================
const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  withCredentials: true, // for cookies (optional)
});

// ==============================
// Token Helpers
// ==============================
const getAccessToken = (): string | null => {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('access_token');
};

const getRefreshToken = (): string | null => {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('refresh_token');
};

const setTokens = (access: string, refresh?: string) => {
  if (typeof window === 'undefined') return;

  localStorage.setItem('access_token', access);
  if (refresh) localStorage.setItem('refresh_token', refresh);
};

const clearTokens = () => {
  if (typeof window === 'undefined') return;

  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
};

// ==============================
// Request Interceptor
// ==============================
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = getAccessToken();

    if (token) {
      config.headers.set('Authorization', `Bearer ${token}`);
    }

    return config;
  },
  (error) => Promise.reject(error)
);

// ==============================
// Refresh Token Logic
// ==============================
let isRefreshing = false;
let failedQueue: Array<{
  resolve: (value?: unknown) => void;
  reject: (error: unknown) => void;
}> = [];

const processQueue = (error: unknown, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (error) prom.reject(error);
    else prom.resolve(token);
  });

  failedQueue = [];
};

// ==============================
// Response Interceptor
// ==============================
api.interceptors.response.use(
  (response: AxiosResponse) => response,
  async (error: AxiosError) => {
    const originalRequest: any = error.config;

    // If 401 & not already retried
    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        // Queue requests while refreshing
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then((token) => {
            originalRequest.headers['Authorization'] = `Bearer ${token}`;
            return api(originalRequest);
          })
          .catch((err) => Promise.reject(err));
      }

      originalRequest._retry = true;
      isRefreshing = true;

      const refreshToken = getRefreshToken();

      if (!refreshToken) {
        clearTokens();
        window.location.href = '/login';
        return Promise.reject(error);
      }

      try {
        const res = await axios.post(
          `${process.env.NEXT_PUBLIC_API_URL}/auth/refresh`,
          {
            refresh_token: refreshToken,
          }
        );

        const newAccessToken = res.data.access_token;

        setTokens(newAccessToken);

        api.defaults.headers.common[
          'Authorization'
        ] = `Bearer ${newAccessToken}`;

        processQueue(null, newAccessToken);

        originalRequest.headers[
          'Authorization'
        ] = `Bearer ${newAccessToken}`;

        return api(originalRequest);
      } catch (err) {
        processQueue(err, null);
        clearTokens();
        window.location.href = '/login';
        return Promise.reject(err);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);

// ==============================
// TYPES
// ==============================

export interface AuthPayload {
  email: string;
  password: string;
  name?: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  user: {
    id: string;
    email: string;
  };
}

export interface AgentPayload {
  message: string;
  workspace_id?: string;
  session_id?: string; 
  budget?:number;
}

export interface CampaignPayload {
  name: string;
  workspace_id: string;
  budget?: number;
}

// ==============================
// API MODULES
// ==============================

export const authAPI = {
  register: (data: AuthPayload) =>
    api.post('/auth/register', data),

  login: async (data: AuthPayload) => {
    const res = await api.post<LoginResponse>(
      '/auth/login',
      data
    );

    // Save tokens
    setTokens(res.data.access_token, res.data.refresh_token);

    return res;
  },

  logout: () => {
    clearTokens();
    window.location.href = '/login';
  },
};

export const agentAPI = {
  run: (data: AgentPayload) =>
    api.post('/agent/run', data),

  chat: (data: AgentPayload) =>
    api.post('/agent/chat', data),
};

export const campaignAPI = {
  list: (workspace_id: string) =>
    api.get('/campaign/', {
      params: { workspace_id },
    }),

  create: (data: CampaignPayload) =>
    api.post('/campaign/', data),

  delete: (id: string) =>
    api.delete(`/campaign/${id}`),
};

export default api;