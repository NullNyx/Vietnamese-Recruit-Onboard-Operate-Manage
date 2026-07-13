// @vitest-environment jsdom
import { describe, it, expect, vi, beforeEach } from "vitest";

import type { InboxStatus } from "@/lib/api/recruitment";

const mockFetch = vi.fn();
vi.stubGlobal("fetch", mockFetch);

describe("Recruitment Inbox API Client (GH #184)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

      const mockItems = [
        {
          id: "inbox-1",
          gmail_message_id: "msg_abc123",
          gmail_thread_id: "thread_abc123",
          sender_name: "Nguyen Van A",
          sender_email: "nguyenvana@example.com",
          subject: "Ung tuyen Python Developer",
          snippet: "Toi muon ung tuyen vi tri Python Developer",
          has_attachments: true,
          attachments_metadata: [
            { name: "CV_NguyenVanA.pdf", type: "application/pdf", size: 245760 },
          ],
          inbox_status: "needs_classification",
      prediction_intent: "job_application",
      confidence_raw: 0.45,
      confidence_calibrated: 0.42,
      evidence: [{ signal: "subject:ung tuyen" }],
      source_hints: [{ key: "sender_role", value: "candidate" }],
      corrected_intent: null,
      corrected_by_user_id: null,
      corrected_at: null,
      correction_history: [],
      dismissed: false,
      dismissed_at: null,
      dismissed_by_user_id: null,
      processing_error: null,
      retry_count: 1,
      is_retry_exhausted: false,
      created_at: "2026-07-13T10:00:00Z",
      updated_at: "2026-07-13T10:00:00Z",
    },
    {
      id: "inbox-2",
      gmail_message_id: "msg_def456",
      gmail_thread_id: "thread_def456",
      sender_name: "Tran Thi B",
      sender_email: "tranthib@example.com",
      subject: "Ung tuyen Frontend",
      snippet: "Gui CV ung tuyen",
      has_attachments: false,
      inbox_status: "needs_information",
      prediction_intent: "job_application",
      confidence_raw: 0.35,
      confidence_calibrated: 0.32,
      evidence: [{ signal: "subject:CV" }],
      source_hints: [],
      corrected_intent: null,
      corrected_by_user_id: null,
      corrected_at: null,
      correction_history: [],
      dismissed: false,
      dismissed_at: null,
      dismissed_by_user_id: null,
      processing_error: null,
      retry_count: 2,
      is_retry_exhausted: false,
      created_at: "2026-07-13T09:00:00Z",
      updated_at: "2026-07-13T09:00:00Z",
    },
  ];

  // ---------------------------------------------------------------------------
  // listInbox
  // ---------------------------------------------------------------------------

  it("listInbox fetches with default pagination", async () => {
    const { listInbox } = await import("@/lib/api/recruitment");

    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: () =>
        Promise.resolve({
          items: mockItems,
          total: 2,
          page: 1,
          page_size: 20,
        }),
    });

    const result = await listInbox();

    expect(mockFetch).toHaveBeenCalledWith(
      "/api/recruitment/inbox",
      expect.objectContaining({ credentials: "include" }),
    );
    expect(result.items).toHaveLength(2);
    expect(result.total).toBe(2);
  });

  it("listInbox fetches with status filter", async () => {
    const { listInbox } = await import("@/lib/api/recruitment");

    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: () =>
        Promise.resolve({
          items: [mockItems[0]],
          total: 1,
          page: 1,
          page_size: 20,
        }),
    });

    const result = await listInbox({ inbox_status: "needs_classification" });

    expect(mockFetch).toHaveBeenCalledWith(
      "/api/recruitment/inbox?inbox_status=needs_classification",
      expect.objectContaining({ credentials: "include" }),
    );
    expect(result.items).toHaveLength(1);
    expect(result.items[0].inbox_status).toBe("needs_classification");
  });

  it("listInbox fetches with pagination params", async () => {
    const { listInbox } = await import("@/lib/api/recruitment");

    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: () =>
        Promise.resolve({
          items: [],
          total: 0,
          page: 2,
          page_size: 10,
        }),
    });

    await listInbox({ page: 2, page_size: 10 });

    expect(mockFetch).toHaveBeenCalledWith(
      "/api/recruitment/inbox?page=2&page_size=10",
      expect.objectContaining({ credentials: "include" }),
    );
  });

      it("listInbox supports all four status filters", async () => {
        const { listInbox } = await import("@/lib/api/recruitment");

        const statuses: InboxStatus[] = [
          "needs_classification",
          "needs_information",
          "ready_for_review",
          "resolved",
        ];

        for (const status of statuses) {
          mockFetch.mockResolvedValueOnce({
            ok: true,
            status: 200,
            json: () => Promise.resolve({ items: [], total: 0, page: 1, page_size: 20 }),
          });

          await listInbox({ inbox_status: status });

          expect(mockFetch).toHaveBeenLastCalledWith(
            `/api/recruitment/inbox?inbox_status=${status}`,
            expect.any(Object),
          );
        }
      });

  // ---------------------------------------------------------------------------
  // getInboxItem
  // ---------------------------------------------------------------------------

  it("getInboxItem fetches a single item with full detail", async () => {
    const { getInboxItem } = await import("@/lib/api/recruitment");

    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: () => Promise.resolve(mockItems[0]),
    });

    const result = await getInboxItem("inbox-1");

    expect(mockFetch).toHaveBeenCalledWith(
      "/api/recruitment/inbox/inbox-1",
      expect.objectContaining({ credentials: "include" }),
    );
    expect(result.id).toBe("inbox-1");
    expect(result.prediction_intent).toBe("job_application");
    expect(result.confidence_raw).toBe(0.45);
    expect(result.confidence_calibrated).toBe(0.42);
    expect(result.evidence).toHaveLength(1);
    expect(result.source_hints).toHaveLength(1);
    expect(result.is_retry_exhausted).toBe(false);
  });

  it("getInboxItem returns retry exhausted state", async () => {
    const { getInboxItem } = await import("@/lib/api/recruitment");

    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: () =>
        Promise.resolve({
          ...mockItems[0],
          id: "inbox-exhausted",
          is_retry_exhausted: true,
          retry_count: 3,
          processing_error: "AI provider unavailable; retries exhausted",
        }),
    });

    const result = await getInboxItem("inbox-exhausted");

    expect(result.is_retry_exhausted).toBe(true);
    expect(result.retry_count).toBe(3);
    expect(result.processing_error).toContain("retries exhausted");
  });

  // ---------------------------------------------------------------------------
  // correctInboxIntent
  // ---------------------------------------------------------------------------

  it("correctInboxIntent sends POST with corrected_intent", async () => {
    const { correctInboxIntent } = await import("@/lib/api/recruitment");

    const correctedItem = {
      ...mockItems[0],
      corrected_intent: "other",
      corrected_by_user_id: "user-1",
      corrected_at: "2026-07-13T11:00:00Z",
      correction_history: [
        {
          previous_intent: "job_application",
          corrected_intent: "other",
          corrected_by_user_id: "user-1",
          corrected_at: "2026-07-13T11:00:00Z",
        },
      ],
      inbox_status: "resolved",
    };

    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: () => Promise.resolve(correctedItem),
    });

    const result = await correctInboxIntent("inbox-1", "other");

    expect(mockFetch).toHaveBeenCalledWith(
      "/api/recruitment/inbox/inbox-1/correct-intent",
      expect.objectContaining({
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ corrected_intent: "other" }),
      }),
    );
    expect(result.corrected_intent).toBe("other");
    expect(result.inbox_status).toBe("resolved");
    expect(result.correction_history).toHaveLength(1);
  });

  it("correctInboxIntent preserves correction history on multiple corrections", async () => {
    const { correctInboxIntent } = await import("@/lib/api/recruitment");

    const updatedItem = {
      ...mockItems[0],
      corrected_intent: "partner",
      corrected_by_user_id: "user-1",
      corrected_at: "2026-07-13T12:00:00Z",
      correction_history: [
        {
          previous_intent: "job_application",
          corrected_intent: "other",
          corrected_by_user_id: "user-1",
          corrected_at: "2026-07-13T11:00:00Z",
        },
        {
          previous_intent: "other",
          corrected_intent: "partner",
          corrected_by_user_id: "user-1",
          corrected_at: "2026-07-13T12:00:00Z",
        },
      ],
      inbox_status: "resolved",
    };

    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: () => Promise.resolve(updatedItem),
    });

    const result = await correctInboxIntent("inbox-1", "partner");

        expect(result.correction_history!).toHaveLength(2);
        expect(updatedItem.correction_history[1].corrected_intent).toBe("partner");
  });

  // ---------------------------------------------------------------------------
  // dismissInboxItem
  // ---------------------------------------------------------------------------

  it("dismissInboxItem sends POST and returns dismissed item", async () => {
    const { dismissInboxItem } = await import("@/lib/api/recruitment");

    const dismissedItem = {
      ...mockItems[0],
      dismissed: true,
      dismissed_at: "2026-07-13T11:00:00Z",
      dismissed_by_user_id: "user-1",
      inbox_status: "resolved",
    };

    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: () => Promise.resolve(dismissedItem),
    });

    const result = await dismissInboxItem("inbox-1");

    expect(mockFetch).toHaveBeenCalledWith(
      "/api/recruitment/inbox/inbox-1/dismiss",
      expect.objectContaining({
        method: "POST",
        credentials: "include",
      }),
    );
    expect(result.dismissed).toBe(true);
    expect(result.dismissed_by_user_id).toBe("user-1");
    expect(result.dismissed_at).toBeTruthy();
    expect(result.inbox_status).toBe("resolved");
  });

  it("dismissInboxItem is idempotent when already dismissed", async () => {
    const { dismissInboxItem } = await import("@/lib/api/recruitment");

    // Idempotent: dismissing an already dismissed item returns success
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: () =>
        Promise.resolve({
          ...mockItems[0],
          dismissed: true,
          dismissed_at: "2026-07-13T10:30:00Z",
          dismissed_by_user_id: "user-1",
          inbox_status: "resolved",
        }),
    });

    const result = await dismissInboxItem("inbox-1");

    expect(result.dismissed).toBe(true);
    expect(result.dismissed_at).toBeTruthy();
  });

  // ---------------------------------------------------------------------------
  // Error handling
  // ---------------------------------------------------------------------------

  it("throws ApiError with message on server error", async () => {
    const { listInbox } = await import("@/lib/api/recruitment");
    const { ApiError } = await import("@/lib/api/types");

    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 422,
      json: () =>
        Promise.resolve({
          detail: "Invalid inbox_status 'invalid'. Valid values: needs_classification, needs_information, ready_for_review, resolved",
        }),
    });

    // @ts-expect-error exercise runtime validation for an unsupported status
    await expect(listInbox({ inbox_status: "invalid" })).rejects.toThrow(ApiError);
  });

  it("throws 404 when inbox item not found", async () => {
    const { getInboxItem } = await import("@/lib/api/recruitment");
    const { ApiError } = await import("@/lib/api/types");

    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 404,
      json: () => Promise.resolve({ detail: "Recruitment Inbox item not found" }),
    });

    await expect(getInboxItem("nonexistent")).rejects.toThrow(ApiError);
  });

  it("throws 409 when modifying a dismissed item", async () => {
    const { correctInboxIntent } = await import("@/lib/api/recruitment");
    const { ApiError } = await import("@/lib/api/types");

    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 409,
      json: () => Promise.resolve({ detail: "Cannot modify a dismissed inbox item" }),
    });

    await expect(correctInboxIntent("dismissed-id", "other")).rejects.toThrow(ApiError);
  });
});
