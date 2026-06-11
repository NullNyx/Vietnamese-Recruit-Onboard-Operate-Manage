import type {
  ConnectionStatusResponse,
  ConnectResponse,
  SyncResponse,
  MessageBodyResponse,
  SendEmailRequest,
  SendEmailResponse,
  AttachmentsResponse,
  EmailMessage,
} from "./types";
import { ApiError } from "./types";

const BASE = "/api/gmail";

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

export async function getStatus(): Promise<ConnectionStatusResponse> {
  const res = await fetch(`${BASE}/status`);
  return handleResponse<ConnectionStatusResponse>(res);
}

export async function connect(): Promise<ConnectResponse> {
  const res = await fetch(`${BASE}/connect`, {
    method: "POST",
  });
  return handleResponse<ConnectResponse>(res);
}

export async function disconnect(): Promise<ConnectionStatusResponse> {
  const res = await fetch(`${BASE}/disconnect`, {
    method: "POST",
  });
  return handleResponse<ConnectionStatusResponse>(res);
}

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
