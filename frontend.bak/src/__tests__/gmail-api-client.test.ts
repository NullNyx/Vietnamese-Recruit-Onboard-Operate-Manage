// @vitest-environment jsdom
import { describe, it, expect, vi, beforeEach } from "vitest";

const mockFetch = vi.fn();
vi.stubGlobal("fetch", mockFetch);

describe("Gmail API Client", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  // ---------------------------------------------------------------------------
  // Connection status (identity router)
  // ---------------------------------------------------------------------------

  describe("getConnectionStatus", () => {
    it("calls GET /api/auth/organization-google-connection and returns status", async () => {
      const { getConnectionStatus } = await import("@/lib/api/gmail");

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: () =>
          Promise.resolve({
            status: "connected",
            email: "admin@example.com",
            has_secret: true,
          }),
      });

      const result = await getConnectionStatus();

      expect(mockFetch).toHaveBeenCalledWith(
        "/api/auth/organization-google-connection",
      );
      expect(result.status).toBe("connected");
      expect(result.email).toBe("admin@example.com");
      expect(result.has_secret).toBe(true);
    });

    it("returns disconnected when not connected", async () => {
      const { getConnectionStatus } = await import("@/lib/api/gmail");

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: () =>
          Promise.resolve({
            status: "disconnected",
            email: null,
            has_secret: false,
          }),
      });

      const result = await getConnectionStatus();

      expect(result.status).toBe("disconnected");
      expect(result.email).toBeNull();
    });

    it("throws ApiError on non-ok response", async () => {
      const { getConnectionStatus } = await import("@/lib/api/gmail");
      const { ApiError } = await import("@/lib/api/types");

      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        statusText: "Internal Server Error",
        json: () => Promise.resolve({ detail: "Server error" }),
      });

      await expect(getConnectionStatus()).rejects.toThrow(ApiError);
    });
  });

  // ---------------------------------------------------------------------------
  // Authorize URL
  // ---------------------------------------------------------------------------

  describe("getAuthorizeUrl", () => {
    it("calls GET /api/auth/organization-google-connection/authorize-url", async () => {
      const { getAuthorizeUrl } = await import("@/lib/api/gmail");

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: () =>
          Promise.resolve({
            status: "disconnected",
            email: null,
            has_secret: true,
            redirect_url: "https://accounts.google.com/o/oauth2/v2/auth?...",
          }),
      });

      const result = await getAuthorizeUrl();

      expect(mockFetch).toHaveBeenCalledWith(
        "/api/auth/organization-google-connection/authorize-url",
      );
      expect(result.redirect_url).toContain("accounts.google.com");
    });
  });

  // ---------------------------------------------------------------------------
  // Reconnect
  // ---------------------------------------------------------------------------

  describe("reconnectConnection", () => {
    it("calls POST /api/auth/organization-google-connection/reconnect", async () => {
      const { reconnectConnection } = await import("@/lib/api/gmail");

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: () =>
          Promise.resolve({
            status: "disconnected",
            email: "admin@example.com",
            has_secret: true,
            redirect_url: "https://accounts.google.com/o/oauth2/v2/auth?...",
          }),
      });

      const result = await reconnectConnection();

      expect(mockFetch).toHaveBeenCalledWith(
        "/api/auth/organization-google-connection/reconnect",
        { method: "POST" },
      );
      expect(result.redirect_url).toContain("accounts.google.com");
    });
  });

  // ---------------------------------------------------------------------------
  // Disconnect
  // ---------------------------------------------------------------------------

  describe("disconnectConnection", () => {
    it("calls DELETE /api/auth/organization-google-connection", async () => {
      const { disconnectConnection } = await import("@/lib/api/gmail");

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: () =>
          Promise.resolve({
            status: "disconnected",
            email: null,
            has_secret: false,
          }),
      });

      const result = await disconnectConnection();

      expect(mockFetch).toHaveBeenCalledWith(
        "/api/auth/organization-google-connection",
        { method: "DELETE" },
      );
      expect(result.status).toBe("disconnected");
    });
  });

  // ---------------------------------------------------------------------------
  // Capability health
  // ---------------------------------------------------------------------------

  describe("getCapabilityHealth", () => {
    it("returns unknown for all capabilities when connected", async () => {
      const { getCapabilityHealth } = await import("@/lib/api/gmail");

      const result = getCapabilityHealth(true);

      expect(result).toHaveLength(3);
      for (const cap of result) {
        expect(cap.health).toBe("unknown");
      }
      expect(result.map((c) => c.capability)).toEqual([
        "gmail_ingestion",
        "gmail_sending",
        "calendar_sync",
      ]);
    });

    it("returns unavailable for all capabilities when disconnected", async () => {
      const { getCapabilityHealth } = await import("@/lib/api/gmail");

      const result = getCapabilityHealth(false);

      expect(result).toHaveLength(3);
      for (const cap of result) {
        expect(cap.health).toBe("unavailable");
      }
    });
  });

  // ---------------------------------------------------------------------------
  // processAttachments (unchanged)
  // ---------------------------------------------------------------------------

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

  // ---------------------------------------------------------------------------
  // listEmailsNeedingReview (unchanged)
  // ---------------------------------------------------------------------------

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

  // ---------------------------------------------------------------------------
  // reclassifyEmail (unchanged)
  // ---------------------------------------------------------------------------

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

  // ---------------------------------------------------------------------------
  // processAttachments handles no attachments (unchanged)
  // ---------------------------------------------------------------------------

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
