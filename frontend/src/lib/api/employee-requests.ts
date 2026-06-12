/** API client for Employee Request (Leave & Overtime) endpoints. */

const BASE = "/api/employee-requests";

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail || `Request failed: ${res.status}`);
  }
  return res.json();
}

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface EmployeeRequestListItem {
  id: string;
  employee_id: string;
  request_type: string;
  status: string;
  submitted_at: string | null;
  updated_at: string | null;
  /** Overtime fields */
  work_date: string | null;
  start_time: string | null;
  end_time: string | null;
  duration_minutes: number | null;
  /** Leave fields */
  leave_type: string | null;
  start_date: string | null;
  end_date: string | null;
  /** Common */
  reason: string | null;
  project_or_task: string | null;
  cancellation_reason: string | null;
}

export interface EmployeeRequestListResponse {
  requests: EmployeeRequestListItem[];
}

export interface CreateLeaveData {
  leave_type: "annual" | "sick" | "unpaid" | "other";
  start_date: string;
  end_date: string;
  reason: string;
}

export interface LeaveResponse {
  id: string;
  employee_id: string;
  status: string;
  leave_type: string | null;
  start_date: string | null;
  end_date: string | null;
  reason: string | null;
  submitted_at: string | null;
  updated_at: string | null;
  cancellation_reason: string | null;
}

export interface LeaveCreateResponse {
  message: string;
  request: LeaveResponse;
}

export interface LeaveCancelResponse {
  message: string;
  request: LeaveResponse;
}

export interface CreateOvertimeData {
  work_date: string;
  start_time: string;
  end_time: string;
  reason: string;
  project_or_task?: string | null;
}

export interface OvertimeResponse {
  id: string;
  employee_id: string;
  status: string;
  work_date: string | null;
  start_time: string | null;
  end_time: string | null;
  duration_minutes: number | null;
  reason: string | null;
  project_or_task: string | null;
  submitted_at: string | null;
  updated_at: string | null;
  cancellation_reason: string | null;
}

export interface OvertimeCreateResponse {
  message: string;
  request: OvertimeResponse;
}

export interface OvertimeCancelResponse {
  message: string;
  request: OvertimeResponse;
}

// ---------------------------------------------------------------------------
// List
// ---------------------------------------------------------------------------

/** Fetch all requests for the current employee (leave + overtime merged). */
export async function fetchMyRequests(): Promise<EmployeeRequestListResponse> {
  const res = await fetch(`${BASE}/me`, { credentials: "include" });
  return handleResponse<EmployeeRequestListResponse>(res);
}

// ---------------------------------------------------------------------------
// Leave
// ---------------------------------------------------------------------------

/** Create a new leave request. */
export async function createLeave(data: CreateLeaveData): Promise<LeaveCreateResponse> {
  const res = await fetch(`${BASE}/me/leave`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify(data),
  });
  return handleResponse<LeaveCreateResponse>(res);
}

/** Cancel own submitted leave request. */
export async function cancelLeave(
  requestId: string,
  cancellationReason?: string | null,
): Promise<LeaveCancelResponse> {
  const res = await fetch(`${BASE}/me/leave/${requestId}/cancel`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({ cancellation_reason: cancellationReason ?? null }),
  });
  return handleResponse<LeaveCancelResponse>(res);
}

// ---------------------------------------------------------------------------
// Overtime
// ---------------------------------------------------------------------------

/** Create a new overtime request. */
export async function createOvertime(data: CreateOvertimeData): Promise<OvertimeCreateResponse> {
  const res = await fetch(`${BASE}/me/overtime`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify(data),
  });
  return handleResponse<OvertimeCreateResponse>(res);
}

/** Cancel own submitted overtime request. */
export async function cancelOvertime(
  requestId: string,
  cancellationReason?: string | null,
): Promise<OvertimeCancelResponse> {
  const res = await fetch(`${BASE}/me/overtime/${requestId}/cancel`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({ cancellation_reason: cancellationReason ?? null }),
  });
  return handleResponse<OvertimeCancelResponse>(res);
}
