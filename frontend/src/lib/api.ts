import type { User } from '../types';

const API_BASE = '/api';

let authToken: string | null = null;
let currentUser: User | null = null;

export function setAuthToken(token: string | null) {
  authToken = token;
  if (token) {
    localStorage.setItem('bi_token', token);
  } else {
    localStorage.removeItem('bi_token');
  }
}

export function getAuthToken(): string | null {
  if (!authToken) {
    authToken = localStorage.getItem('bi_token');
  }
  return authToken;
}

export function setCurrentUser(user: User | null) {
  currentUser = user;
  if (user) {
    localStorage.setItem('bi_user', JSON.stringify(user));
  } else {
    localStorage.removeItem('bi_user');
  }
}

export function getCurrentUser(): User | null {
  if (!currentUser) {
    const stored = localStorage.getItem('bi_user');
    if (stored) currentUser = JSON.parse(stored);
  }
  return currentUser;
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getAuthToken();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string> || {}),
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });
  if (res.status === 401) {
    setAuthToken(null);
    setCurrentUser(null);
    window.location.href = '/login';
    throw new Error('Unauthorized');
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Request failed' }));
    throw new Error(err.detail || 'Request failed');
  }
  return res.json();
}

export const api = {
  login: (username: string, password: string) =>
    request<{ access_token: string; user: User }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    }),

  getProfile: () => request<User>('/user/profile'),

  getKPIs: (persona: string = 'CEO') =>
    request<{ kpi_cards: Array<import('../types').KPICard>; persona: string }>(`/kpis?persona=${persona}`),

  getKPIDetail: (id: string, persona: string = 'CEO') =>
    request<import('../types').Insight>(`/kpis/${id}?persona=${persona}`),

  getKPITrend: (id: string) =>
    request<{ kpi_name: string; data_points: Array<{ date: string; value: number }> }>(`/kpis/${id}/trend`),

  getKPIDrivers: (id: string, persona: string = 'CEO') =>
    request<{ kpi_name: string; drivers: import('../types').Driver[] }>(`/kpis/${id}/drivers?persona=${persona}`),

  getInsights: (persona: string = 'CEO') =>
    request<{ insights: import('../types').Insight[]; total: number }>(`/insights?persona=${persona}`),

  getInsightDetail: (id: string) =>
    request<import('../types').Insight>(`/insights/${id}`),

  getRecommendations: (persona: string = 'CEO') =>
    request<{ recommendations: import('../types').Recommendation[]; total: number }>(`/recommendations?persona=${persona}`),

  getDataSources: () =>
    request<{ data_sources: import('../types').DataSourceInfo[] }>('/data-sources'),

  getLineage: (kpi?: string) =>
    request<import('../types').Lineage>(`/lineage${kpi ? `?kpi_name=${kpi}` : ''}`),

  submitFeedback: (data: { insight_id: number; rating: string; feedback_type?: string; correction?: string }) =>
    request<{ status: string; feedback_id: number }>('/feedback', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  getFeedbackDashboard: () =>
    request<import('../types').FeedbackDashboard>('/feedback/dashboard'),

  sendAssistantMessage: (message: string, persona: string = 'CEO') =>
    request<import('../types').AssistantMessage>('/assistant', {
      method: 'POST',
      body: JSON.stringify({ message, persona }),
    }),

  getTelemetry: () => request<import('../types').TelemetryData>('/telemetry'),

  getScenarios: () => request<{ scenarios: import('../types').Scenario[] }>('/demo/scenarios'),

  switchScenario: (scenario: string) =>
    request<{ scenario: import('../types').Scenario; analysis: import('../types').Insight }>('/demo/scenario', {
      method: 'POST',
      body: JSON.stringify({ scenario }),
    }),

  getAdminUsers: () => request<{ users: User[] }>('/admin/users'),

  uploadFile: async (file: File, tableName?: string) => {
    const formData = new FormData();
    formData.append('file', file);
    if (tableName) formData.append('table_name', tableName);
    const token = getAuthToken();
    const res = await fetch(`${API_BASE}/upload/file`, {
      method: 'POST',
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: formData,
    });
    if (!res.ok) { const err = await res.json().catch(() => ({})); throw new Error(err.detail || 'Upload failed'); }
    return res.json();
  },

  previewFile: async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    const token = getAuthToken();
    const res = await fetch(`${API_BASE}/upload/preview`, {
      method: 'POST',
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: formData,
    });
    if (!res.ok) { const err = await res.json().catch(() => ({})); throw new Error(err.detail || 'Preview failed'); }
    return res.json();
  },

  getUploadedTables: () => request<{ tables: import('../types').UploadedTable[] }>('/upload/tables'),

  getTableData: (tableName: string, limit?: number, offset?: number) =>
    request<{ table_name: string; total_rows: number; columns: string[]; rows: Array<Record<string, unknown>> }>(
      `/upload/tables/${tableName}?limit=${limit || 50}&offset=${offset || 0}`
    ),

  deleteTable: (tableName: string) =>
    request<{ success: boolean }>(`/upload/tables/${tableName}`, { method: 'DELETE' }),

  autoDetectMapping: async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    const token = getAuthToken();
    const res = await fetch(`${API_BASE}/upload/auto-detect`, {
      method: 'POST',
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: formData,
    });
    if (!res.ok) { const err = await res.json().catch(() => ({})); throw new Error(err.detail || 'Auto-detect failed'); }
    return res.json();
  },

  applyMapping: (data: { table_name: string; mapped_type: string; column_mapping: Record<string, string> }) =>
    request<{ success: boolean }>('/upload/apply-mapping', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  getMappings: () => request<{ mappings: import('../types').DataMapping[] }>('/upload/mappings'),

  deleteMapping: (tableName: string) =>
    request<{ success: boolean }>(`/upload/mappings/${tableName}`, { method: 'DELETE' }),
};
