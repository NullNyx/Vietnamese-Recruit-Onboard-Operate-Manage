/**

 */

const BASE = "/api/onboarding";

// ─── Types ────────────────────────────────────────────────────────────────────

export type OnboardingStatus = "in_progress" | "ready_for_completion" | "complete";
export type OnboardingTaskStatus = "pending" | "done";

export interface OnboardingTask {
  id: string;
  name: string;
  status: OnboardingTaskStatus;
  order_index: number;
  completed_at?: string | null;
  completed_by_name?: string | null;
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
  completed_at?: string | null;
  accepted_at?: string | null;
  job_opening?: string | null;
  department_id?: string | null;
  position_id?: string | null;
  manager_id?: string | null;
  start_date?: string | null;
  tasks?: OnboardingTask[];
  documents?: OnboardingDocument[];
  contract_draft?: OnboardingContractDraft | null;
}

export interface OnboardingTimelineItem {
  event_type: string;
  kind: "milestone" | "task" | "document" | "contract" | "reminder";
  timestamp: string;
  title: string;
  description?: string | null;
  actor_name?: string | null;
  status?: string | null;
  due_at?: string | null;
  is_overdue: boolean;
}

export interface OnboardingContractDraft {
  id: string;
  process_id: string;
  contract_type: string;
  content: string | null;
  status: "draft" | "ready" | "sent" | "signed";
  revision: number;
  created_by: string | null;
  updated_by: string | null;
  created_at: string;
  updated_at: string;
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
  ready_for_completion: number;
  complete: number;
}

export type ProcessFilter = "all" | "in_progress" | "ready_for_completion" | "complete";

export interface ContractDraftUpdate {
  contract_type?: string | null;
  content?: string | null;
}

export type ContractDraft = OnboardingContractDraft;

export interface ContractDraftStatusUpdate {
  status: OnboardingContractDraft["status"];
}

export interface OnboardingTimelineResponse {
  events: OnboardingTimelineItem[];
}

export type OnboardingTemplateType = "task" | "document" | "contract";

export interface OnboardingTemplate {
  id: string;
  template_type: OnboardingTemplateType;
  key: string;
  display_name: string;
  description: string | null;
  template_body: string | null;
  is_required: boolean;
  order_index: number;
  version: number;
  is_system: boolean;
  is_archived: boolean;
  created_at: string;
  updated_at: string;
}

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

/** PATCH /api/onboarding/processes/{process_id}/complete */
export async function confirmOnboardingCompletion(processId: string): Promise<OnboardingProcess> {
  return apiFetch<OnboardingProcess>(`/processes/${processId}/complete`, {
    method: "PATCH",
  });
}

/** GET /api/onboarding/processes/{process_id}/timeline */
export async function getOnboardingTimeline(processId: string): Promise<OnboardingTimelineResponse> {
  return apiFetch<OnboardingTimelineResponse>(`/processes/${processId}/timeline`);
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

// ─── Document Types ──────────────────────────────────────────────────────────

export interface OnboardingDocument {
  id: string;
  process_id: string;
  document_type: string;
  display_name: string;
  is_required: boolean;
  status: "pending" | "uploaded" | "verified" | "rejected";
  file_name: string | null;
  file_size: number | null;
  mime_type: string | null;
  reject_reason: string | null;
  uploaded_by_hr_id: string | null;
  uploaded_at: string | null;
  verified_by_hr_id: string | null;
  verified_at: string | null;
  ai_extraction: Record<string, unknown> | null;
}

export interface DocumentUploadResponse {
  id: string;
  status: string;
  file_name: string;
  file_size: number;
  mime_type: string;
}

export interface DocumentVerifyRequest {
  verified: boolean;
  reject_reason?: string | null;
}

export interface DocumentCounts {
  total: number;
  pending: number;
  uploaded: number;
  verified: number;
  rejected: number;
}

// ─── Contract Draft API ───────────────────────────────────────────────────────

/** GET /api/onboarding/processes/{process_id}/contract */
export async function getOnboardingContractDraft(processId: string): Promise<OnboardingContractDraft> {
  return apiFetch<OnboardingContractDraft>(`/processes/${processId}/contract`);
}

/** PATCH /api/onboarding/processes/{process_id}/contract */
export async function updateOnboardingContractDraft(
  processId: string,
  data: ContractDraftUpdate,
): Promise<ContractDraft> {
  return apiFetch<OnboardingContractDraft>(`/processes/${processId}/contract`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

/** PATCH /api/onboarding/processes/{process_id}/contract/generate */
export async function generateContractDraft(processId: string): Promise<OnboardingContractDraft> {
  return apiFetch<OnboardingContractDraft>(`/processes/${processId}/contract/generate`, {
    method: "PATCH",
  });
}

/** PATCH /api/onboarding/processes/{process_id}/contract/status */
export async function updateContractStatus(
  processId: string,
  data: { status: string },
): Promise<OnboardingContractDraft> {
  return apiFetch<OnboardingContractDraft>(`/processes/${processId}/contract/status`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

/** GET /api/onboarding/processes/{process_id}/contract/export */
export async function exportContractDraft(processId: string): Promise<string> {
  const res = await fetch(`${BASE}/processes/${processId}/contract/export`, {
    credentials: "include",
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "Unknown error");
    throw new Error(`API ${res.status}: ${text}`);
  }
  return res.text();
}

// ─── Template API ────────────────────────────────────────────────────────────

export interface OnboardingTemplateCreateInput {
  template_type: OnboardingTemplateType;
  key: string;
  display_name: string;
  description?: string | null;
  template_body?: string | null;
  is_required?: boolean;
  order_index?: number;
  version?: number;
  is_system?: boolean;
  is_archived?: boolean;
}

export interface OnboardingTemplateUpdateInput {
  display_name?: string | null;
  description?: string | null;
  template_body?: string | null;
  is_required?: boolean | null;
  order_index?: number | null;
  is_archived?: boolean | null;
}

async function templateFetch<T>(path: string, init?: RequestInit): Promise<T> {
  return apiFetch<T>(`/templates${path}`, init);
}

export async function listOnboardingTemplates(
  templateType?: OnboardingTemplateType,
  includeArchived = false,
): Promise<{ items: OnboardingTemplate[] }> {
  const params = new URLSearchParams();
  if (templateType) params.set("template_type", templateType);
  if (includeArchived) params.set("include_archived", "true");
  const suffix = params.toString() ? `?${params.toString()}` : "";
  return templateFetch<{ items: OnboardingTemplate[] }>(suffix);
}

export async function createOnboardingTemplate(
  data: OnboardingTemplateCreateInput,
): Promise<OnboardingTemplate> {
  return templateFetch<OnboardingTemplate>("", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function updateOnboardingTemplate(
  templateId: string,
  data: OnboardingTemplateUpdateInput,
): Promise<OnboardingTemplate> {
  return templateFetch<OnboardingTemplate>(`/${templateId}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export async function archiveOnboardingTemplate(templateId: string): Promise<OnboardingTemplate> {
  return templateFetch<OnboardingTemplate>(`/${templateId}/archive`, {
    method: "POST",
  });
}

export async function previewOnboardingTemplate(
  templateId: string,
): Promise<{ id: string; template_type: OnboardingTemplateType; preview: string }> {
  return templateFetch<{ id: string; template_type: OnboardingTemplateType; preview: string }>(
    `/${templateId}/preview`,
  );
}

// ─── Document API ────────────────────────────────────────────────────────────

/** GET /api/onboarding/processes/{process_id}/documents */
export async function listOnboardingDocuments(processId: string): Promise<OnboardingDocument[]> {
  return apiFetch<OnboardingDocument[]>(`/processes/${processId}/documents`);
}

/** PATCH /api/onboarding/documents/{document_id}/upload */
export async function uploadOnboardingDocument(documentId: string): Promise<DocumentUploadResponse> {
  return apiFetch<DocumentUploadResponse>(`/documents/${documentId}/upload`, { method: "PATCH" });
}

/** PATCH /api/onboarding/documents/{document_id}/verify */
export async function verifyOnboardingDocument(
  documentId: string,
  data: DocumentVerifyRequest,
): Promise<OnboardingDocument> {
  return apiFetch<OnboardingDocument>(`/documents/${documentId}/verify`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}
