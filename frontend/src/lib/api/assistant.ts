/**
 * API client for the AI Assistant module.
 *
 * Conversation history is held in React state (not persisted, per grill decision).
 * Each request sends the full history; backend processes statelessly.
 */

const BASE = "/api/assistant";
const TIMEOUT_MS = 60_000; // LLM calls can be slow

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

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
  confirm_endpoint: string;
  confirm_method: string;
  confirm_body: Record<string, unknown>;
}

export interface ChatResponse {
  messages: ChatMessage[];
  draft_action: DraftAction | null;
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
): Promise<ChatResponse> {
  const res = await fetchWithTimeout(`${BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ messages }),
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
