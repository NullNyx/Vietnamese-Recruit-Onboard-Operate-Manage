// @vitest-environment jsdom
import { describe, it, expect, vi, beforeEach } from "vitest";

const mockFetch = vi.fn();
vi.stubGlobal("fetch", mockFetch);

describe("Recruitment Review API Client", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("listReviewQueue fetches with pagination", async () => {
    const { listReviewQueue } = await import("@/lib/api/recruitment");

    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: () =>
        Promise.resolve({
          items: [
            {
              id: "cv-1",
              processing_status: "needs_review",
              confidence_score: 0.45,
              parsed_cv_data: { name: "Nguyen Van A" },
            },
          ],
          total: 1,
          page: 1,
          page_size: 20,
        }),
    });

    const result = await listReviewQueue({ page: 1, page_size: 20 });

    expect(mockFetch).toHaveBeenCalledWith(
      "/api/recruitment/cv-review?page=1&page_size=20",
      expect.objectContaining({ credentials: "include" }),
    );
    expect(result.items).toHaveLength(1);
    expect(result.items[0].processing_status).toBe("needs_review");
  });

  it("submitCorrection sends PUT with corrected data", async () => {
    const { submitCorrection } = await import("@/lib/api/recruitment");

    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: () =>
        Promise.resolve({
          id: "candidate-1",
          name: "Nguyen Van A",
          email: "a@example.com",
          status: "new",
        }),
    });

    await submitCorrection("cv-1", {
      name: "Nguyen Van A",
      email: "a@example.com",
      phone: "0901234567",
      skills: ["Python"],
      experience: [],
      education: [],
      summary: "Developer",
    });

    expect(mockFetch).toHaveBeenCalledWith(
      "/api/recruitment/cv-review/cv-1",
      expect.objectContaining({
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
      }),
    );
  });

  it("retryParse calls POST to retry endpoint", async () => {
    const { retryParse } = await import("@/lib/api/recruitment");

    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: () =>
        Promise.resolve({
          id: "cv-1",
          processing_status: "completed",
          confidence_score: 0.85,
        }),
    });

    const result = await retryParse("cv-1");

    expect(mockFetch).toHaveBeenCalledWith(
      "/api/recruitment/cv-review/cv-1/retry",
      expect.objectContaining({
        method: "POST",
        credentials: "include",
      }),
    );
    expect(result.processing_status).toBe("completed");
  });

  it("dismissReview calls DELETE endpoint", async () => {
    const { dismissReview } = await import("@/lib/api/recruitment");

    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 204,
    });

    await dismissReview("cv-1");

    expect(mockFetch).toHaveBeenCalledWith(
      "/api/recruitment/cv-review/cv-1/dismiss",
      expect.objectContaining({
        method: "DELETE",
        credentials: "include",
      }),
    );
  });
});
