const API_BASE = '/api';

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const token = localStorage.getItem('token');
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options?.headers as Record<string, string> || {}),
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });

  if (res.status === 403) {
    throw new Error('ACCESS_RESTRICTED');
  }

  if (!res.ok) {
    throw new Error(`API error: ${res.status}`);
  }

  return res.json();
}

export const api = {
  auth: {
    login: (email: string, password: string) =>
      request<{ access_token: string; user: any }>('/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email, password }),
      }),
    me: () => request<any>('/auth/me'),
    users: () => request<any[]>('/auth/users'),
  },

  dashboard: {
    get: (persona: string = 'CEO') => request<any>(`/dashboard?persona=${encodeURIComponent(persona)}`),
  },

  kpis: {
    list: (persona: string = 'CEO') => request<any[]>(`/kpis?persona=${encodeURIComponent(persona)}`),
    get: (name: string) => request<any>(`/kpis/${encodeURIComponent(name)}`),
    trend: (name: string, days: number = 30) => request<any>(`/kpis/${encodeURIComponent(name)}/trend?days=${days}`),
    definitions: () => request<any[]>('/kpis/definitions'),
  },

  insights: {
    list: (persona: string = 'CEO') => request<any[]>(`/insights?persona=${encodeURIComponent(persona)}`),
    get: (id: number) => request<any>(`/insights/${id}`),
    analyze: (kpiName: string, persona: string = 'CEO') =>
      request<any>(`/insights/analyze/${encodeURIComponent(kpiName)}?persona=${encodeURIComponent(persona)}`, {
        method: 'POST',
      }),
  },

  drivers: {
    list: (anomalyId?: number) =>
      request<any[]>(`/drivers${anomalyId ? `?anomaly_id=${anomalyId}` : ''}`),
  },

  recommendations: {
    list: (persona?: string) =>
      request<any[]>(`/recommendations${persona ? `?persona=${encodeURIComponent(persona)}` : ''}`),
  },

  dataSources: {
    list: () => request<any[]>('/data-sources'),
  },

  feedback: {
    list: () => request<any[]>('/feedback'),
    dashboard: () => request<any>('/feedback/dashboard'),
    create: (data: { insight_id: number; feedback_type: string; comment?: string }) =>
      request<any>('/feedback', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
  },

  assistant: {
    send: (message: string, persona: string = 'CEO') =>
      request<any>('/assistant', {
        method: 'POST',
        body: JSON.stringify({ message, persona }),
      }),
  },

  telemetry: {
    get: () => request<any>('/telemetry'),
  },

  reports: {
    generate: (kpiName: string, persona: string = 'CEO') =>
      request<any>('/reports/generate', {
        method: 'POST',
        body: JSON.stringify({ kpi_name: kpiName, persona, include_evidence: true, include_recommendations: true }),
      }),
  },

  lineage: {
    get: () => request<any>('/lineage'),
  },
};
