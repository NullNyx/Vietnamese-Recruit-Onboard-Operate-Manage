// @vitest-environment jsdom

import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

const listInbox = vi.fn();
const splitInboxItem = vi.fn();
const proposeInboxLink = vi.fn();
const resolveInboxLinkProposal = vi.fn();

vi.mock("sonner", () => ({ toast: { success: vi.fn(), error: vi.fn() } }));
vi.mock("@/lib/api/recruitment", async (importOriginal) => {
  const original = await importOriginal<typeof import("@/lib/api/recruitment")>();
  return {
    ...original,
    listInbox,
    splitInboxItem,
    proposeInboxLink,
    resolveInboxLinkProposal,
    correctInboxIntent: vi.fn(),
    dismissInboxItem: vi.fn(),
  };
});

const inboxItem = {
  id: "inbox-1",
  gmail_message_id: "msg-1",
  gmail_thread_id: "thread-1",
  sender_name: "Agency Recruiter",
  sender_email: "recruiter@agency.example",
  subject: "Two applicants",
  snippet: "Nguyen A and Tran B apply",
  has_attachments: true,
  attachments_metadata: [],
  inbox_status: "ready_for_review" as const,
  prediction_intent: "job_application",
  confidence_raw: 0.9,
  confidence_calibrated: 0.9,
  evidence: [{ signal: "application_language" }],
  source_hints: [{ key: "sender_role", value: "agency" }],
  corrected_intent: null,
  corrected_by_user_id: null,
  corrected_at: null,
  correction_history: [],
  dismissed: false,
  dismissed_at: null,
  dismissed_by_user_id: null,
  processing_error: null,
  retry_count: 0,
  is_retry_exhausted: false,
  created_at: "2026-07-13T10:00:00Z",
  updated_at: "2026-07-13T10:00:00Z",
};

describe("Recruitment Inbox issue #185 UI journeys", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    listInbox.mockResolvedValue({ items: [inboxItem], total: 1, page: 1, page_size: 20 });
    splitInboxItem.mockResolvedValue({ applications: [{ id: "app-a" }, { id: "app-b" }] });
    proposeInboxLink.mockResolvedValue({
      id: "proposal-1",
      recruitment_inbox_item_id: "inbox-1",
      target_job_application_id: "application-1",
      status: "pending",
    });
    resolveInboxLinkProposal.mockResolvedValue({ status: "confirmed" });
  });

  it("lets HR split an agency source into one application per applicant", async () => {
    const user = userEvent.setup();
    const { default: RecruitmentInboxPage } = await import(
      "@/app/(dashboard)/recruitment/inbox/page"
    );
    render(<RecruitmentInboxPage />);

    await user.click(await screen.findByText("Two applicants"));
    await user.click(screen.getByRole("button", { name: "Tách ứng viên" }));
    await user.selectOptions(screen.getByLabelText("Nguồn ứng tuyển"), "agency");
    await user.type(screen.getByLabelText("Tên ứng viên 1"), "Nguyen A");
    await user.type(screen.getByLabelText("Email ứng viên 1"), "a@example.com");
    await user.click(screen.getByRole("button", { name: "Thêm ứng viên" }));
    await user.type(screen.getByLabelText("Tên ứng viên 2"), "Tran B");
    await user.type(screen.getByLabelText("Email ứng viên 2"), "b@example.com");
    await user.click(screen.getByRole("button", { name: "Xác nhận tách" }));

    await waitFor(() =>
      expect(splitInboxItem).toHaveBeenCalledWith("inbox-1", {
        source: "agency",
        applicants: [
          { name: "Nguyen A", email: "a@example.com" },
          { name: "Tran B", email: "b@example.com" },
        ],
      }),
    );
  });

  it("keeps a cross-thread link pending until HR confirms it", async () => {
    const user = userEvent.setup();
    const { default: RecruitmentInboxPage } = await import(
      "@/app/(dashboard)/recruitment/inbox/page"
    );
    render(<RecruitmentInboxPage />);

    await user.click(await screen.findByText("Two applicants"));
    await user.click(screen.getByRole("button", { name: "Liên kết email" }));
    await user.type(screen.getByLabelText("Job Application đích"), "application-1");
    await user.click(screen.getByRole("button", { name: "Tạo đề xuất" }));

    await waitFor(() =>
      expect(proposeInboxLink).toHaveBeenCalledWith("inbox-1", "application-1"),
    );
    expect(resolveInboxLinkProposal).not.toHaveBeenCalled();

    await user.click(screen.getByRole("button", { name: "Xác nhận liên kết" }));
    await waitFor(() =>
      expect(resolveInboxLinkProposal).toHaveBeenCalledWith("proposal-1", "confirmed"),
    );
  });
});
