/**
 * API client for the AI Assistant module.
 *
 * Conversation history is held in React state (not persisted, per grill decision).
 * Each request sends the full history; backend processes statelessly.
 */

import { API_BASE_URL } from "./client";

const BASE = `${API_BASE_URL}/api/assistant`;
const TIMEOUT_MS = 60_000; // LLM calls can be slow

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------


export interface AssistantFeedbackRequest {
  /** Client-generated session identifier */
  session_id: string;
  /** Index of the message this feedback is for */
  message_index: number;
  /** Thumbs up or thumbs down */
  feedback_type: "up" | "down";
  /** Optional free-text explanation */
  optional_text?: string;
}
export interface ChatMessage {
  role: "user" | "assistant" | "tool";
  content: string | null;
  tool_calls?: Array<{
    id: string;
    type: "function";
    function: { name: string; arguments: string };
  }>;
  tool_call_id?: string;
  name?: string;
}

export interface DraftAction {
  action_type: string;
  parameters: Record<string, unknown>;
  preview: string;
  provenance?: Record<string, unknown>;
  confirm_endpoint: string;
  confirm_method: string;
  confirm_body: Record<string, unknown>;
}

export interface ChatResponse {
  messages: ChatMessage[];
  draft_action: DraftAction | null;
}

export interface SessionStartResponse {
  session_id: string;
}

interface ChatRequestMessage {
  role: "user" | "assistant";
  content: string;
}

// ---------------------------------------------------------------------------
// API Functions
// ---------------------------------------------------------------------------

async function fetchWithTimeout(
  url: string,
  init?: RequestInit,
): Promise<Response> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), TIMEOUT_MS);
  try {
    return await fetch(url, { ...init, signal: controller.signal, credentials: "include" });
  } finally {
    clearTimeout(timeout);
  }
}

/**
 * Send a chat message to the AI Assistant.
 *
 * @param messages - Full conversation history. Last message must be from user.
 * @returns New messages from this turn + optional Draft Action.
 */
export async function sendChatMessage(
  messages: ChatMessage[],
  sessionId?: string,
): Promise<ChatResponse> {
  // Filter out tool messages and assistant-only tool-call placeholders.
  // Backend accepts only user/assistant text history (ADR-0006).
  const sanitized: ChatRequestMessage[] = messages.flatMap((message) => {
    if (message.role === "tool") {
      return [];
    }

    if (message.content === null) {
      return [];
    }

    const content = message.content.trim();
    if (!content) {
      return [];
    }

    return [{ role: message.role, content }];
  });

  const body: Record<string, unknown> = { messages: sanitized };
  if (sessionId) {
    body.session_id = sessionId;
  }

  const res = await fetchWithTimeout(`${BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "Unknown error");
    throw new Error(`Assistant API ${res.status}: ${text}`);
  }

  return res.json() as Promise<ChatResponse>;
}

/**
 * Confirm a Draft Action by calling the real endpoint directly.
 * The LLM is never involved in the write (ADR-0006, human-in-the-loop).
 */
export async function confirmDraftAction(
  draft: DraftAction,
): Promise<unknown> {
  // SSRF guard: only allow endpoints under the configured API base.
  if (!draft.confirm_endpoint.startsWith("/api/")) {
    throw new Error("Invalid confirm endpoint: must start with /api/");
  }

  const res = await fetchWithTimeout(`${API_BASE_URL}${draft.confirm_endpoint}`, {
    method: draft.confirm_method,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(draft.confirm_body),
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "Unknown error");
    throw new Error(`Confirm API ${res.status}: ${text}`);
  }

  // Some write endpoints return 204 No Content.
  if (res.status === 204) {
    return undefined;
  }

  return res.json();
}

/**
 * Record the HR decision after the write (or rejection) has completed.
 */
export async function recordDraftDecision(
  draft: DraftAction,
  decision: "confirm" | "reject",
): Promise<void> {
  const res = await fetchWithTimeout(`${BASE}/draft-decision`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      decision,
      action_type: draft.action_type,
      provenance: draft.provenance ?? {},
      confirm_endpoint: draft.confirm_endpoint,
    }),
  });

    if (!res.ok) {
        throw new Error(`Assistant audit API ${res.status}`);
      }
    }

    /**
     * Send feedback (thumbs up/down) for an assistant message.
     *
     * @param feedback - Feedback details including session_id, message_index, feedback_type, and optional text.
     */
    export async function sendFeedback(
      feedback: AssistantFeedbackRequest,
    ): Promise<void> {
      const res = await fetchWithTimeout(`${BASE}/feedback`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(feedback),
      });

    if (!res.ok) {
        const text = await res.text().catch(() => "Unknown error");
        throw new Error(`Feedback API ${res.status}: ${text}`);
      }
    }

/**
 * Start an AI Assistant chat session.
 * Called when ChatInterface mounts.
 */
export async function startSession(
  assistantType: "hr" | "employee",
): Promise<SessionStartResponse> {
  const res = await fetchWithTimeout(`${BASE}/session/start`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ assistant_type: assistantType }),
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "Unknown error");
    throw new Error(`Session API ${res.status}: ${text}`);
  }

  return res.json() as Promise<SessionStartResponse>;
}

/**
 * End an AI Assistant chat session.
 * Called when ChatInterface unmounts.
 */
export async function endSession(sessionId: string): Promise<void> {
  const res = await fetchWithTimeout(`${BASE}/session/end`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId }),
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "Unknown error");
    throw new Error(`Session API ${res.status}: ${text}`);
  }
}