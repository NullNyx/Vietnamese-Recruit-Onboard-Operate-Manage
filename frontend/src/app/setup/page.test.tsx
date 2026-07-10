/**
 * @vitest-environment jsdom
 */
import "@testing-library/jest-dom";
import { render, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const { replace, getSetupStatus } = vi.hoisted(() => ({
  replace: vi.fn(),
  getSetupStatus: vi.fn(),
}));

vi.mock("next/navigation", () => ({ useRouter: () => ({ replace }) }));
vi.mock("@/hooks/use-current-user", () => ({
  useCurrentUser: () => ({ user: null, loading: false, refetch: vi.fn() }),
}));
vi.mock("@/lib/api/auth", () => ({
  getSetupStatus,
  setupFirstRun: vi.fn(),
}));

import SetupPage from "./page";

describe("SetupPage", () => {
  beforeEach(() => {
    replace.mockReset();
    getSetupStatus.mockReset();
  });

  it("redirects completed deployments to login", async () => {
    getSetupStatus.mockResolvedValue({ setup_complete: true });

    render(<SetupPage />);

    await waitFor(() => expect(replace).toHaveBeenCalledWith("/login"));
  });
});
