/**
 * Unified API client for Vroom HR.
 *
 * Provides a shared fetch wrapper that:
 * - Prepends NEXT_PUBLIC_API_URL (or localhost fallback)
 * - Sends credentials: "include" for HttpOnly cookie auth
 * - Auto-refreshes access token on 401 via POST /api/auth/refresh
 * - Parses error responses into ApiError with error_code
 */

// ── Token refresh state (module-level to dedupe concurrent refreshes) ──
let _refreshPromise: Promise<boolean> | null = null;

async function _tryRefreshToken(): Promise<boolean> {
  // Reuse in-flight refresh to avoid thundering-herd on 401
  if (_refreshPromise) return _refreshPromise;

  _refreshPromise = (async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/auth/refresh`, {
        method: "POST",
        credentials: "include",
      });
      return res.ok;
    } catch {
      return false;
    } finally {
      _refreshPromise = null;
    }
  })();
  return _refreshPromise;
}

import { ApiError } from "./types";
import { isValidationErrorDetail, formatValidationErrors } from "./validation-errors";

/**
 * Read the current locale from NEXT_LOCALE cookie (client-side only).
 * Falls back to 'vi' (default locale) when not found or server-side.
 */
function getAcceptLanguage(): string {
  if (typeof document === 'undefined') return 'vi';
  const match = document.cookie.match(/(?:^|;\s*)NEXT_LOCALE=([^;]*)/);
  return match?.[1] ?? 'vi';
}


/**
 * Base URL for all API requests.
 * Reads from NEXT_PUBLIC_API_URL env var, falls back to http://localhost:8000
 */
export const API_BASE_URL: string =
  (typeof process !== "undefined" && process.env?.NEXT_PUBLIC_API_URL) ||
  "http://localhost:8000";

/** True when the given request body is a browser FormData instance. */
function isFormData(body: unknown): body is FormData {
  return (
    typeof FormData !== "undefined" && body instanceof FormData
  );
}

/**
 * Core fetch wrapper for all BE API calls.
 *
 * - Prepends API_BASE_URL
 * - Always sends credentials: "include"
 * - Sets Content-Type: application/json by default (omitted for FormData so the
 *   browser can set the multipart boundary itself)
 * - Parses error responses with error_code into ApiError
 */
export async function apiFetch<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const url = `${API_BASE_URL}${path}`;
  const bodyIsForm = isFormData(options.body);

  let res: Response;
  try {
    res = await fetch(url, {
      credentials: "include",
      ...options,
      headers: {
        ...(bodyIsForm ? {} : { "Content-Type": "application/json" }),
        "Accept-Language": getAcceptLanguage(),
        ...(options.headers || {}),
      },
    });
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") {
      throw new ApiError(0, "TIMEOUT", "Yêu cầu đã hết thời gian chờ");
    }
    throw new ApiError(0, "NETWORK_ERROR", "Lỗi kết nối mạng");
  }

      if (!res.ok) {
        // 401 → try token refresh first, fallback to login redirect
        if (res.status === 401 && typeof window !== "undefined" && !window.location.pathname.match(/^\/(?:vi|en)?\/?(?:login|setup|change-password)?$/)) {

          const refreshed = await _tryRefreshToken();
          if (refreshed) {
            // Retry original request with fresh access_token cookie
            res = await fetch(url, {
              credentials: "include",
              ...options,
              headers: {
                ...(bodyIsForm ? {} : { "Content-Type": "application/json" }),
                "Accept-Language": getAcceptLanguage(),
                ...(options.headers || {}),
              },
            });
            if (res.ok) {
              if (res.status === 204) return undefined as T;
              return res.json() as Promise<T>;
            }
          }
          // Refresh failed or retry still not ok → login
          window.location.href = "/login";
          // Halt execution — never resolve, page is navigating away
          return new Promise(() => {});
        }
      const payload = await res.json().catch(() => null);

        // ── Pydantic validation error (422 detail array) ──
        if (isValidationErrorDetail(payload?.detail)) {
          const { fieldErrors, summary } = formatValidationErrors(payload.detail);
          throw new ApiError(
            res.status,
            "VALIDATION_ERROR",
            summary,
            undefined,
            fieldErrors,
          );
        }

        const errorCode =
          payload?.error_code ??
          payload?.error?.code ??
          payload?.detail?.error_code ??
          "UNKNOWN_ERROR";
        const message =
          payload?.message ??
          payload?.error?.message ??
          (typeof payload?.detail === "string" ? payload.detail : undefined) ??
          payload?.detail?.message ??
          res.statusText;
        const details = payload?.detail ?? undefined;

        throw new ApiError(
          res.status,
          errorCode,
          typeof message === "string" ? message : JSON.stringify(message),
          details && typeof details === "object" ? (details as Record<string, unknown>) : undefined,
        );
  }

  // Handle 204 No Content
  if (res.status === 204) {
    return undefined as T;
  }

  return res.json() as Promise<T>;
}


/**
 * Binary download variant: parses error bodies like apiFetch but returns a Blob
 * (plus response headers) instead of JSON. Used for MinIO presigned document
 * downloads where the BE streams file bytes.
 */
export async function apiFetchBlob(
  path: string,
  options: RequestInit = {},
): Promise<Blob> {
  const url = `${API_BASE_URL}${path}`;

  let res: Response;
  try {
    res = await fetch(url, {
      credentials: "include",
      ...options,
      headers: {
        "Accept-Language": getAcceptLanguage(),
        ...(options.headers || {}),
      },
    });
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") {
      throw new ApiError(0, "TIMEOUT", "Yêu cầu đã hết thời gian chờ");
    }
    throw new ApiError(0, "NETWORK_ERROR", "Lỗi kết nối mạng");
  }

      if (!res.ok) {
        // 401 → try token refresh first, fallback to login redirect
        if (res.status === 401 && typeof window !== "undefined" && !window.location.pathname.match(/^\/(?:vi|en)?\/?(?:login|setup|change-password)?$/)) {

          const refreshed = await _tryRefreshToken();
          if (refreshed) {
            res = await fetch(url, {
              credentials: "include",
              ...options,
              headers: {
                "Accept-Language": getAcceptLanguage(),
                ...(options.headers || {}),
              },
            });
            if (res.ok) return res.blob();
          }
          window.location.href = "/login";
          return new Promise(() => {});
        }
        // Same error parsing as apiFetch
        const payload = await res.json().catch(() => null);

        // ── Pydantic validation error (422 detail array) ──
        if (isValidationErrorDetail(payload?.detail)) {
          const { fieldErrors, summary } = formatValidationErrors(payload.detail);
          throw new ApiError(
            res.status,
            "VALIDATION_ERROR",
            summary,
            undefined,
            fieldErrors,
          );
        }

        const errorCode =
          payload?.error_code ??
          payload?.error?.code ??
          payload?.detail?.error_code ??
          "UNKNOWN_ERROR";
        const message =
          payload?.message ??
          payload?.error?.message ??
          (typeof payload?.detail === "string" ? payload.detail : undefined) ??
          payload?.detail?.message ??
          res.statusText;
        throw new ApiError(
          res.status,
          errorCode,
          typeof message === "string" ? message : JSON.stringify(message),
        );
  }

  return res.blob();
}

/** Export ApiError type alias for call sites. */
export type { ApiError };