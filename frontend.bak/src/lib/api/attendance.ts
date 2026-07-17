/** API client for Attendance network configuration. */

const BASE = "/api/attendance/settings/network";

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail || `Request failed: ${res.status}`);
  }
  return res.json();
}

export interface NetworkAllowlistResponse {
  networks: string[];
  updated_at: string | null;
}

export interface NetworkAllowlistUpdate {
  networks: string[];
}

export async function getNetworkAllowlist(): Promise<NetworkAllowlistResponse> {
  const res = await fetch(BASE);
  return handleResponse<NetworkAllowlistResponse>(res);
}

export async function updateNetworkAllowlist(
  networks: string[]
): Promise<NetworkAllowlistResponse> {
  const res = await fetch(BASE, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ networks }),
  });
  return handleResponse<NetworkAllowlistResponse>(res);
}

export async function addNetworkToAllowlist(
  networks: string[]
): Promise<NetworkAllowlistResponse> {
  const res = await fetch(`${BASE}/add`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ networks }),
  });
  return handleResponse<NetworkAllowlistResponse>(res);
}

export async function removeNetworkFromAllowlist(
  cidr: string
): Promise<NetworkAllowlistResponse> {
  const params = new URLSearchParams({ cidr });
  const res = await fetch(`${BASE}?${params.toString()}`, {
    method: "DELETE",
  });
  return handleResponse<NetworkAllowlistResponse>(res);
}
