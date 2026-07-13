import { beforeEach, describe, expect, it, vi } from "vitest";

const fetchMock = vi.fn();
vi.stubGlobal("fetch", fetchMock);

describe("Job Application assignment and promotion API", () => {
  beforeEach(() => vi.clearAllMocks());

  it("assigns exactly one Job Opening with authenticated cookies", async () => {
    fetchMock.mockResolvedValue({
      ok: true,
      json: async () => ({
        id: "application-1",
        job_opening_id: "opening-1",
        candidate_id: null,
        status: "new",
      }),
    });
    const { assignJobApplication } = await import("@/lib/api/recruitment");

    await assignJobApplication("application-1", "opening-1");

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/recruitment/job-applications/application-1/assignment",
      expect.objectContaining({
        method: "POST",
        credentials: "include",
        body: JSON.stringify({ job_opening_id: "opening-1" }),
      }),
    );
  });

  it("promotes with reviewed identity and optional Job Opening", async () => {
    fetchMock.mockResolvedValue({
      ok: true,
      json: async () => ({
        id: "application-1",
        candidate_id: "candidate-1",
        candidate_name: "Nguyen Van A",
        candidate_email: "a@example.com",
        job_opening_id: null,
        status: "promoted",
      }),
    });
    const { promoteJobApplication } = await import("@/lib/api/recruitment");

    await promoteJobApplication("application-1", {
      applicant_name: "Nguyen Van A",
      applicant_email: "a@example.com",
      job_opening_id: null,
    });

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/recruitment/job-applications/application-1/promote",
      expect.objectContaining({
        method: "POST",
        credentials: "include",
        body: JSON.stringify({
          applicant_name: "Nguyen Van A",
          applicant_email: "a@example.com",
          job_opening_id: null,
        }),
      }),
    );
  });
});
