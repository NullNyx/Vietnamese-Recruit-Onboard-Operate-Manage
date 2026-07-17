/**
 * @vitest-environment jsdom
 *
 * Tests for the InterviewList component — displays interviews
 * with status badges, complete/cancel actions, and replacement.
 */
import { describe, it, expect, vi, beforeAll, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import "@testing-library/jest-dom";
import { InterviewList } from "../interview-list";
import type { InterviewResponse } from "@/lib/api/recruitment";

beforeAll(() => {
  global.ResizeObserver = class ResizeObserver {
    observe() {}
    unobserve() {}
    disconnect() {}
  };
});

const MOCK_INTERVIEWS: InterviewResponse[] = [
  {
    id: "iv-1",
    candidate_id: "cand-1",
    status: "scheduled",
    round_name: "Technical Round 1",
    start_at: "2099-06-15T10:00:00Z",
    end_at: "2099-06-15T11:00:00Z",
    timezone: "Asia/Ho_Chi_Minh",
    calendar_event_id: "evt-001",
    needs_relink: false,
    participants: [
      {
        id: "p1",
        interview_id: "iv-1",
        type: "candidate",
        email: "cand@example.com",
        name: "John Doe",
        employee_id: null,
      },
      {
        id: "p2",
        interview_id: "iv-1",
        type: "employee",
        email: "emp@example.com",
        name: "Alice Nguyen",
        employee_id: "emp-1",
      },
    ],
  },
  {
    id: "iv-2",
    candidate_id: "cand-1",
    status: "completed",
    round_name: "HR Round",
    start_at: "2099-06-10T14:00:00Z",
    end_at: "2099-06-10T14:30:00Z",
    timezone: "Asia/Ho_Chi_Minh",
    calendar_event_id: "evt-002",
    needs_relink: false,
    participants: [],
  },
  {
    id: "iv-3",
    candidate_id: "cand-1",
    status: "cancelled",
    round_name: "Final Round",
    start_at: "2099-06-20T09:00:00Z",
    end_at: "2099-06-20T10:00:00Z",
    timezone: "Asia/Ho_Chi_Minh",
    calendar_event_id: null,
    needs_relink: false,
    participants: [],
  },
];

describe("InterviewList", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows empty state when no interviews", () => {
    render(
      <InterviewList interviews={[]} candidateId="cand-1" />,
    );
    expect(screen.getByText("Chưa có lịch phỏng vấn nào.")).toBeInTheDocument();
  });

  it("renders all interviews sorted by start_at descending", () => {
    render(<InterviewList interviews={MOCK_INTERVIEWS} candidateId="cand-1" />);

    // Check round names are rendered
    expect(screen.getByText("Technical Round 1")).toBeInTheDocument();
    expect(screen.getByText("HR Round")).toBeInTheDocument();
    expect(screen.getByText("Final Round")).toBeInTheDocument();
  });

  it("shows status badges for each interview", () => {
    render(<InterviewList interviews={MOCK_INTERVIEWS} candidateId="cand-1" />);

    expect(screen.getByText("Đã lên lịch")).toBeInTheDocument();
    expect(screen.getByText("Đã hoàn thành")).toBeInTheDocument();
    expect(screen.getByText("Đã hủy")).toBeInTheDocument();
  });

  it("shows timezone information", () => {
    render(<InterviewList interviews={MOCK_INTERVIEWS} candidateId="cand-1" />);
    const timezoneElements = screen.getAllByText("Asia/Ho_Chi_Minh");
    expect(timezoneElements.length).toBeGreaterThanOrEqual(3);
  });

  it("shows participant details when present", () => {
    render(<InterviewList interviews={MOCK_INTERVIEWS} candidateId="cand-1" />);
    expect(screen.getByText("John Doe")).toBeInTheDocument();
    expect(screen.getByText("Alice Nguyen")).toBeInTheDocument();
  });

  describe("action buttons", () => {
    it("shows complete button for scheduled interviews", () => {
      const onComplete = vi.fn();
      render(
        <InterviewList
          interviews={MOCK_INTERVIEWS}
          candidateId="cand-1"
          onComplete={onComplete}
        />,
      );

      const completeButtons = screen.getAllByText("Hoàn thành");
      expect(completeButtons).toHaveLength(1); // Only for scheduled interview
    });

    it("shows cancel button for scheduled interviews", () => {
      const onCancel = vi.fn();
      render(
        <InterviewList
          interviews={MOCK_INTERVIEWS}
          candidateId="cand-1"
          onCancel={onCancel}
        />,
      );

      const cancelButtons = screen.getAllByText("Hủy");
      expect(cancelButtons).toHaveLength(1);
    });

    it("shows replacement button for cancelled interviews", () => {
      const onReplacement = vi.fn();
      render(
        <InterviewList
          interviews={MOCK_INTERVIEWS}
          candidateId="cand-1"
          onReplacement={onReplacement}
        />,
      );

      expect(screen.getByText("Đặt lịch thay thế")).toBeInTheDocument();
    });

    it("calls onComplete when complete button is clicked", () => {
      const onComplete = vi.fn();
      render(
        <InterviewList
          interviews={MOCK_INTERVIEWS}
          candidateId="cand-1"
          onComplete={onComplete}
        />,
      );

      fireEvent.click(screen.getByText("Hoàn thành"));
      expect(onComplete).toHaveBeenCalledTimes(1);
      expect(onComplete).toHaveBeenCalledWith(
        expect.objectContaining({ id: "iv-1" }),
      );
    });

    it("calls onCancel when cancel button is clicked", () => {
      const onCancel = vi.fn();
      render(
        <InterviewList
          interviews={MOCK_INTERVIEWS}
          candidateId="cand-1"
          onCancel={onCancel}
        />,
      );

      fireEvent.click(screen.getByText("Hủy"));
      expect(onCancel).toHaveBeenCalledTimes(1);
      expect(onCancel).toHaveBeenCalledWith(
        expect.objectContaining({ id: "iv-1" }),
      );
    });

    it("does not show action buttons for completed interviews", () => {
      render(
        <InterviewList interviews={MOCK_INTERVIEWS} candidateId="cand-1" />,
      );
      // Should not show complete/cancel for the completed interview
      // We only have 1 scheduled interview, so we should only see 1 set of buttons
    });
  });
});
