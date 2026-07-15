"use client";

import { useEffect, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";

import type { CurrentUser } from "@/lib/api/auth";

export type { CurrentUser } from "@/lib/api/auth";

export const currentUserQueryKey = ["current-user"] as const;
const E2E_CURRENT_USER_KEY = "vroom-hr:e2e-current-user";

function readE2ECurrentUserOverride(): CurrentUser | null {
  if (typeof window === "undefined") return null;
  try {
    const globalUser = (window as typeof window & {
      __VROOM_HR_E2E_CURRENT_USER__?: CurrentUser;
    }).__VROOM_HR_E2E_CURRENT_USER__;
    if (globalUser) return globalUser;
    const raw = window.localStorage.getItem(E2E_CURRENT_USER_KEY);
    return raw ? (JSON.parse(raw) as CurrentUser) : null;
  } catch {
    return null;
  }
}

async function fetchCurrentUser(): Promise<CurrentUser | null> {
  const res = await fetch("/api/auth/me");
  if (!res.ok) {
    if (res.status === 401) return null;
    throw new Error(`Failed to fetch user: ${res.status}`);
  }
  return res.json();
}

/**
 * Cached current user hook — fetches once, shares across all components.
 * No more re-fetching on every navigation.
 */
export function useCurrentUser() {
  const queryClient = useQueryClient();
  const [hydrated, setHydrated] = useState(false);
  const [e2eUser, setE2eUser] = useState<CurrentUser | null>(null);

  useEffect(() => {
    setHydrated(true);
    setE2eUser(readE2ECurrentUserOverride());
  }, []);

  const {
    data: user,
    isLoading: loading,
    error,
    refetch: refetchCurrentUser,
  } = useQuery({
    queryKey: currentUserQueryKey,
    queryFn: fetchCurrentUser,
    enabled: hydrated && !e2eUser,
    initialData: e2eUser ?? undefined,
    // User data is stable — keep fresh for 5 minutes
    staleTime: 5 * 60 * 1000,
    gcTime: 30 * 60 * 1000,
    // Don't refetch on every window focus
    refetchOnWindowFocus: false,
    refetchOnMount: false,
  });

  const refetch = async () => {
    if (e2eUser) return;
    await queryClient.invalidateQueries({
      queryKey: currentUserQueryKey,
      refetchType: "none",
    });
    await refetchCurrentUser();
  };

  return {
    user: user ?? null,
    loading: hydrated ? loading : true,
    error: error?.message ?? null,
    refetch,
  };
}
