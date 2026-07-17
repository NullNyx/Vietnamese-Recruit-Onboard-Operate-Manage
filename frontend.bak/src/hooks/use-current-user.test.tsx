import { act, renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { afterEach, describe, expect, it, vi } from "vitest";

import { useCurrentUser } from "./use-current-user";

const user = {
  id: "user-1",
  email: "hr@example.com",
  name: "HR User",
  avatar_url: null,
  employee_id: null,
  role: "admin" as const,
  must_change_password: false,
  gmail_grant_valid: false,
  calendar_grant_valid: false,
  created_at: "2026-01-01T00:00:00Z",
  last_login: "2026-01-01T00:00:00Z",
};

afterEach(() => {
  vi.restoreAllMocks();
});

describe("useCurrentUser", () => {
  it("refetches the user after authentication updates the session", async () => {
    let authenticated = false;
    vi.stubGlobal(
      "fetch",
      vi.fn(() =>
        Promise.resolve(
          authenticated
            ? new Response(JSON.stringify(user), { status: 200 })
            : new Response(null, { status: 401 }),
        ),
      ),
    );

    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );

    const { result } = renderHook(() => useCurrentUser(), { wrapper });
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.user).toBeNull();

    authenticated = true;
    await act(async () => {
      await result.current.refetch();
    });

    await waitFor(() => expect(result.current.user).toEqual(user));
  });
});
