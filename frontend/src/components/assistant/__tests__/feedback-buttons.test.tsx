/**
 * @vitest-environment jsdom
 */
import "@testing-library/jest-dom";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { FeedbackButtons } from "../feedback-buttons";

describe("FeedbackButtons", () => {
  const defaultProps = {
    messageIndex: 0,
    sessionId: "test-session",
    onFeedback: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders thumbs up and thumbs down buttons", () => {
    render(<FeedbackButtons {...defaultProps} />);

    expect(screen.getByLabelText("Thumbs up")).toBeInTheDocument();
    expect(screen.getByLabelText("Thumbs down")).toBeInTheDocument();
  });

  it("calls onFeedback with 'up' when thumbs up is clicked", async () => {
    const onFeedback = vi.fn().mockResolvedValue(undefined);
    render(<FeedbackButtons {...defaultProps} onFeedback={onFeedback} />);

    fireEvent.click(screen.getByLabelText("Thumbs up"));

    await waitFor(() => {
      expect(onFeedback).toHaveBeenCalledWith(0, "up");
    });
  });

  it("shows 'Đã đánh giá' after thumbs up is clicked", async () => {
    const onFeedback = vi.fn().mockResolvedValue(undefined);
    render(<FeedbackButtons {...defaultProps} onFeedback={onFeedback} />);

    fireEvent.click(screen.getByLabelText("Thumbs up"));

    await waitFor(() => {
      expect(screen.getByText("Đã đánh giá")).toBeInTheDocument();
    });
  });

  it("disables buttons after feedback is submitted", async () => {
    const onFeedback = vi.fn().mockResolvedValue(undefined);
    render(<FeedbackButtons {...defaultProps} onFeedback={onFeedback} />);

    fireEvent.click(screen.getByLabelText("Thumbs up"));

    await waitFor(() => {
      expect(screen.getByLabelText("Thumbs up")).toBeDisabled();
      expect(screen.getByLabelText("Thumbs down")).toBeDisabled();
    });
  });

  it("shows text input when thumbs down is clicked", () => {
    render(<FeedbackButtons {...defaultProps} />);

    fireEvent.click(screen.getByLabelText("Thumbs down"));

    expect(
      screen.getByPlaceholderText("Phản hồi thêm (không bắt buộc)..."),
    ).toBeInTheDocument();
  });

  it("calls onFeedback with 'down' when thumbs down text is submitted", async () => {
    const onFeedback = vi.fn().mockResolvedValue(undefined);
    render(<FeedbackButtons {...defaultProps} onFeedback={onFeedback} />);

    fireEvent.click(screen.getByLabelText("Thumbs down"));
    expect(
      screen.getByPlaceholderText("Phản hồi thêm (không bắt buộc)..."),
    ).toBeInTheDocument();

    fireEvent.click(screen.getByText("Gửi"));

    await waitFor(() => {
      expect(onFeedback).toHaveBeenCalledWith(0, "down", undefined);
    });
  });

  it("calls onFeedback with 'down' and text when text is filled and submitted", async () => {
    const onFeedback = vi.fn().mockResolvedValue(undefined);
    render(<FeedbackButtons {...defaultProps} onFeedback={onFeedback} />);

    fireEvent.click(screen.getByLabelText("Thumbs down"));

    const textarea = screen.getByPlaceholderText(
      "Phản hồi thêm (không bắt buộc)...",
    );
    fireEvent.change(textarea, { target: { value: "Not helpful" } });

    fireEvent.click(screen.getByText("Gửi"));

    await waitFor(() => {
      expect(onFeedback).toHaveBeenCalledWith(0, "down", "Not helpful");
    });
  });
});
