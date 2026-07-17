/**
 * @vitest-environment jsdom
 *
 * Tests for the ADR-0008 schedule-interview contract surfaced by
 * `ScheduleInterviewDialog`: the `start` (ISO 8601) + `duration` payload mapping
 * and the validation bounds (future start, duration 15–180, 1–10 interviewers,
 * notes ≤ 1000) that gate the confirm action.
 *
 * Validates: Requirements 1.1, 1.2
 */
import { describe, it, expect, vi, beforeAll, beforeEach } from "vitest";
import { render, screen, fireEvent, within } from "@testing-library/react";
import "@testing-library/jest-dom";

import {
  ScheduleInterviewDialog,
  type Interviewer,
  type ScheduleInterviewFormData,
} from "../schedule-interview-dialog";

// --- Polyfills for jsdom (required by Radix Dialog portal) ---
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

// A clearly-future local datetime value, in the `datetime-local` input format.
const FUTURE_LOCAL = "2099-06-15T10:30";
// Replicates the dialog's `toIsoStart` helper so the assertion is timezone-agnostic.
const FUTURE_ISO = new Date(FUTURE_LOCAL).toISOString();
const PAST_LOCAL = "2020-01-01T09:00";

function renderDialog(onConfirm: (data: ScheduleInterviewFormData) => void) {
  return render(
    <ScheduleInterviewDialog
      open
      onOpenChange={() => {}}
      onConfirm={onConfirm}
      interviewers={INTERVIEWERS}
    />,
  );
}

function setStart(value: string) {
  fireEvent.change(screen.getByLabelText("Thời gian bắt đầu"), {
    target: { value },
  });
}

function setDuration(value: string) {
  fireEvent.change(screen.getByLabelText("Thời lượng (phút)"), {
    target: { value },
  });
}

function setNotes(value: string) {
  fireEvent.change(screen.getByLabelText("Ghi chú (tùy chọn)"), {
    target: { value },
  });
}

/** Click an interviewer toggle inside the selectable list (not a chip). */
function selectInterviewer(name: string) {
  const list = screen.getByText("Người phỏng vấn (1–10)").parentElement!;
  fireEvent.click(within(list).getByRole("button", { name }));
}

function confirmButton() {
  return screen.getByRole("button", { name: CONFIRM_LABEL });
}

describe("ScheduleInterviewDialog — ADR-0008 schedule contract", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("payload mapping (Requirement 1.1)", () => {
    it("emits { start: ISO, durationMinutes, interviewerIds, notes } on confirm", () => {
      const onConfirm = vi.fn();
      renderDialog(onConfirm);

      setStart(FUTURE_LOCAL);
      setDuration("90");
      selectInterviewer("Alice Nguyen");
      selectInterviewer("Bob Tran");
      setNotes("Vòng kỹ thuật");

      expect(confirmButton()).toBeEnabled();
      fireEvent.click(confirmButton());

      expect(onConfirm).toHaveBeenCalledTimes(1);
      expect(onConfirm).toHaveBeenCalledWith({
        start: FUTURE_ISO,
        durationMinutes: 90,
        interviewerIds: ["emp-1", "emp-2"],
        notes: "Vòng kỹ thuật",
      });
    });

    it("converts the datetime-local value to an ISO 8601 string", () => {
      const onConfirm = vi.fn();
      renderDialog(onConfirm);

      setStart(FUTURE_LOCAL);
      selectInterviewer("Alice Nguyen");
      fireEvent.click(confirmButton());

      const payload = onConfirm.mock.calls[0][0] as ScheduleInterviewFormData;
      // ISO 8601 with a Z (UTC) suffix; round-trips back to the same instant.
      expect(payload.start).toBe(FUTURE_ISO);
      expect(payload.start).toMatch(
        /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$/,
      );
      expect(new Date(payload.start).toISOString()).toBe(payload.start);
    });

    it("omits notes (undefined) when the notes field is left empty", () => {
      const onConfirm = vi.fn();
      renderDialog(onConfirm);

      setStart(FUTURE_LOCAL);
      selectInterviewer("Alice Nguyen");
      fireEvent.click(confirmButton());

      const payload = onConfirm.mock.calls[0][0] as ScheduleInterviewFormData;
      expect(payload.notes).toBeUndefined();
    });

    it("defaults duration to 60 minutes when left unchanged", () => {
      const onConfirm = vi.fn();
      renderDialog(onConfirm);

      setStart(FUTURE_LOCAL);
      selectInterviewer("Alice Nguyen");
      fireEvent.click(confirmButton());

      const payload = onConfirm.mock.calls[0][0] as ScheduleInterviewFormData;
      expect(payload.durationMinutes).toBe(60);
    });
  });

  describe("validation bounds gate confirm (Requirement 1.2)", () => {
    it("blocks a start at/before now and does not call onConfirm", () => {
      const onConfirm = vi.fn();
      renderDialog(onConfirm);

      setStart(PAST_LOCAL);
      selectInterviewer("Alice Nguyen");

      expect(confirmButton()).toBeDisabled();
      fireEvent.click(confirmButton());
      expect(onConfirm).not.toHaveBeenCalled();
    });

    it("blocks a duration below the 15-minute lower bound", () => {
      const onConfirm = vi.fn();
      renderDialog(onConfirm);

      setStart(FUTURE_LOCAL);
      selectInterviewer("Alice Nguyen");
      setDuration("10");

      expect(confirmButton()).toBeDisabled();
      fireEvent.click(confirmButton());
      expect(onConfirm).not.toHaveBeenCalled();
    });

    it("accepts the 15-minute lower bound", () => {
      const onConfirm = vi.fn();
      renderDialog(onConfirm);

      setStart(FUTURE_LOCAL);
      selectInterviewer("Alice Nguyen");
      setDuration("15");

      expect(confirmButton()).toBeEnabled();
      fireEvent.click(confirmButton());
      expect(onConfirm).toHaveBeenCalledWith(
        expect.objectContaining({ durationMinutes: 15 }),
      );
    });

    it("blocks a duration above the 180-minute upper bound", () => {
      const onConfirm = vi.fn();
      renderDialog(onConfirm);

      setStart(FUTURE_LOCAL);
      selectInterviewer("Alice Nguyen");
      setDuration("181");

      expect(confirmButton()).toBeDisabled();
      fireEvent.click(confirmButton());
      expect(onConfirm).not.toHaveBeenCalled();
    });

    it("accepts the 180-minute upper bound", () => {
      const onConfirm = vi.fn();
      renderDialog(onConfirm);

      setStart(FUTURE_LOCAL);
      selectInterviewer("Alice Nguyen");
      setDuration("180");

      expect(confirmButton()).toBeEnabled();
      fireEvent.click(confirmButton());
      expect(onConfirm).toHaveBeenCalledWith(
        expect.objectContaining({ durationMinutes: 180 }),
      );
    });

    it("blocks confirm when no interviewer is selected (lower bound 1)", () => {
      const onConfirm = vi.fn();
      renderDialog(onConfirm);

      setStart(FUTURE_LOCAL);

      expect(confirmButton()).toBeDisabled();
      fireEvent.click(confirmButton());
      expect(onConfirm).not.toHaveBeenCalled();
    });

    it("blocks confirm when notes exceed 1000 characters", () => {
      const onConfirm = vi.fn();
      renderDialog(onConfirm);

      setStart(FUTURE_LOCAL);
      selectInterviewer("Alice Nguyen");
      setNotes("x".repeat(1001));

      expect(confirmButton()).toBeDisabled();
      fireEvent.click(confirmButton());
      expect(onConfirm).not.toHaveBeenCalled();
    });

    it("accepts notes at exactly the 1000-character bound", () => {
      const onConfirm = vi.fn();
      renderDialog(onConfirm);

      setStart(FUTURE_LOCAL);
      selectInterviewer("Alice Nguyen");
      setNotes("x".repeat(1000));

      expect(confirmButton()).toBeEnabled();
      fireEvent.click(confirmButton());
      expect(onConfirm).toHaveBeenCalledTimes(1);
    });
  });
});
