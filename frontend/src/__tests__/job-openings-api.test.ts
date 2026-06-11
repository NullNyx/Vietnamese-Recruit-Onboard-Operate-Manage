// @vitest-environment jsdom
import { describe, it, expect, vi, beforeEach } from "vitest";

const mockFetch = vi.fn();
vi.stubGlobal("fetch", mockFetch);

describe("Job Opening API Client", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.resetModules();
  });

  it("listJobOpenings fetches with pagination and status filter", async () => {
    const { listJobOpenings } = await import("@/lib/api/recruitment");

    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: () =>
        Promise.resolve({
          job_openings: [
            {
              id: "jo-1",
              title: "Senior Developer",
              position_id: "pos-1",
              position_name: "Senior Developer",
              target_headcount: 3,
              status: "open",
              created_at: "2026-06-01T00:00:00Z",
              total_candidates: 5,
              accepted_count: 2,
            },
          ],
          total_count: 1,
          page: 1,
          page_size: 20,
        }),
    });

    const result = await listJobOpenings({
      page: 1,
      page_size: 20,
      status: ["open"],
    });

    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining("/api/recruitment/job-openings"),
      expect.objectContaining({ credentials: "include" }),
    );
    expect(result.job_openings).toHaveLength(1);
    expect(result.job_openings[0].title).toBe("Senior Developer");
    expect(result.job_openings[0].accepted_count).toBe(2);
  });

  it("getJobOpening fetches detail by ID", async () => {
    const { getJobOpening } = await import("@/lib/api/recruitment");

    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: () =>
        Promise.resolve({
          id: "jo-1",
          title: "Senior Developer",
          position_id: "pos-1",
          position_name: "Senior Developer",
          target_headcount: 3,
          status: "open",
          opened_at: "2026-06-01T00:00:00Z",
          closed_at: null,
          cancelled_at: null,
          created_at: "2026-06-01T00:00:00Z",
          updated_at: "2026-06-01T00:00:00Z",
          candidate_counts: { new: 2, screening: 1, accepted: 2 },
        }),
    });

    const result = await getJobOpening("jo-1");
    expect(result.title).toBe("Senior Developer");
    expect(result.candidate_counts.accepted).toBe(2);
  });

  it("getJobOpening handles 404", async () => {
    const { getJobOpening } = await import("@/lib/api/recruitment");

    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 404,
      json: () => Promise.resolve({ error_code: "JOB_OPENING_NOT_FOUND", message: "Not found" }),
    });

    await expect(getJobOpening("x")).rejects.toThrow();
  });

  it("listJobOpenings handles network error", async () => {
    const { listJobOpenings } = await import("@/lib/api/recruitment");

    mockFetch.mockRejectedValueOnce(new Error("fail"));
    await expect(listJobOpenings({ page: 1 })).rejects.toThrow();
  });

  it("listJobOpenings omits empty params", async () => {
    const { listJobOpenings } = await import("@/lib/api/recruitment");

    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: () => Promise.resolve({ job_openings: [], total_count: 0, page: 1, page_size: 20 }),
    });

    await listJobOpenings({ search: "", status: [] });

    const url = mockFetch.mock.calls[0][0] as string;
    expect(url).not.toContain("search=");
    expect(url).not.toContain("status=");
    expect(url).toBe("/api/recruitment/job-openings");
  });

  it("listJobOpenings sends page=0 correctly", async () => {
    const { listJobOpenings } = await import("@/lib/api/recruitment");

    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: () => Promise.resolve({ job_openings: [], total_count: 0, page: 0, page_size: 20 }),
    });

    await listJobOpenings({ page: 0 });

    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining("page=0"),
      expect.objectContaining({ credentials: "include" }),
    );
  });
});
