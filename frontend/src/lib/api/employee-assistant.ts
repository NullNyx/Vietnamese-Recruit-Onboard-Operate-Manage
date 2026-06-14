/**
 * API client for the Employee AI Assistant.
 *
 * Same interface as the HR assistant API client, but hits
 * POST /api/ess/assistant/chat instead of /api/assistant/chat.
 *
 * Conversation history is held in React state (not persisted).
 * Each request sends the full history; backend processes statelessly.
 */

const BASE = "/api/ess/assistant";
const TIMEOUT_MS = 60_000; // LLM calls can be slow

// ---------------------------------------------------------------------------
// Types (re-exported from HR assistant for shared shape)
// ---------------------------------------------------------------------------

export type { ChatMessage, DraftAction, ChatResponse } from "./assistant";

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
    return await fetch(url, {
      ...init,
      signal: controller.signal,
      credentials: "include",
    });
  } finally {
    clearTimeout(timeout);
  }
}

/**
 * Send a chat message to the Employee AI Assistant.
 *
 * @param messages - Full conversation history. Last message must be from user.
 * @returns New messages from this turn + optional Draft Action.
 */
export async function sendEmployeeChatMessage(
  messages: import("./assistant").ChatMessage[],
): Promise<import("./assistant").ChatResponse> {
  // Client-side guard: last message must be from user
  const lastMsg = messages[messages.length - 1];
  if (lastMsg && lastMsg.role !== "user") {
    throw new Error("Last message must be from user");
  }
  // Filter out tool messages and assistant-only tool-call placeholders.
  // Backend accepts only user/assistant text history (ADR-0006).
  const sanitized: { role: "user" | "assistant"; content: string }[] =
    messages.flatMap((message) => {
      if (message.role === "tool") return [];
      if (message.content === null) return [];
      const content = message.content.trim();
      if (!content) return [];
      return [{ role: message.role, content }];
    });

  const res = await fetchWithTimeout(`${BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ messages: sanitized }),
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "Unknown error");
    throw new Error(`Employee Assistant API ${res.status}: ${text}`);
  }

  return res.json() as Promise<import("./assistant").ChatResponse>;
}

/**
 * Confirm a Draft Action by calling the real endpoint directly.
 * Strictly scoped to employee endpoints — rejects HR admin endpoints.
 * This prevents employee assistant from accidentally calling HR APIs.
 */
export async function confirmEmployeeDraftAction(
  draft: import("./assistant").DraftAction,
): Promise<unknown> {
  // Scoped guard: only allow /api/employee-requests/me/* endpoints
  if (
    !draft.confirm_endpoint.startsWith("/api/employee-requests/me/")
  ) {
    throw new Error(
      "Invalid confirm endpoint: must start with /api/employee-requests/me/",
    );
  }

  const res = await fetchWithTimeout(draft.confirm_endpoint, {
    method: draft.confirm_method,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(draft.confirm_body),
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "Unknown error");
    throw new Error(`Confirm API ${res.status}: ${text}`);
  }

  return res.json();
}
