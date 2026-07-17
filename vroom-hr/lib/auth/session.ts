'use client';

import { useQuery } from "@tanstack/react-query";
import type { CurrentUser } from "@/lib/api/auth";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { apiFetch } from "@/lib/api/client";
import { ApiError } from "@/lib/api/types";

/**
 * Fetch current user profile from BE via GET /api/auth/me.
 *
 * IMPORTANT (BUG-1 fix): BE trả về **flat `UserResponse`** (`{id, email, name,
 * role, must_change_password, gmail_grant_valid, calendar_grant_valid,
 * employee_id, …}`) — KHÔNG wrap trong `user`. Endpoint này khác với
 * `/login`, `/setup`, `/change-password` (các endpoint đó trả
 * `AuthSessionResponse = { user, must_change_password, setup_complete }`,
 * được `lib/api/auth.ts` giữ nguyên).
 *
 * Trả về `CurrentUser` flat khi 200; trả về `null` khi 401/403 (chưa authed).
 * Các lỗi khác (mạng, 5xx) đẩy lên React Query để retry.
 */
async function fetchCurrentUser(): Promise<CurrentUser | null> {
  try {
    return await apiFetch<CurrentUser>("/api/auth/me");
  } catch (error) {
    if (error instanceof ApiError && (error.statusCode === 401 || error.statusCode === 403)) {
      return null;
    }
    throw error;
  }
}

/**
 * React Query hook that fetches and caches the current user session.
 *
 * - Trả về `user` (CurrentUser flat, khớp BE `/api/auth/me`), `isLoading`,
 *   `isAuthenticated`, `isAdmin`, `mustChangePassword`, `setupComplete`.
 * - Khi `/api/auth/me` 401/403 → `user` = null (unauthenticated).
 * - Refetch on window focus via React Query defaults.
 *
 * API public giữ nguyên so với bản cũ để các layout/page không phải refactor:
 * `user`, `isLoading`, `isAuthenticated`, `isAdmin`, `mustChangePassword`,
 * `setupComplete`, `error`, `refetch`.
 */
export function useSession() {
  const { data, isLoading, error, refetch } = useQuery<CurrentUser | null>({
    queryKey: ["session"],
    queryFn: fetchCurrentUser,
    retry: (failureCount, error) => {
      // Don't retry auth failures (đã được map thành null, nhưng phòng hờ
      // khi queryFn throw ApiError 401/403 do logic_gateway).
      if (error instanceof ApiError && (error.statusCode === 401 || error.statusCode === 403)) {
        return false;
      }
      return failureCount < 2;
    },
    staleTime: 30 * 1000,
  });

  // `data` là flat CurrentUser khi authed; `null` khi 401/403; `undefined`
  // khi đang loading hoặc lỗi tạm thời chưa retry xong.
  const user: CurrentUser | null = data ?? null;
  const isAuthenticated = !!data && !error;
  const isAdmin = user?.role === "admin";
  const mustChangePassword = user?.must_change_password ?? false;
  // /api/auth/me trả 200 ⇔ đã có user (và org) ⇒ setup hoàn tất.
  const setupComplete = !!data;

  return {
    user,
    isLoading,
    isAuthenticated,
    isAdmin,
    mustChangePassword,
    setupComplete,
    error,
    refetch,
  };
}

/**
 * Higher-level hook that redirects based on auth state.
 * Use in page components that need auth guards.
 *
 * Options:
 * - requireAuth: redirect to /login if not authenticated
 * - requireAdmin: redirect to /employee if not admin
 * - requireEmployee: redirect to / if not employee
 * - redirectIfAuthenticated: redirect to /dashboard if already logged in
 */
export function useAuthGuard(options: {
  requireAuth?: boolean;
  requireAdmin?: boolean;
  requireEmployee?: boolean;
  redirectIfAuthenticated?: boolean;
} = {}) {
  const { user, isLoading, isAuthenticated, isAdmin } = useSession();
  const router = useRouter();

  useEffect(() => {
    if (isLoading) return;

    if (options.redirectIfAuthenticated && isAuthenticated) {
      if (isAdmin) {
        router.replace("/dashboard");
      } else {
        router.replace("/employee");
      }
      return;
    }

    if (options.requireAuth && !isAuthenticated) {
      router.replace("/login");
      return;
    }

    if (options.requireAdmin && !isAdmin) {
      router.replace("/employee");
      return;
    }

    if (options.requireEmployee && isAdmin) {
      router.replace("/dashboard");
      return;
    }
  }, [
    isLoading,
    isAuthenticated,
    isAdmin,
    router,
    options.requireAuth,
    options.requireAdmin,
    options.requireEmployee,
    options.redirectIfAuthenticated,
  ]);

  return { user, isLoading, isAuthenticated, isAdmin };
}