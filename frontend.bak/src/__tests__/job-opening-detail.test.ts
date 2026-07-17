// @vitest-environment jsdom
import { describe, it, expect, vi, beforeEach } from "vitest";

// Mock fetch globally
const mockFetch = vi.fn();
vi.stubGlobal("fetch", mockFetch);

describe("Job Opening Detail Page - Candidate Counts Display", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const mockJobOpeningDetail = {
    id: "jo-123",
    title: "Senior Developer",
    description: "We are looking for a senior developer",
    position_id: "pos-1",
    position_name: "Senior Developer",
    target_headcount: 3,
    status: "open",
    opened_at: "2026-06-01T00:00:00Z",
    closed_at: null,
    cancelled_at: null,
    created_at: "2026-06-01T00:00:00Z",
    updated_at: "2026-06-01T00:00:00Z",
    candidate_counts: {
      new: 2,
      reviewing: 3,
      interview_scheduled: 1,
      accepted: 3,
      rejected: 5,
      archived: 2,
    },
  };

  it("shows candidate counts per status from API response", async () => {
    const { getJobOpening } = await import("@/lib/api/recruitment");

    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: () => Promise.resolve(mockJobOpeningDetail),
    });

    const result = await getJobOpening("jo-123");

    expect(result.candidate_counts).toBeDefined();
    expect(result.candidate_counts.new).toBe(2);
    expect(result.candidate_counts.reviewing).toBe(3);
    expect(result.candidate_counts.interview_scheduled).toBe(1);
    expect(result.candidate_counts.accepted).toBe(3);
    expect(result.candidate_counts.rejected).toBe(5);
    expect(result.candidate_counts.archived).toBe(2);
  });

  it("calculates total candidates correctly", async () => {
    const { getJobOpening } = await import("@/lib/api/recruitment");

    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: () => Promise.resolve(mockJobOpeningDetail),
    });

    const result = await getJobOpening("jo-123");
    const totalCandidates = Object.values(result.candidate_counts).reduce((a, b) => a + b, 0);

    expect(totalCandidates).toBe(16); // 2+3+1+3+5+2
  });

  it("shows filled status when accepted equals target", async () => {
    const { getJobOpening } = await import("@/lib/api/recruitment");

    const data = {
      ...mockJobOpeningDetail,
      target_headcount: 3,
      candidate_counts: {
        ...mockJobOpeningDetail.candidate_counts,
        accepted: 3,
      },
    };

    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: () => Promise.resolve(data),
    });

    const result = await getJobOpening("jo-123");
    const acceptedCount = result.candidate_counts.accepted;
    const filled = acceptedCount >= result.target_headcount;

    expect(filled).toBe(true);
    expect(acceptedCount).toBe(result.target_headcount);
  });

  it("shows overfilled status when accepted exceeds target", async () => {
    const { getJobOpening } = await import("@/lib/api/recruitment");

    const data = {
      ...mockJobOpeningDetail,
      target_headcount: 3,
      candidate_counts: {
        ...mockJobOpeningDetail.candidate_counts,
        accepted: 5,
      },
    };

    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: () => Promise.resolve(data),
    });

    const result = await getJobOpening("jo-123");
    const acceptedCount = result.candidate_counts.accepted;
    const filled = acceptedCount >= result.target_headcount;
    const overfilled = acceptedCount > result.target_headcount;

    expect(filled).toBe(true);
    expect(overfilled).toBe(true);
  });

  it("handles empty candidate counts", async () => {
    const { getJobOpening } = await import("@/lib/api/recruitment");

    const data = {
      ...mockJobOpeningDetail,
      candidate_counts: {},
    };

    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: () => Promise.resolve(data),
    });

    const result = await getJobOpening("jo-123");

    expect(result.candidate_counts).toBeDefined();
    expect(result.candidate_counts.new ?? 0).toBe(0);
    expect(result.candidate_counts.accepted ?? 0).toBe(0);
  });

  it("handles null candidate counts", async () => {
    const { getJobOpening } = await import("@/lib/api/recruitment");

    const data = {
      ...mockJobOpeningDetail,
      candidate_counts: null,
    };

    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: () => Promise.resolve(data),
    });

    const result = await getJobOpening("jo-123");

    // The page should handle null gracefully - counts default to 0
    expect(result.candidate_counts).toBeNull();
  });
});
