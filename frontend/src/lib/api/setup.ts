/** API client for the setup wizard. */

const BASE = process.env.NEXT_PUBLIC_API_URL || '';

async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}/api/setup${path}`, {
    credentials: 'include',
    headers: { 'Content-Type': 'application/json', ...init?.headers },
    ...init,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(body.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

export interface SetupStatus {
  setup_complete: boolean;
  admin_exists: boolean;
  org_configured: boolean;
  ai_provider_configured: boolean;
}

export function getStatus(): Promise<SetupStatus> {
  return api<SetupStatus>('/status');
}

export function createAdmin(data: { email: string; password: string; name: string }) {
  return api<{ id: string; email: string; role: string }>('/admin', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export function configureOrg(data: { name: string; tax_code: string; timezone: string }) {
  return api<{ status: string }>('/organization', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export function configureAi(data: { provider: string; api_key?: string | null }) {
  return api<{ status: string }>('/ai-provider', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export function completeSetup(): Promise<{ status: string }> {
  return api<{ status: string }>('/complete', { method: 'POST' });
}
