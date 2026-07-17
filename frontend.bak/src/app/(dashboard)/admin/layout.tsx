"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { Shield } from "lucide-react";

import { useCurrentUser } from "@/hooks/use-current-user";
import type { CurrentUser } from "@/hooks/use-current-user";

function readE2EOverride(): CurrentUser | null {
  if (typeof window === "undefined") return null;
  try {
    return (window as typeof window & {
      __VROOM_HR_E2E_CURRENT_USER__?: CurrentUser;
    }).__VROOM_HR_E2E_CURRENT_USER__ ?? null;
  } catch {
    return null;
  }
}

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { user, loading } = useCurrentUser();
  const router = useRouter();
  // In E2E tests, the user is injected via addInitScript and is available
  // synchronously on the client, but not during SSR. Reading it here prevents
  // a catastrophic hydration mismatch where SSR shows a loading spinner
  // while the client immediately shows the real content (e.g. assistant page).
  const e2eUser = readE2EOverride();
  const effectiveUser = e2eUser ?? user;
  const effectiveLoading = e2eUser ? false : loading;

  useEffect(() => {
    if (!effectiveLoading && effectiveUser && effectiveUser.role !== "admin") {
      router.replace("/");
    }
  }, [effectiveUser, effectiveLoading, router]);

  // Show loading state while checking role
  if (effectiveLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="flex flex-col items-center gap-3 text-muted-foreground">
          <Shield className="h-8 w-8 animate-pulse" aria-hidden="true" />
          <p className="text-sm">Đang kiểm tra quyền truy cập...</p>
        </div>
      </div>
    );
  }

  // If not admin, show nothing while redirecting
  if (!effectiveUser || effectiveUser.role !== "admin") {
    return null;
  }

  return <>{children}</>;
}
