import axios, { AxiosError, AxiosInstance } from "axios";
import type {
  TokenResponse,
  User,
  Startup,
  StartupListItem,
  AnalysisJob,
  Memo,
  MemoListItem,
  MemoSection,
} from "@/types";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const API_PREFIX = "/api/v1";

function createClient(): AxiosInstance {
  const client = axios.create({
    baseURL: `${BASE_URL}${API_PREFIX}`,
    timeout: 30000,
    headers: { "Content-Type": "application/json" },
  });

  // Attach access token from localStorage
  client.interceptors.request.use((config) => {
    if (typeof window !== "undefined") {
      const token = localStorage.getItem("access_token");
      if (token) config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  });

  // Auto-refresh on 401
  client.interceptors.response.use(
    (res) => res,
    async (error: AxiosError) => {
      const original = error.config as (typeof error.config) & { _retry?: boolean };
      if (error.response?.status === 401 && !original?._retry) {
        original._retry = true;
        try {
          const refresh = localStorage.getItem("refresh_token");
          if (refresh) {
            const { data } = await axios.post<TokenResponse>(
              `${BASE_URL}${API_PREFIX}/auth/refresh`,
              { refresh_token: refresh }
            );
            localStorage.setItem("access_token", data.access_token);
            localStorage.setItem("refresh_token", data.refresh_token);
            if (original.headers) {
              original.headers.Authorization = `Bearer ${data.access_token}`;
            }
            return client(original);
          }
        } catch {
          localStorage.removeItem("access_token");
          localStorage.removeItem("refresh_token");
          window.location.href = "/login";
        }
      }
      return Promise.reject(error);
    }
  );

  return client;
}

export const api = createClient();

// ── Auth ───────────────────────────────────────────────────
export const authApi = {
  register: (email: string, password: string, full_name?: string) =>
    api.post<TokenResponse>("/auth/register", { email, password, full_name }),

  login: (email: string, password: string) =>
    api.post<TokenResponse>("/auth/login", { email, password }),

  me: () => api.get<User>("/auth/me"),
};

// ── Upload ─────────────────────────────────────────────────
export const uploadApi = {
  uploadDeck: (file: File, website_url?: string) => {
    const form = new FormData();
    form.append("file", file);
    if (website_url) form.append("website_url", website_url);
    return api.post<Startup>("/upload/deck", form, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },

  addWebsite: (startupId: string, website_url: string) => {
    const form = new FormData();
    form.append("website_url", website_url);
    return api.post(`/upload/${startupId}/website`, form, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },
};

// ── Startups ───────────────────────────────────────────────
export const startupApi = {
  list: (skip = 0, limit = 20) =>
    api.get<StartupListItem[]>("/startups/", { params: { skip, limit } }),

  get: (id: string) => api.get<Startup>(`/startups/${id}`),

  delete: (id: string) => api.delete(`/startups/${id}`),
};

// ── Analysis ───────────────────────────────────────────────
export const analysisApi = {
  start: (startupId: string) =>
    api.post<AnalysisJob>(`/analysis/start/${startupId}`),

  status: (jobId: string) =>
    api.get<AnalysisJob>(`/analysis/status/${jobId}`),

  streamUrl: (jobId: string) =>
    `${BASE_URL}${API_PREFIX}/analysis/stream/${jobId}`,
};

// ── Memos ──────────────────────────────────────────────────
export const memoApi = {
  list: (skip = 0, limit = 20) =>
    api.get<MemoListItem[]>("/memos/", { params: { skip, limit } }),

  get: (id: string) => api.get<Memo>(`/memos/${id}`),

  updateSection: (memoId: string, sectionKey: string, content: string) =>
    api.patch(`/memos/${memoId}/sections/${sectionKey}`, { content }),

  regenerateSection: (memoId: string, sectionKey: string) =>
    api.post(`/memos/${memoId}/sections/${sectionKey}/regenerate`),

  delete: (id: string) => api.delete(`/memos/${id}`),
};

// ── Export ─────────────────────────────────────────────────
export const exportApi = {
  pdfUrl: (memoId: string) =>
    `${BASE_URL}${API_PREFIX}/export/memo/${memoId}/pdf`,
};
