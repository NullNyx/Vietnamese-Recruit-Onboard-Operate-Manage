/**
 * API client for Attendance endpoints.
 *
 * Covers:
 * - ESS check-in / check-out / today / history  (/api/attendance/me/*)
 * - HR records list + correction                (/api/attendance/records*)
 * - HR network allowlist CRUD                   (/api/attendance/settings/network*)
 */

import { apiFetch } from "./client";

// ---------------------------------------------------------------------------
// Network allowlist types
// ---------------------------------------------------------------------------

export interface NetworkAllowlistResponse {
  networks: string[];
  updated_at: string | null;
}

export interface NetworkAllowlistUpdate {
  networks: string[];
}

// ---------------------------------------------------------------------------
// Attendance record types
// ---------------------------------------------------------------------------

export interface AttendanceRecord {
  id: string;
  employee_id: string;
  work_date: string;
  check_in_at: string | null;
  check_out_at: string | null;
  check_in_ip: string | null;
  check_out_ip: string | null;
  source: string;
  employee_name: string | null;
  employee_code: string | null;
  corrected_at: string | null;
  correction_reason: string | null;
  created_at: string;
  updated_at: string;
}

export interface CheckInResponse {
  message: string;
  record: AttendanceRecord;
}

export type CheckOutResponse = CheckInResponse;

export interface HistoryResponse {
  records: AttendanceRecord[];
  year: number;
  month: number;
}

export interface AttendanceListResponse {
  records: AttendanceRecord[];
  total: number;
  page: number;
  page_size: number;
}

export interface CorrectionResponse {
  message: string;
  record: AttendanceRecord;
}

export interface CorrectionData {
  /** New check-in time (null to clear). */
  check_in_at?: string | null;
  /** New check-out time (null to clear). */
  check_out_at?: string | null;
  /** Required reason for the correction. */
  correction_reason: string;
}

// ===========================================================================
// ESS endpoints
// ===========================================================================

export async function checkIn(): Promise<CheckInResponse> {
  return apiFetch<CheckInResponse>("/api/attendance/me/check-in", { method: "POST" });
}

export async function checkOut(): Promise<CheckOutResponse> {
  return apiFetch<CheckOutResponse>("/api/attendance/me/check-out", { method: "POST" });
}

/** Today's record for the current employee, or null if none yet. */
export async function getTodayRecord(): Promise<AttendanceRecord | null> {
  return apiFetch<AttendanceRecord | null>("/api/attendance/me/today");
}

export async function getMyHistory(params?: {
  year?: number;
  month?: number;
  days?: number;
}): Promise<HistoryResponse> {
  const sp = new URLSearchParams();
  if (params?.year !== undefined) sp.set("year", String(params.year));
  if (params?.month !== undefined) sp.set("month", String(params.month));
  if (params?.days !== undefined) sp.set("days", String(params.days));
  const qs = sp.toString();
  return apiFetch<HistoryResponse>(qs ? `/api/attendance/me/history?${qs}` : "/api/attendance/me/history");
}

// ===========================================================================
// HR admin endpoints
// ===========================================================================

export async function listAttendanceRecords(params: {
  start_date: string;
  end_date: string;
  employee_id?: string;
  status?: "checked_in" | "completed";
  page?: number;
  page_size?: number;
}): Promise<AttendanceListResponse> {
  const sp = new URLSearchParams();
  sp.set("start_date", params.start_date);
  sp.set("end_date", params.end_date);
  if (params.employee_id) sp.set("employee_id", params.employee_id);
  if (params.status) sp.set("status", params.status);
  if (params.page) sp.set("page", String(params.page));
  if (params.page_size) sp.set("page_size", String(params.page_size));
  return apiFetch<AttendanceListResponse>(`/api/attendance/records?${sp.toString()}`);
}

export async function correctAttendanceRecord(
  recordId: string,
  data: CorrectionData,
): Promise<CorrectionResponse> {
  return apiFetch<CorrectionResponse>(
    `/api/attendance/records/${recordId}/correct`,
    { method: "PUT", body: JSON.stringify(data) },
  );
}

// ===========================================================================
// Network allowlist
// ===========================================================================

const NETWORK_BASE = "/api/attendance/settings/network";

export async function getNetworkAllowlist(): Promise<NetworkAllowlistResponse> {
  return apiFetch<NetworkAllowlistResponse>(NETWORK_BASE);
}

export async function updateNetworkAllowlist(
  networks: string[],
): Promise<NetworkAllowlistResponse> {
  return apiFetch<NetworkAllowlistResponse>(NETWORK_BASE, {
    method: "PUT",
    body: JSON.stringify({ networks }),
  });
}

export async function addNetworkToAllowlist(
  networks: string[],
): Promise<NetworkAllowlistResponse> {
  return apiFetch<NetworkAllowlistResponse>(`${NETWORK_BASE}/add`, {
    method: "POST",
    body: JSON.stringify({ networks }),
  });
}

export async function removeNetworkFromAllowlist(
  cidr: string,
): Promise<NetworkAllowlistResponse> {
  const params = new URLSearchParams({ cidr });
  return apiFetch<NetworkAllowlistResponse>(`${NETWORK_BASE}?${params.toString()}`, {
    method: "DELETE",
  });
}