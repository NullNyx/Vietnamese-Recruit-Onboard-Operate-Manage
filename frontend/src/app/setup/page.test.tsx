/**
 * @vitest-environment jsdom
 */
import "@testing-library/jest-dom";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const { replace, getSetupStatus, setupFirstRun, refetch } = vi.hoisted(() => ({
  replace: vi.fn(),
  getSetupStatus: vi.fn(),
  setupFirstRun: vi.fn(),
  refetch: vi.fn(),
}));

vi.mock("next/navigation", () => ({ useRouter: () => ({ replace }) }));
vi.mock("@/hooks/use-current-user", () => ({
  useCurrentUser: () => ({ user: null, loading: false, refetch }),
}));
vi.mock("@/lib/api/auth", () => ({
  getSetupStatus,
  setupFirstRun,
  AuthApiError: class AuthApiError extends Error {
    code?: string;
    fields: Record<string, string>;
    constructor(message: string, code?: string, fields: Record<string, string> = {}) {
      super(message);
      this.code = code;
      this.fields = fields;
    }
  },
}));

import SetupPage from "./page";

describe("SetupPage", () => {
  afterEach(() => cleanup());
  beforeEach(() => {
    replace.mockReset();
    getSetupStatus.mockReset();
    setupFirstRun.mockReset();
    refetch.mockReset().mockResolvedValue(undefined);
  });

  it("redirects completed deployments to login", async () => {
    getSetupStatus.mockResolvedValue({ setup_complete: true });
    render(<SetupPage />);
    await waitFor(() => expect(replace).toHaveBeenCalledWith("/login"));
  });

  it("does not show the form when status is unavailable and retries", async () => {
    getSetupStatus.mockRejectedValueOnce(new Error("offline")).mockResolvedValueOnce({ setup_complete: false });
    render(<SetupPage />);
    expect(await screen.findByRole("button", { name: "Thử lại" })).toBeInTheDocument();
    expect(screen.queryByLabelText("Tên Organization")).not.toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Thử lại" }));
    expect(await screen.findByLabelText("Tên Organization")).toBeInTheDocument();
  });

  it("keeps non-sensitive values while moving through the review step", async () => {
    getSetupStatus.mockResolvedValue({ setup_complete: false });
    render(<SetupPage />);
    const user = userEvent.setup();
    const organization = await screen.findByLabelText("Tên Organization");
    await user.type(organization, "Công ty ABC");
    await user.click(screen.getByRole("button", { name: "Tiếp tục" }));
    await user.type(screen.getByLabelText("Họ tên HR"), "Nguyễn Văn A");
    await user.type(screen.getByLabelText("Email HR"), "hr@abc.vn");
    await user.type(screen.getByLabelText("Mật khẩu"), "a-secure-password");
    await user.type(screen.getByLabelText("Xác nhận mật khẩu"), "a-secure-password");
    await user.click(screen.getByRole("button", { name: "Xem lại thiết lập" }));
    expect(await screen.findByText("Công ty ABC")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Quay lại" }));
    expect(screen.getByLabelText("Họ tên HR")).toHaveValue("Nguyễn Văn A");
    expect(screen.getByLabelText("Email HR")).toHaveValue("hr@abc.vn");
    expect(screen.getByLabelText("Mật khẩu")).toHaveValue("a-secure-password");
  });

  it("blocks invalid confirmation and shows a field error", async () => {
    getSetupStatus.mockResolvedValue({ setup_complete: false });
    render(<SetupPage />);
    await screen.findByLabelText("Tên Organization");
    fireEvent.change(screen.getByLabelText("Tên Organization"), { target: { value: "ABC" } });
    fireEvent.click(screen.getByRole("button", { name: "Tiếp tục" }));
    await waitFor(() => expect(screen.getByLabelText("Họ tên HR")).toBeInTheDocument());
    fireEvent.change(screen.getByLabelText("Họ tên HR"), { target: { value: "HR" } });
    fireEvent.change(screen.getByLabelText("Email HR"), { target: { value: "hr@abc.vn" } });
    fireEvent.change(screen.getByLabelText("Mật khẩu"), { target: { value: "a-secure-password" } });
    fireEvent.change(screen.getByLabelText("Xác nhận mật khẩu"), { target: { value: "different-password" } });
    fireEvent.click(screen.getByRole("button", { name: "Xem lại thiết lập" }));
    expect(await screen.findByText("Mật khẩu xác nhận không khớp")).toBeInTheDocument();
    expect(setupFirstRun).not.toHaveBeenCalled();
  });

  it("shows success and offers an explicit dashboard action", async () => {
    getSetupStatus.mockResolvedValue({ setup_complete: false });
    setupFirstRun.mockResolvedValue({ user: { role: "admin" } });
    render(<SetupPage />);
    const user = userEvent.setup();
    await user.type(await screen.findByLabelText("Tên Organization"), "ABC");
    await user.click(screen.getByRole("button", { name: "Tiếp tục" }));
    await user.type(screen.getByLabelText("Họ tên HR"), "HR");
    await user.type(screen.getByLabelText("Email HR"), "hr@abc.vn");
    await user.type(screen.getByLabelText("Mật khẩu"), "a-secure-password");
    await user.type(screen.getByLabelText("Xác nhận mật khẩu"), "a-secure-password");
    await user.click(screen.getByRole("button", { name: "Xem lại thiết lập" }));
    await user.click(screen.getByRole("button", { name: "Hoàn tất thiết lập" }));
    expect(await screen.findByRole("heading", { name: "Thiết lập thành công" })).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Mở dashboard" }));
    expect(replace).toHaveBeenCalledWith("/");
  });
});
