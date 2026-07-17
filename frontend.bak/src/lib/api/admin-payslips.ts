/** API client for Admin Payslip management. */

const BASE = "/api/admin/payslips";

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
  period_month: string;
  gross_salary: string;
  deductions: string;
  insurance_employee: string;
  taxable_income: string;
  pit_amount: string;
  net_salary: string;
  currency: string;
  status: "draft" | "published";
  published_at: string | null;
  pdf_url: string | null;
  created_at: string;
  updated_at: string;
}

export interface PayslipListResponse {
  payslips: Payslip[];
  total: number;
  page: number;
  page_size: number;
}

export interface CreatePayslipRequest {
  employee_id: string;
  period_month: string;
  gross_salary: string;
  deductions?: string;
  insurance_employee?: string;
  taxable_income?: string;
  pit_amount?: string;
  net_salary: string;
  pdf_url?: string;
}

export interface UpdatePayslipRequest {
  gross_salary?: string;
  deductions?: string;
  insurance_employee?: string;
  taxable_income?: string;
  pit_amount?: string;
  net_salary?: string;
  pdf_url?: string;
}

// ---------------------------------------------------------------------------
// Admin Endpoints
// ---------------------------------------------------------------------------

/** List payslips with optional filters. */
export async function fetchPayslips(options?: {
  page?: number;
  page_size?: number;
  employee_id?: string;
  status?: "draft" | "published";
  period_month?: string; // YYYY-MM
}): Promise<PayslipListResponse> {
  const params = new URLSearchParams();
  if (options?.page) params.set("page", String(options.page));
  if (options?.page_size) params.set("page_size", String(options.page_size));
  if (options?.employee_id) params.set("employee_id", options.employee_id);
  if (options?.status) params.set("status", options.status);
  if (options?.period_month) params.set("period_month", options.period_month);

  const url = params.toString() ? `${BASE}?${params}` : BASE;
  const res = await fetch(url, { credentials: "include" });
  return handleResponse<PayslipListResponse>(res);
}

/** Get a specific payslip by ID. */
export async function fetchPayslip(id: string): Promise<Payslip> {
  const res = await fetch(`${BASE}/${encodeURIComponent(id)}`, {
    credentials: "include",
  });
  return handleResponse<Payslip>(res);
}

/** Create a new draft payslip. */
export async function createPayslip(data: CreatePayslipRequest): Promise<Payslip> {
  const res = await fetch(BASE, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify(data),
  });
  return handleResponse<Payslip>(res);
}

/** Update a draft payslip. */
export async function updatePayslip(id: string, data: UpdatePayslipRequest): Promise<Payslip> {
  const res = await fetch(`${BASE}/${encodeURIComponent(id)}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify(data),
  });
  return handleResponse<Payslip>(res);
}

/** Publish a draft payslip. */
export async function publishPayslip(id: string): Promise<Payslip> {
  const res = await fetch(`${BASE}/${encodeURIComponent(id)}/publish`, {
    method: "POST",
    credentials: "include",
  });
  return handleResponse<Payslip>(res);
}

/** Delete a draft payslip. */
export async function deletePayslip(id: string): Promise<void> {
  const res = await fetch(`${BASE}/${encodeURIComponent(id)}`, {
    method: "DELETE",
    credentials: "include",
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail || `Failed to delete: ${res.status}`);
  }
}
