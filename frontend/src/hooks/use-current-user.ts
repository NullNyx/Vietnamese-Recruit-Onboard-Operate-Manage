"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";

import type { CurrentUser } from "@/lib/api/auth";

export type { CurrentUser } from "@/lib/api/auth";

export const currentUserQueryKey = ["current-user"] as const;

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

  const {
    data: user,
    isLoading: loading,
    error,
    refetch: refetchCurrentUser,
  } = useQuery({
    queryKey: currentUserQueryKey,
    queryFn: fetchCurrentUser,
    // User data is stable — keep fresh for 5 minutes
    staleTime: 5 * 60 * 1000,
    gcTime: 30 * 60 * 1000,
    // Don't refetch on every window focus
    refetchOnWindowFocus: false,
    refetchOnMount: false,
  });

  const refetch = async () => {
    await queryClient.invalidateQueries({
      queryKey: currentUserQueryKey,
      refetchType: "none",
    });
    await refetchCurrentUser();
  };

  return {
    user: user ?? null,
    loading,
    error: error?.message ?? null,
    refetch,
  };
}
