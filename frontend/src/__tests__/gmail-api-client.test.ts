// @vitest-environment jsdom
import { describe, it, expect, vi, beforeEach } from "vitest";

const mockFetch = vi.fn();
vi.stubGlobal("fetch", mockFetch);

describe("Gmail API Client", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("processAttachments calls correct endpoint", async () => {
    const { processAttachments } = await import("@/lib/api/gmail");

    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: () =>
        Promise.resolve({
          processed_count: 1,
          cv_documents: [
            {
              id: "doc-1",
              original_filename: "cv.pdf",
              processing_status: "completed",
              confidence_score: 0.85,
            },
          ],
        }),
    });

    const result = await processAttachments("msg_123");

    expect(mockFetch).toHaveBeenCalledWith(
      "/api/gmail/messages/msg_123/process-attachments",
      { method: "POST" },
    );
    expect(result.processed_count).toBe(1);
  });

  it("listEmailsNeedingReview calls correct endpoint", async () => {
    const { listEmailsNeedingReview } = await import("@/lib/api/gmail");

    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: () =>
        Promise.resolve({
          messages: [
            {
              id: "email-1",
              gmail_message_id: "msg_1",
              subject: "CV Application",
              processing_status: "needs_review",
            },
          ],
          total: 1,
        }),
    });

    const result = await listEmailsNeedingReview();

    expect(mockFetch).toHaveBeenCalledWith(
      "/api/gmail/review/emails?limit=50&offset=0",
    );
    expect(result.messages).toHaveLength(1);
  });

  it("reclassifyEmail calls correct endpoint", async () => {
    const { reclassifyEmail } = await import("@/lib/api/gmail");

    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: () =>
        Promise.resolve({
          id: "email-1",
          processing_status: "classified",
        }),
    });

    const result = await reclassifyEmail("email-1");

    expect(mockFetch).toHaveBeenCalledWith(
      "/api/gmail/review/emails/email-1/reclassify",
      { method: "POST" },
    );
    expect(result.processing_status).toBe("classified");
  });

  it("processAttachments handles no attachments", async () => {
    const { processAttachments } = await import("@/lib/api/gmail");

    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: () =>
        Promise.resolve({
          processed_count: 0,
          message: "No attachments found",
        }),
    });

    const result = await processAttachments("msg_456");

    expect(result.processed_count).toBe(0);
    expect(result.message).toBe("No attachments found");
  });
});
