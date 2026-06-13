/** API client for Payslip endpoints. */

const BASE = "/api/payslips";

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    const detail = error.detail;
    const message =
      typeof detail === "string"
        ? detail
        : detail
          ? JSON.stringify(detail)
          : `Request failed: ${res.status}`;
    throw new Error(message);
  }
  return res.json();
}

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface Payslip {
  id: string;
  employee_id: string;
  pay_period_start: string;
  pay_period_end: string;
  gross_amount: string;
  total_deductions: string;
  net_amount: string;
  currency: string;
  details: Record<string, unknown> | null;
  pdf_url: string | null;
  created_at: string;
  updated_at: string;
}

export interface PayslipListResponse {
  payslips: Payslip[];
}

// ---------------------------------------------------------------------------
// Employee-owned endpoints
// ---------------------------------------------------------------------------

/** Fetch all published payslips for the current employee. */
export async function fetchMyPayslips(): Promise<PayslipListResponse> {
  const res = await fetch(`${BASE}/me`, { credentials: "include" });
  return handleResponse<PayslipListResponse>(res);
}

/** Fetch a single published payslip owned by the current employee. */
export async function fetchMyPayslip(id: string): Promise<Payslip> {
  const res = await fetch(`${BASE}/me/${encodeURIComponent(id)}`, {
    credentials: "include",
  });
  return handleResponse<Payslip>(res);
}
