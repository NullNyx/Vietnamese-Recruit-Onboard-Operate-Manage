import type {
  CapabilityHealth,
  CapabilityHealthState,
  OrganizationGoogleConnectionResponse,
  SyncResponse,
  MessageBodyResponse,
  SendEmailRequest,
  SendEmailResponse,
  AttachmentsResponse,
  EmailMessage,
} from "./types";
import { ApiError } from "./types";

const BASE = "/api/gmail";
const AUTH_BASE = "/api/auth";

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const body = await res.json().catch(() => ({
      detail: res.statusText,
    }));
    const message =
      body?.detail || body?.error?.message || `Request failed: ${res.status}`;
    const errorCode = body?.error_code || "UNKNOWN_ERROR";
    throw new ApiError(res.status, errorCode, message, body);
  }
  return res.json();
}

// ---------------------------------------------------------------------------
// Organization Google Connection (identity router)
// ---------------------------------------------------------------------------

/**
 * Get the current Google Workspace connection status for the organization.
 *
 * Calls GET /api/auth/organization-google-connection and returns the
 * connection state, email, and whether OAuth secrets are configured.
 */
export async function getConnectionStatus(): Promise<OrganizationGoogleConnectionResponse> {
  const res = await fetch(`${AUTH_BASE}/organization-google-connection`);
  return handleResponse<OrganizationGoogleConnectionResponse>(res);
}

/**
 * Get the Google OAuth authorize URL to start the connection flow.
 *
 * Calls GET /api/auth/organization-google-connection/authorize-url.
 * Redirect the user to the returned redirect_url.
 */
export async function getAuthorizeUrl(): Promise<OrganizationGoogleConnectionResponse> {
  const res = await fetch(
    `${AUTH_BASE}/organization-google-connection/authorize-url`,
  );
  return handleResponse<OrganizationGoogleConnectionResponse>(res);
}

/**
 * Reconnect (re-authorize) the Google Workspace connection.
 *
 * Calls POST /api/auth/organization-google-connection/reconnect.
 * Redirect the user to the returned redirect_url.
 */
export async function reconnectConnection(): Promise<OrganizationGoogleConnectionResponse> {
  const res = await fetch(
    `${AUTH_BASE}/organization-google-connection/reconnect`,
    { method: "POST" },
  );
  return handleResponse<OrganizationGoogleConnectionResponse>(res);
}

/**
 * Disconnect the organization Google Workspace connection.
 *
 * Calls DELETE /api/auth/organization-google-connection and returns the
 * resulting disconnected status.
 */
export async function disconnectConnection(): Promise<OrganizationGoogleConnectionResponse> {
  const res = await fetch(`${AUTH_BASE}/organization-google-connection`, {
    method: "DELETE",
  });
  return handleResponse<OrganizationGoogleConnectionResponse>(res);
}

// ---------------------------------------------------------------------------
// Capability Health
// ---------------------------------------------------------------------------

/**
 * Available capabilities that depend on the Google Workspace connection.
 */
export const CAPABILITIES = [
  { capability: "gmail_ingestion", label: "Gmail ingestion" },
  { capability: "gmail_sending", label: "Gmail sending" },
  { capability: "calendar_sync", label: "Calendar sync" },
] as const;

export function getCapabilityLabel(capability: string): string {
  const entry = CAPABILITIES.find((c) => c.capability === capability);
  return entry?.label ?? capability;
}

/**
 * Get capability health for each Google Workspace feature.
 *
 * Since the backend does not expose per-capability health status,
 * this returns an honest unknown/unavailable state for each capability.
 *
 * When connected, capabilities are reported as "unknown" (cannot verify).
 * When disconnected, they are reported as "unavailable" (no connection).
 */
export function getCapabilityHealth(
  isConnected: boolean,
): CapabilityHealth[] {
  const baseHealth: CapabilityHealthState = isConnected
    ? "unknown"
    : "unavailable";

  return CAPABILITIES.map((c) => ({
    capability: c.capability,
    health: baseHealth,
    label: c.label,
    description: isConnected
      ? "Không thể xác thực trạng thái dịch vụ"
      : "Chưa kết nối Gmail",
  }));
}

// ---------------------------------------------------------------------------
// Gmail operations (unchanged)
// ---------------------------------------------------------------------------

export async function syncEmails(): Promise<SyncResponse> {
  const res = await fetch(`${BASE}/sync`, {
    method: "POST",
  });
  return handleResponse<SyncResponse>(res);
}

export async function getMessageBody(
  messageId: string,
): Promise<MessageBodyResponse> {
  const res = await fetch(`${BASE}/messages/${messageId}/body`);
  return handleResponse<MessageBodyResponse>(res);
}

export async function removeLabel(
  messageId: string,
  labelName: string,
): Promise<void> {
  const res = await fetch(`${BASE}/messages/${messageId}/labels/remove`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ label_name: labelName }),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({
      detail: res.statusText,
    }));
    const message =
      body?.detail || body?.error?.message || `Request failed: ${res.status}`;
    const errorCode = body?.error_code || "UNKNOWN_ERROR";
    throw new ApiError(res.status, errorCode, message, body);
  }
}

export async function sendEmail(
  data: SendEmailRequest,
): Promise<SendEmailResponse> {
  const res = await fetch(`${BASE}/send`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return handleResponse<SendEmailResponse>(res);
}

export async function getAttachments(
  messageId: string,
): Promise<AttachmentsResponse> {
  const res = await fetch(`${BASE}/messages/${messageId}/attachments`, {
    method: "POST",
  });
  return handleResponse<AttachmentsResponse>(res);
}

export interface ClassifyResponse {
  classified_count: number;
  cv_processed_count?: number;
  total: number;
  remaining: number;
  message: string;
  results: Array<{ subject: string; category: string | null }>;
}

/**
 * Classify a small batch of emails (default 5).
 * Call repeatedly from FE to process all emails with progress.
 */
export async function classifyBatch(
  limit: number = 5,
): Promise<ClassifyResponse> {
  const res = await fetch(`${BASE}/classify?limit=${limit}`, {
    method: "POST",
  });
  return handleResponse<ClassifyResponse>(res);
}

export interface ReviewEmailsResponse {
  messages: EmailMessage[];
  total: number;
}

/**
 * List emails that need human review (needs_review status).
 */
export async function listEmailsNeedingReview(
  limit: number = 50,
  offset: number = 0,
): Promise<ReviewEmailsResponse> {
  const res = await fetch(
    `${BASE}/review/emails?limit=${limit}&offset=${offset}`,
  );
  return handleResponse<ReviewEmailsResponse>(res);
}

/**
 * Reclassify a needs_review email.
 */
export async function reclassifyEmail(
  messageId: string,
): Promise<EmailMessage> {
  const res = await fetch(`${BASE}/review/emails/${messageId}/reclassify`, {
    method: "POST",
  });
  return handleResponse<EmailMessage>(res);
}

export interface ProcessAttachmentsResponse {
  processed_count: number;
  cv_documents?: Array<{
    id: string;
    original_filename: string;
    processing_status: string;
    confidence_score: number | null;
  }>;
  message?: string;
}

/**
 * Fetch attachments and trigger CV processing pipeline for an email.
 */
    export async function processAttachments(
      messageId: string,
    ): Promise<ProcessAttachmentsResponse> {
      const res = await fetch(`${BASE}/messages/${encodeURIComponent(messageId)}/process-attachments`, {
        method: "POST",
      });
      return handleResponse<ProcessAttachmentsResponse>(res);
    }

    // ---------------------------------------------------------------------------
    // Historical import API
    // ---------------------------------------------------------------------------

    export interface ImportPreviewResponse {
      days: number;
      estimated_count: number;
      already_imported_count: number;
      query_window_start: string;
      query_window_end: string;
    }

    export interface ImportStartResponse {
      job_id: string;
      status: string;
      days: number;
      message: string;
    }

    export interface ImportStatusResponse {
      job_id: string | null;
      status: string;
      days: number | null;
      total_count: number;
      processed_count: number;
      cv_count: number;
      errors: number;
      started_at: string | null;
      completed_at: string | null;
      error_message: string | null;
    }

    export interface ImportCancelResponse {
      status: string;
      message: string;
    }

    /**
     * Preview the number of importable emails in a time window.
     */
    export async function previewImport(
      days: number,
    ): Promise<ImportPreviewResponse> {
      const res = await fetch(`${BASE}/import/preview`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ days }),
      });
      return handleResponse<ImportPreviewResponse>(res);
    }

    /**
     * Start a historical email import job.
     */
    export async function startImport(
      days: number,
    ): Promise<ImportStartResponse> {
      const res = await fetch(`${BASE}/import/start`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ days }),
      });
      return handleResponse<ImportStartResponse>(res);
    }

    /**
     * Get the status of current or last historical import job.
     */
    export async function getImportStatus(): Promise<ImportStatusResponse> {
      const res = await fetch(`${BASE}/import/status`);
      return handleResponse<ImportStatusResponse>(res);
    }

    /**
     * Cancel a running historical import job.
     */
    export async function cancelImport(): Promise<ImportCancelResponse> {
      const res = await fetch(`${BASE}/import/cancel`, {
        method: "POST",
      });
      return handleResponse<ImportCancelResponse>(res);
    }
