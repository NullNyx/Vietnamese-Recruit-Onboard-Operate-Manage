// @vitest-environment jsdom

import "@testing-library/jest-dom/vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

const listJobOpenings = vi.fn();
const assignJobApplication = vi.fn();
const promoteJobApplication = vi.fn();

vi.mock("sonner", () => ({ toast: { success: vi.fn(), error: vi.fn() } }));
vi.mock("@/lib/api/recruitment", async (importOriginal) => ({
  ...(await importOriginal<typeof import("@/lib/api/recruitment")>()),
  listJobOpenings,
  assignJobApplication,
  promoteJobApplication,
}));

const application = {
  id: "application-1",
  source_email_message_id: "email-1",
  gmail_message_id: "gmail-1",
  gmail_thread_id: "thread-1",
  source: "direct" as const,
  applicant_name: "Nguyen Van A",
  applicant_email: "a@example.com",
  sender_name: "Nguyen Van A",
  sender_email: "a@example.com",
  job_opening_id: null,
  status: "new",
  message_references: [],
};

const opening = {
  id: "opening-1",
  title: "Backend Engineer",
  position_id: "position-1",
  position_name: "Engineer",
  target_headcount: 1,
  status: "open" as const,
  created_at: "2026-07-13T00:00:00Z",
  total_candidates: 0,
  accepted_count: 0,
};

describe("Job Application HR journey", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    listJobOpenings.mockResolvedValue({
      job_openings: [opening],
      total_count: 1,
      page: 1,
      page_size: 100,
    });
    assignJobApplication.mockResolvedValue({
      id: application.id,
      job_opening_id: opening.id,
      candidate_id: null,
      status: "new",
    });
    promoteJobApplication.mockResolvedValue({
      id: application.id,
      candidate_id: "candidate-1",
      candidate_name: application.applicant_name,
      candidate_email: application.applicant_email,
      job_opening_id: opening.id,
      status: "promoted",
    });
  });

  it("lets HR assign one opening and promote through public API mocks", async () => {
    const user = userEvent.setup();
    const { JobApplicationActions } = await import(
      "@/components/recruitment/job-application-actions"
    );
    render(<JobApplicationActions applications={[application]} />);

    await user.selectOptions(await screen.findByLabelText("Job Opening"), opening.id);
    await waitFor(() =>
      expect(assignJobApplication).toHaveBeenCalledWith(application.id, opening.id),
    );

    await user.click(screen.getByRole("button", { name: "Promote thành Candidate" }));
    await waitFor(() =>
      expect(promoteJobApplication).toHaveBeenCalledWith(application.id, {
        applicant_name: application.applicant_name,
        applicant_email: application.applicant_email,
        job_opening_id: opening.id,
      }),
    );
    expect(await screen.findByText("Đã promote")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Promote thành Candidate" })).toBeNull();
  });

  it("allows HR to leave the Job Opening unspecified", async () => {
    const user = userEvent.setup();
    const { JobApplicationActions } = await import(
      "@/components/recruitment/job-application-actions"
    );
    render(<JobApplicationActions applications={[{ ...application, job_opening_id: opening.id }]} />);

    await user.selectOptions(await screen.findByLabelText("Job Opening"), "");

    await waitFor(() =>
      expect(assignJobApplication).toHaveBeenCalledWith(application.id, null),
    );
  });
});
