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

  it("calls onDismissed when Cancel is clicked", () => {
    const handleDismiss = vi.fn();
    render(<DraftActionCard draft={mockDraft} onDismissed={handleDismiss} />);
    
    fireEvent.click(screen.getByText("Hủy"));
    expect(handleDismiss).toHaveBeenCalledTimes(1);
  });

  it("calls confirmDraftAction and shows success on confirm", async () => {
    const handleConfirmed = vi.fn();
    vi.mocked(confirmDraftAction).mockResolvedValueOnce({ status: "ok" });

    render(<DraftActionCard draft={mockDraft} onConfirmed={handleConfirmed} />);
    
    fireEvent.click(screen.getByText("Xác nhận"));
    
    expect(confirmDraftAction).toHaveBeenCalledWith(mockDraft);
    
    await waitFor(() => {
      expect(toast.success).toHaveBeenCalledWith("Đã gửi thành công!");
      expect(handleConfirmed).toHaveBeenCalledTimes(1);
      expect(screen.getByText("Đã xác nhận và gửi thành công.")).toBeInTheDocument();
    });
  });

  it("shows error toast if confirmation fails", async () => {
    const handleConfirmed = vi.fn();
    vi.mocked(confirmDraftAction).mockRejectedValueOnce(new Error("API Error"));

    render(<DraftActionCard draft={mockDraft} onConfirmed={handleConfirmed} />);
    
    fireEvent.click(screen.getByText("Xác nhận"));
    
    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith("Gửi thất bại: API Error");
      expect(handleConfirmed).not.toHaveBeenCalled();
      // Should still show confirm button, not success state
      expect(screen.getByText("Xác nhận")).toBeInTheDocument();
    });
  });
});
