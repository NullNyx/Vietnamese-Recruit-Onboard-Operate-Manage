/**

 */

const BASE = "/api/onboarding";

// ─── Types ────────────────────────────────────────────────────────────────────

export type OnboardingStatus = "in_progress" | "complete";
export type OnboardingTaskStatus = "pending" | "done";

export interface OnboardingTask {
  id: string;
  name: string;
  status: OnboardingTaskStatus;
  order_index: number;
}

export interface OnboardingProcess {
  id: string;
  status: OnboardingStatus;
  employee_id: string;
  employee_full_name: string;
  employee_email: string;
  employee_code?: string;
  completed_count: number;
  total_count: number;
  missing_setup_fields: string[];
  accepted_at?: string | null;
  job_opening?: string | null;
  department_id?: string | null;
  position_id?: string | null;
  manager_id?: string | null;
  start_date?: string | null;
  tasks?: OnboardingTask[];
}

export interface OnboardingProcessListResponse {
  items: OnboardingProcess[];
  total: number;
  page: number;
  page_size: number;
}

export interface OnboardingCounts {
  total: number;
  in_progress: number;
  complete: number;
}

export type ProcessFilter = "all" | "in_progress" | "complete";

// ─── API Helpers ────────────────────────────────────────────────────────────

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    ...init,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "Unknown error");
    throw new Error(`API ${res.status}: ${text}`);
  }
  return res.json() as Promise<T>;
}

// ─── Query Keys ───────────────────────────────────────────────────────────────

export const onboardingKeys = {
  all: ["onboarding"] as const,
  lists: () => [...onboardingKeys.all, "list"] as const,
  list: (filter: ProcessFilter) => [...onboardingKeys.lists(), filter] as const,
  details: () => [...onboardingKeys.all, "detail"] as const,
  detail: (id: string) => [...onboardingKeys.details(), id] as const,
  counts: () => [...onboardingKeys.all, "counts"] as const,
};

// ─── API Functions ────────────────────────────────────────────────────────────

/** GET /api/onboarding/processes */
export async function listOnboardingProcesses(
  filter: ProcessFilter = "all"
): Promise<OnboardingProcessListResponse> {
  const params = filter !== "all" ? `?status=${filter}` : "";
  return apiFetch<OnboardingProcessListResponse>(`/processes${params}`);
}

/** GET /api/onboarding/processes/{process_id} */
export async function getOnboardingProcess(
  processId: string
): Promise<OnboardingProcess> {
  return apiFetch<OnboardingProcess>(`/processes/${processId}`);
}

/** GET /api/onboarding/counts */
export async function getOnboardingCounts(): Promise<OnboardingCounts> {
  return apiFetch<OnboardingCounts>("/counts");
}

/** PATCH /api/onboarding/tasks/{task_id} */
export async function updateTaskStatus(
  taskId: string,
  status: OnboardingTaskStatus
): Promise<OnboardingTask> {
  return apiFetch<OnboardingTask>(`/tasks/${taskId}`, {
    method: "PATCH",
    body: JSON.stringify({ status }),
  });
}

/** PATCH /api/onboarding/processes/{process_id}/employee-setup */
export async function updateEmployeeSetup(
  processId: string,
  data: {
    department_id?: string | null;
    position_id?: string | null;
    manager_id?: string | null;
    start_date?: string | null;
  }
): Promise<OnboardingProcess> {
  return apiFetch<OnboardingProcess>(`/processes/${processId}/employee-setup`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}
