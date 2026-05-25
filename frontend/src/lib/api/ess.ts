/**
 * API client for Employee Self-Service (ESS) endpoints.
 */

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const error = await res
      .json()
      .catch(() => ({ detail: { message: res.statusText } }));
    throw new Error(error.detail?.message || `Request failed: ${res.status}`);
  }
  return res.json();
}

/**
 * Handle response but also return the HTTP status code for 409 handling.
 */
async function handleResponseWithStatus<T>(
  res: Response,
): Promise<{ data: T; status: number }> {
  if (!res.ok) {
    const error = await res
      .json()
      .catch(() => ({ detail: { message: res.statusText, code: "" } }));
    const err = new Error(
      error.detail?.message || `Request failed: ${res.status}`,
    ) as Error & { statusCode: number; errorCode: string };
    err.statusCode = res.status;
    err.errorCode = error.detail?.code || "";
    throw err;
  }
  const data = await res.json();
  return { data, status: res.status };
}

// Types

export type AttendanceStatus = "not_checked_in" | "checked_in" | "checked_out";

export interface MonthlySummary {
  days_worked: number;
  days_absent: number;
  total_hours: number;
}

export interface DashboardData {
  today_attendance: AttendanceStatus;
  pending_leave_count: number;
  pending_overtime_count: number;
  monthly_summary: MonthlySummary;
  annual_leave_remaining: number | null;
}

export interface CheckInOutResponse {
  id: string;
  employee_id: string;
  work_date: string;
  check_in: string | null;
  check_out: string | null;
  work_hours: number | null;
  overtime_hours: number;
  status: string;
}

export interface TodayAttendanceResponse {
  id: string;
  employee_id: string;
  work_date: string;
  check_in: string | null;
  check_out: string | null;
  work_hours: number | null;
  overtime_hours: number;
  status: string;
}

export interface AttendanceHistoryRecord {
  id: string;
  employee_id: string;
  work_date: string;
  check_in: string | null;
  check_out: string | null;
  work_hours: number | null;
  overtime_hours: number;
  status: string;
  note: string | null;
}

export interface AttendanceHistorySummary {
  total_work_days: number;
  total_work_hours: number;
  total_overtime_hours: number;
  late_count: number;
  early_departure_count: number;
}

export interface AttendanceHistoryResponse {
  records: AttendanceHistoryRecord[];
  summary: AttendanceHistorySummary;
}

// Overtime types
export interface OvertimeRequestResponse {
  id: string;
  employee_id: string;
  work_date: string;
  planned_hours: number;
  actual_hours: number | null;
  reason: string;
  status: string;
  created_at: string;
}

export interface CreateOvertimeRequestData {
  work_date: string;
  planned_hours: number;
  reason: string;
}

// Overtime API
export async function createOvertimeRequest(
  data: CreateOvertimeRequestData,
): Promise<OvertimeRequestResponse> {
  const res = await fetch("/api/v1/ess/overtime/requests", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return handleResponse<OvertimeRequestResponse>(res);
}

export async function getOvertimeRequests(): Promise<
  OvertimeRequestResponse[]
> {
  const res = await fetch("/api/v1/ess/overtime/requests");
  return handleResponse<OvertimeRequestResponse[]>(res);
}

export async function cancelOvertimeRequest(
  requestId: string,
): Promise<OvertimeRequestResponse> {
  const res = await fetch(`/api/v1/ess/overtime/requests/${requestId}/cancel`, {
    method: "POST",
  });
  return handleResponse<OvertimeRequestResponse>(res);
}

// Dashboard
export async function getDashboard(): Promise<DashboardData> {
  const res = await fetch("/api/v1/ess/dashboard");
  return handleResponse<DashboardData>(res);
}

// Attendance - Today's status
export async function getAttendanceToday(): Promise<TodayAttendanceResponse | null> {
  const res = await fetch("/api/v1/ess/attendance/today");
  if (res.status === 404) return null;
  return handleResponse<TodayAttendanceResponse>(res);
}

// Attendance - History
export async function getAttendanceHistory(
  month: number,
  year: number,
): Promise<AttendanceHistoryResponse> {
  const res = await fetch(
    `/api/v1/ess/attendance/history?month=${month}&year=${year}`,
  );
  return handleResponse<AttendanceHistoryResponse>(res);
}

// Attendance actions
export async function checkIn(): Promise<CheckInOutResponse> {
  const res = await fetch("/api/v1/ess/attendance/check-in", {
    method: "POST",
  });
  const { data } = await handleResponseWithStatus<CheckInOutResponse>(res);
  return data;
}

export async function checkOut(): Promise<CheckInOutResponse> {
  const res = await fetch("/api/v1/ess/attendance/check-out", {
    method: "POST",
  });
  const { data } = await handleResponseWithStatus<CheckInOutResponse>(res);
  return data;
}

// Leave types

export interface LeaveBalance {
  leave_type_id: string;
  leave_type_name: string;
  total_days: number;
  used_days: number;
  remaining_days: number;
}

export interface LeaveRequestResponse {
  id: string;
  employee_id: string;
  leave_type_id: string;
  leave_type_name: string;
  start_date: string;
  end_date: string;
  total_days: number;
  reason: string | null;
  status: string;
  created_at: string;
  reviewed_by: string | null;
  reviewed_at: string | null;
  review_note: string | null;
}

export type LeaveRequest = LeaveRequestResponse;

export interface CreateLeaveRequestPayload {
  leave_type_id: string;
  start_date: string;
  end_date: string;
  reason?: string;
}

// Leave - Balances
export async function getLeaveBalances(): Promise<LeaveBalance[]> {
  const res = await fetch("/api/v1/ess/leave/balances");
  return handleResponse<LeaveBalance[]>(res);
}

// Leave - List requests
export async function getLeaveRequests(): Promise<LeaveRequestResponse[]> {
  const res = await fetch("/api/v1/ess/leave/requests");
  return handleResponse<LeaveRequestResponse[]>(res);
}

// Leave - Create request
export async function createLeaveRequest(
  data: CreateLeaveRequestPayload,
): Promise<LeaveRequestResponse> {
  const res = await fetch("/api/v1/ess/leave/requests", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  const { data: result } =
    await handleResponseWithStatus<LeaveRequestResponse>(res);
  return result;
}

// Leave - Cancel request
export async function cancelLeaveRequest(
  requestId: string,
): Promise<LeaveRequestResponse> {
  const res = await fetch(`/api/v1/ess/leave/requests/${requestId}/cancel`, {
    method: "POST",
  });
  const { data } = await handleResponseWithStatus<LeaveRequestResponse>(res);
  return data;
}

// Documents

export interface ESSDocument {
  id: string;
  file_name: string;
  document_type: string;
  file_size: number;
  uploaded_at: string;
}

export interface ESSDocumentDownload {
  download_url: string;
  file_name: string;
  expires_in_seconds: number;
}

export async function getDocuments(
  documentType?: string,
): Promise<ESSDocument[]> {
  const params = new URLSearchParams();
  if (documentType) {
    params.set("document_type", documentType);
  }
  const query = params.toString();
  const url = `/api/v1/ess/documents${query ? `?${query}` : ""}`;
  const res = await fetch(url);
  return handleResponse<ESSDocument[]>(res);
}

export async function getDocumentDownloadUrl(
  documentId: string,
): Promise<ESSDocumentDownload> {
  const res = await fetch(`/api/v1/ess/documents/${documentId}/download`);
  return handleResponse<ESSDocumentDownload>(res);
}

// Schedule types

export interface ScheduleHoliday {
  holiday_date: string;
  name: string;
}

export interface ScheduleResponse {
  schedule_name: string;
  shift_start: string;
  shift_end: string;
  working_days: string[];
  holidays: ScheduleHoliday[];
}

export interface NoScheduleResponse {
  message: string;
}

export type ScheduleResult = ScheduleResponse | NoScheduleResponse;

// Schedule API
export async function getSchedule(): Promise<ScheduleResult> {
  const res = await fetch("/api/v1/ess/schedule");
  return handleResponse<ScheduleResult>(res);
}
