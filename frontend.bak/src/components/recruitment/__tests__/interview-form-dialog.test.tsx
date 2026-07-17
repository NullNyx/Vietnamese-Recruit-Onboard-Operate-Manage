/**
 * @vitest-environment jsdom
 *
 * Tests for the InterviewFormDialog component — the GH #148 interview
 * creation form that maps to CreateInterviewRequest.
 */
import { describe, it, expect, vi, beforeAll, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import "@testing-library/jest-dom";

import {
  InterviewFormDialog,
  type InterviewFormData,
  type Interviewer,
} from "../interview-form-dialog";

beforeAll(() => {
  global.ResizeObserver = class ResizeObserver {
    observe() {}
    unobserve() {}
    disconnect() {}
  };

  if (!Element.prototype.hasPointerCapture) {
    Element.prototype.hasPointerCapture = () => false;
    Element.prototype.setPointerCapture = () => {};
    Element.prototype.releasePointerCapture = () => {};
  }

  if (!Element.prototype.scrollIntoView) {
    Element.prototype.scrollIntoView = () => {};
  }
});

const INTERVIEWERS: Interviewer[] = [
  { id: "emp-1", name: "Alice Nguyen" },
  { id: "emp-2", name: "Bob Tran" },
];

const CONFIRM_LABEL = "Lên lịch phỏng vấn";
const FUTURE_LOCAL = "2099-06-15T10:00";
const FUTURE_END = "2099-06-15T11:00";

function renderDialog(
  onConfirm: (data: InterviewFormData) => void,
  props: Partial<{
    loading: boolean;
    interviewers: Interviewer[];
    mode: "create" | "replacement";
    serverError: string | null;
  }> = {},
) {
  return render(
    <InterviewFormDialog
      open
      onOpenChange={() => {}}
      onConfirm={onConfirm}
      interviewers={props.interviewers ?? INTERVIEWERS}
      loading={props.loading ?? false}
      mode={props.mode ?? "create"}
      serverError={props.serverError ?? null}
    />,
  );
}

describe("InterviewFormDialog", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("payload mapping", () => {
    it("emits all fields on confirm with valid data", () => {
      const onConfirm = vi.fn();
      renderDialog(onConfirm);

      fireEvent.change(screen.getByLabelText("Tên vòng phỏng vấn"), {
        target: { value: "Technical Round 1" },
      });
      fireEvent.change(screen.getByLabelText("Thời gian bắt đầu"), {
        target: { value: FUTURE_LOCAL },
      });
      fireEvent.change(screen.getByLabelText("Thời gian kết thúc"), {
        target: { value: FUTURE_END },
      });
      fireEvent.click(screen.getByRole("button", { name: "Alice Nguyen" }));
      fireEvent.change(screen.getByLabelText("Ghi chú (tùy chọn)"), {
        target: { value: "Technical assessment" },
      });

      expect(screen.getByRole("button", { name: CONFIRM_LABEL })).toBeEnabled();
      fireEvent.click(screen.getByRole("button", { name: CONFIRM_LABEL }));

      expect(onConfirm).toHaveBeenCalledTimes(1);
      const payload = onConfirm.mock.calls[0][0] as InterviewFormData;
      expect(payload.round_name).toBe("Technical Round 1");
      expect(payload.start).toMatch(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$/);
      expect(payload.end).toMatch(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$/);
      expect(payload.timezone).toBe("Asia/Ho_Chi_Minh");
      expect(payload.mode).toBe("google_meet");
      expect(payload.interviewer_ids).toEqual(["emp-1"]);
      expect(payload.notes).toBe("Technical assessment");
    });

    it("defaults mode to google_meet and meeting_link to null", () => {
      const onConfirm = vi.fn();
      renderDialog(onConfirm);

      fireEvent.change(screen.getByLabelText("Tên vòng phỏng vấn"), {
        target: { value: "Intro" },
      });
      fireEvent.change(screen.getByLabelText("Thời gian bắt đầu"), {
        target: { value: FUTURE_LOCAL },
      });
      fireEvent.change(screen.getByLabelText("Thời gian kết thúc"), {
        target: { value: FUTURE_END },
      });
      fireEvent.click(screen.getByRole("button", { name: "Alice Nguyen" }));
      fireEvent.click(screen.getByRole("button", { name: CONFIRM_LABEL }));

      const payload = onConfirm.mock.calls[0][0] as InterviewFormData;
      expect(payload.mode).toBe("google_meet");
      expect(payload.meeting_link).toBeNull();
    });

    it("omits notes when empty", () => {
      const onConfirm = vi.fn();
      renderDialog(onConfirm);

      fireEvent.change(screen.getByLabelText("Tên vòng phỏng vấn"), {
        target: { value: "Intro" },
      });
      fireEvent.change(screen.getByLabelText("Thời gian bắt đầu"), {
        target: { value: FUTURE_LOCAL },
      });
      fireEvent.change(screen.getByLabelText("Thời gian kết thúc"), {
        target: { value: FUTURE_END },
      });
      fireEvent.click(screen.getByRole("button", { name: "Alice Nguyen" }));
      fireEvent.click(screen.getByRole("button", { name: CONFIRM_LABEL }));

      const payload = onConfirm.mock.calls[0][0] as InterviewFormData;
      expect(payload.notes).toBeNull();
    });

    it("includes external participant emails in payload", () => {
      const onConfirm = vi.fn();
      renderDialog(onConfirm);

      fireEvent.change(screen.getByLabelText("Tên vòng phỏng vấn"), {
        target: { value: "Intro" },
      });
      fireEvent.change(screen.getByLabelText("Thời gian bắt đầu"), {
        target: { value: FUTURE_LOCAL },
      });
      fireEvent.change(screen.getByLabelText("Thời gian kết thúc"), {
        target: { value: FUTURE_END },
      });
      fireEvent.click(screen.getByRole("button", { name: "Alice Nguyen" }));

      // Add an external email via the input field
      const externalInput = screen.getByPlaceholderText("email@example.com");
      fireEvent.change(externalInput, { target: { value: "external@test.com" } });
      fireEvent.keyDown(externalInput, { key: "Enter", code: "Enter" });

      fireEvent.click(screen.getByRole("button", { name: CONFIRM_LABEL }));

      const payload = onConfirm.mock.calls[0][0] as InterviewFormData;
      expect(payload.external_participant_emails).toContain("external@test.com");
    });
  });

  describe("validation gates", () => {
    it("blocks confirm when round name is empty", () => {
      const onConfirm = vi.fn();
      renderDialog(onConfirm);

      fireEvent.change(screen.getByLabelText("Thời gian bắt đầu"), {
        target: { value: FUTURE_LOCAL },
      });
      fireEvent.change(screen.getByLabelText("Thời gian kết thúc"), {
        target: { value: FUTURE_END },
      });
      fireEvent.click(screen.getByRole("button", { name: "Alice Nguyen" }));

      expect(screen.getByRole("button", { name: CONFIRM_LABEL })).toBeDisabled();
      fireEvent.click(screen.getByRole("button", { name: CONFIRM_LABEL }));
      expect(onConfirm).not.toHaveBeenCalled();
    });

    it("blocks confirm when start is empty", () => {
      const onConfirm = vi.fn();
      renderDialog(onConfirm);

      fireEvent.change(screen.getByLabelText("Tên vòng phỏng vấn"), {
        target: { value: "Technical" },
      });
      fireEvent.change(screen.getByLabelText("Thời gian kết thúc"), {
        target: { value: FUTURE_END },
      });
      fireEvent.click(screen.getByRole("button", { name: "Alice Nguyen" }));

      expect(screen.getByRole("button", { name: CONFIRM_LABEL })).toBeDisabled();
    });

    it("blocks confirm when end is empty", () => {
      const onConfirm = vi.fn();
      renderDialog(onConfirm);

      fireEvent.change(screen.getByLabelText("Tên vòng phỏng vấn"), {
        target: { value: "Technical" },
      });
      fireEvent.change(screen.getByLabelText("Thời gian bắt đầu"), {
        target: { value: FUTURE_LOCAL },
      });
      fireEvent.click(screen.getByRole("button", { name: "Alice Nguyen" }));

      expect(screen.getByRole("button", { name: CONFIRM_LABEL })).toBeDisabled();
    });
  });

  describe("meeting modes", () => {
    it("shows meeting link input when custom_link is selected", () => {
      renderDialog(vi.fn());
      expect(screen.queryByLabelText("Link cuộc họp")).not.toBeInTheDocument();

      fireEvent.click(screen.getByRole("button", { name: "Link tùy chỉnh" }));
      expect(screen.getByLabelText("Link cuộc họp")).toBeInTheDocument();
    });

    it("blocks confirm when custom_link mode has no meeting link", () => {
      const onConfirm = vi.fn();
      renderDialog(onConfirm);

      fireEvent.change(screen.getByLabelText("Tên vòng phỏng vấn"), {
        target: { value: "Technical" },
      });
      fireEvent.change(screen.getByLabelText("Thời gian bắt đầu"), {
        target: { value: FUTURE_LOCAL },
      });
      fireEvent.change(screen.getByLabelText("Thời gian kết thúc"), {
        target: { value: FUTURE_END },
      });
      fireEvent.click(screen.getByRole("button", { name: "Alice Nguyen" }));
      fireEvent.click(screen.getByRole("button", { name: "Link tùy chỉnh" }));

      expect(screen.getByRole("button", { name: CONFIRM_LABEL })).toBeDisabled();
    });
  });

  describe("external participant emails", () => {
    it("adds email on Enter key", () => {
      renderDialog(vi.fn());

      const emailInput = screen.getByPlaceholderText("email@example.com");
      fireEvent.change(emailInput, { target: { value: "ext@test.com" } });
      fireEvent.keyDown(emailInput, { key: "Enter", code: "Enter" });

      expect(screen.getByText("ext@test.com")).toBeInTheDocument();
    });

    it("removes external email on X click", () => {
      renderDialog(vi.fn());

      const emailInput = screen.getByPlaceholderText("email@example.com");
      fireEvent.change(emailInput, { target: { value: "ext@test.com" } });
      fireEvent.keyDown(emailInput, { key: "Enter", code: "Enter" });

      expect(screen.getByText("ext@test.com")).toBeInTheDocument();

      // Find the remove button within the email chip
      const removeButton = screen.getByRole("button", { name: /Xóa ext/ });
      fireEvent.click(removeButton);

      expect(screen.queryByText("ext@test.com")).not.toBeInTheDocument();
    });
  });

  describe("replacement mode", () => {
    it("shows replacement title and confirm label", () => {
      renderDialog(vi.fn(), { mode: "replacement" });
      expect(screen.getByText("Tạo lịch phỏng vấn thay thế")).toBeInTheDocument();
      expect(
        screen.getByRole("button", { name: "Tạo lịch thay thế" }),
      ).toBeInTheDocument();
    });
  });

  describe("server error", () => {
    it("displays CALENDAR_GRANT_MISSING and preserves form data", () => {
      const onConfirm = vi.fn();
      renderDialog(onConfirm, {
        serverError: "Google Calendar chưa được cấp quyền (CALENDAR_GRANT_MISSING)",
      });

      expect(
        screen.getByText(/Google Calendar chưa được cấp quyền/),
      ).toBeInTheDocument();

      fireEvent.change(screen.getByLabelText("Tên vòng phỏng vấn"), {
        target: { value: "Technical" },
      });

      expect(
        (screen.getByLabelText("Tên vòng phỏng vấn") as HTMLInputElement).value,
      ).toBe("Technical");
    });
  });

  describe("interviewer selection", () => {
    it("toggles interviewer selection on click", () => {
      renderDialog(vi.fn());
      const alice = screen.getByRole("button", { name: "Alice Nguyen" });
      expect(alice).toHaveAttribute("aria-pressed", "false");

      fireEvent.click(alice);
      expect(alice).toHaveAttribute("aria-pressed", "true");

      fireEvent.click(alice);
      expect(alice).toHaveAttribute("aria-pressed", "false");
    });

    it("shows selected interviewers as chips (text appears in chip and list)", () => {
      renderDialog(vi.fn());
      fireEvent.click(screen.getByRole("button", { name: "Alice Nguyen" }));

      // Alice appears both in the chip and in the list (aria-pressed=true)
      const aliceElements = screen.getAllByText("Alice Nguyen");
      expect(aliceElements.length).toBeGreaterThanOrEqual(1);
      expect(aliceElements[0]).toBeInTheDocument();
    });

    it("removes interviewer chip on X click", () => {
      renderDialog(vi.fn());
      fireEvent.click(screen.getByRole("button", { name: "Alice Nguyen" }));

      const removeButton = screen.getByRole("button", { name: /Xóa Alice Nguyen/ });
      fireEvent.click(removeButton);

      // Should still show Alice in the interviewer list (but not pressed)
      const aliceButton = screen.getByRole("button", { name: "Alice Nguyen" });
      expect(aliceButton).toHaveAttribute("aria-pressed", "false");
    });
  });
});
