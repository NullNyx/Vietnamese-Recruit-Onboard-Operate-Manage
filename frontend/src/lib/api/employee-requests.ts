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
  request_type: "leave" | "overtime";
  status: "submitted" | "approved" | "rejected" | "cancelled";
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
  /** Review fields */
  review_reason: string | null;
  reviewed_at: string | null;
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
  status: "submitted" | "approved" | "rejected" | "cancelled";
  leave_type: string | null;
  start_date: string | null;
  end_date: string | null;
  reason: string | null;
  submitted_at: string | null;
  updated_at: string | null;
  cancellation_reason: string | null;
  review_reason: string | null;
  reviewed_at: string | null;
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
  status: "submitted" | "approved" | "rejected" | "cancelled";
  work_date: string | null;
  start_time: string | null;
  end_time: string | null;
  duration_minutes: number | null;
  reason: string | null;
  project_or_task: string | null;
  submitted_at: string | null;
  updated_at: string | null;
  cancellation_reason: string | null;
  review_reason: string | null;
  reviewed_at: string | null;
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
  const res = await fetch(`${BASE}/me/leave/${encodeURIComponent(requestId)}/cancel`, {
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
  const res = await fetch(`${BASE}/me/overtime/${encodeURIComponent(requestId)}/cancel`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({ cancellation_reason: cancellationReason ?? null }),
  });
  return handleResponse<OvertimeCancelResponse>(res);
}

// ---------------------------------------------------------------------------
// Admin / HR Review
// ---------------------------------------------------------------------------

const ADMIN_BASE = "/api/admin/employee-requests";

export interface AdminEmployeeRequestItem {
  id: string;
  employee_id: string;
  employee_name: string;
  request_type: "leave" | "overtime";
  status: "submitted" | "approved" | "rejected" | "cancelled";
  submitted_at: string | null;
  updated_at: string | null;
  reason: string | null;
  /** Overtime fields */
  work_date: string | null;
  start_time: string | null;
  end_time: string | null;
  duration_minutes: number | null;
  /** Leave fields */
  leave_type: string | null;
  start_date: string | null;
  end_date: string | null;
  /** Cancellation */
  cancellation_reason: string | null;
  /** Review fields */
  review_reason: string | null;
  reviewed_at: string | null;
  reviewed_by_user_id: string | null;
}

export interface AdminReviewQueueResponse {
  requests: AdminEmployeeRequestItem[];
}

export interface ReviewRequest {
  review_reason?: string | null;
}

export interface ReviewResponse {
  message: string;
  request: AdminEmployeeRequestItem;
}

export interface FetchSubmittedRequestsFilters {
  request_type?: "leave" | "overtime" | null;
  status?: "submitted" | "approved" | "rejected" | "cancelled" | null;
  date_from?: string | null;
  date_to?: string | null;
  employee_id?: string | null;
}

/** Fetch submitted requests for HR review queue with filters (admin only). */
export async function fetchSubmittedRequests(
  filters?: FetchSubmittedRequestsFilters,
): Promise<AdminReviewQueueResponse> {
  const params = new URLSearchParams();
  if (filters) {
    if (filters.request_type) params.append("request_type", filters.request_type);
    if (filters.status) params.append("status", filters.status);
    if (filters.date_from) params.append("date_from", filters.date_from);
    if (filters.date_to) params.append("date_to", filters.date_to);
    if (filters.employee_id) params.append("employee_id", filters.employee_id);
  }
  const url = params.toString() ? `${ADMIN_BASE}?${params.toString()}` : ADMIN_BASE;
  const res = await fetch(url, { credentials: "include" });
  return handleResponse<AdminReviewQueueResponse>(res);
}

/** Approve a submitted employee request (admin only). */
export async function approveRequest(
  requestId: string,
  reviewReason?: string | null,
): Promise<ReviewResponse> {
  const res = await fetch(`${ADMIN_BASE}/${encodeURIComponent(requestId)}/approve`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({ review_reason: reviewReason ?? null }),
  });
  return handleResponse<ReviewResponse>(res);
}

/** Reject a submitted employee request (admin only). */
export async function rejectRequest(
  requestId: string,
  reviewReason?: string | null,
): Promise<ReviewResponse> {
  const res = await fetch(`${ADMIN_BASE}/${encodeURIComponent(requestId)}/reject`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({ decision_reason: reviewReason ?? null }),
  });
  return handleResponse<ReviewResponse>(res);
}
