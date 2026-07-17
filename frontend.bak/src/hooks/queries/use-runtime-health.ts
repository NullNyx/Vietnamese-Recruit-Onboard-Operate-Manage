"use client";

import { useQuery } from "@tanstack/react-query";

import { getRuntimeHealth, type RuntimeHealthResponse } from "@/lib/api/admin";

export const runtimeHealthKeys = {
  health: ["admin", "runtime", "health"] as const,
};

export function useRuntimeHealth() {
  return useQuery<RuntimeHealthResponse>({
    queryKey: runtimeHealthKeys.health,
    queryFn: getRuntimeHealth,
    staleTime: 30 * 1000,
    refetchInterval: 60 * 1000,
  });
}
