/**
 * @vitest-environment jsdom
 */
import "@testing-library/jest-dom";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { DraftActionCard } from "../draft-action-card";
import { confirmDraftAction } from "@/lib/api/assistant";
import { toast } from "sonner";

// Mock dependencies
vi.mock("@/lib/api/assistant", () => ({
  confirmDraftAction: vi.fn(),
}));

vi.mock("sonner", () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}));

const mockDraft = {
  action_type: "send_email",
  preview: "Gửi thư báo trúng tuyển đến test@example.com",
  parameters: {},
  confirm_endpoint: "/api/test",
  confirm_method: "POST",
  confirm_body: {},
};

describe("DraftActionCard", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders the draft action preview", () => {
    render(<DraftActionCard draft={mockDraft} />);
    expect(screen.getByText(/Draft Action — send_email/)).toBeInTheDocument();
    expect(screen.getByText("Gửi thư báo trúng tuyển đến test@example.com")).toBeInTheDocument();
  });

  it("renders leave draft with correct title", () => {
    const leaveDraft = { ...mockDraft, action_type: "submit_leave_request" };
    render(<DraftActionCard draft={leaveDraft} />);
    expect(screen.getByText(/Draft — Đơn nghỉ phép/)).toBeInTheDocument();
  });

  it("renders overtime draft with correct title", () => {
    const otDraft = { ...mockDraft, action_type: "submit_overtime_request" };
    render(<DraftActionCard draft={otDraft} />);
    expect(screen.getByText(/Draft — Đơn tăng ca/)).toBeInTheDocument();
  });

  it("calls onDismissed when Cancel is clicked", () => {
    const handleDismiss = vi.fn();
    render(<DraftActionCard draft={mockDraft} onDismissed={handleDismiss} />);
    
    fireEvent.click(screen.getByText("Hủy"));
    expect(handleDismiss).toHaveBeenCalledTimes(1);
  });

  it("calls onConfirmed directly when provided (prefill mode)", () => {
    const handleConfirmed = vi.fn();
    render(<DraftActionCard draft={mockDraft} onConfirmed={handleConfirmed} />);
    
    fireEvent.click(screen.getByText("Xác nhận"));
    
    // Prefill mode: onConfirmed is called directly, never confirmDraftAction
    expect(handleConfirmed).toHaveBeenCalledTimes(1);
    expect(confirmDraftAction).not.toHaveBeenCalled();
  });

  it("falls through to confirmDraftAction when onConfirmed is not provided", async () => {
    vi.mocked(confirmDraftAction).mockResolvedValueOnce({ status: "ok" });

    render(<DraftActionCard draft={mockDraft} />);
    
    fireEvent.click(screen.getByText("Xác nhận"));
    
    expect(confirmDraftAction).toHaveBeenCalledWith(mockDraft);
    
    await waitFor(() => {
      expect(toast.success).toHaveBeenCalledWith("Đã gửi thành công!");
    });
  });

  it("shows custom confirm label", () => {
    render(<DraftActionCard draft={mockDraft} confirmLabel="Mở form" />);
    expect(screen.getByText("Mở form")).toBeInTheDocument();
  });

  it("shows error toast if confirmation fails", async () => {
    vi.mocked(confirmDraftAction).mockRejectedValueOnce(new Error("API Error"));

    render(<DraftActionCard draft={mockDraft} />);
    
    fireEvent.click(screen.getByText("Xác nhận"));
    
    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith("Gửi thất bại: API Error");
      expect(screen.getByText("Xác nhận")).toBeInTheDocument();
    });
  });
});
