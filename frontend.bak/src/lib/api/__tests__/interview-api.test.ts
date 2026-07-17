/**
 * @vitest-environment jsdom
 *
 * Tests for the GH #148 / #154 / #155 Interview API functions:
 * createInterview, completeInterview, cancelInterview,
 * createReplacementInterview, listCalendarConflicts,
 * getCalendarConflict, resolveCalendarConflict.
 *
 * Validates correct endpoint URLs, HTTP method, headers, and
 * error handling for each function.
 */
import { describe, it, expect, vi, afterEach } from "vitest";
import {
  createInterview,
  completeInterview,
  cancelInterview,
  createReplacementInterview,
  listCalendarConflicts,
  getCalendarConflict,
  resolveCalendarConflict,
  type CreateInterviewRequest,
  type InterviewResponse,
  type CalendarConflictListResponse,
  type CalendarConflict,
} from "../recruitment";
import { ApiError } from "../types";

const CANDIDATE_ID = "cand-123";
const INTERVIEW_ID = "iv-456";
const CONFLICT_ID = "conf-789";

const SAMPLE_INTERVIEW_RESPONSE: InterviewResponse = {
  id: INTERVIEW_ID,
  candidate_id: CANDIDATE_ID,
  status: "scheduled",
  round_name: "Technical Round 1",
  start_at: "2099-06-15T10:00:00Z",
  end_at: "2099-06-15T11:00:00Z",
  timezone: "Asia/Ho_Chi_Minh",
  calendar_event_id: "evt-001",
  needs_relink: false,
  participants: [
    { id: "p1", interview_id: INTERVIEW_ID, type: "candidate", email: "cand@example.com", name: "John Doe", employee_id: null },
    { id: "p2", interview_id: INTERVIEW_ID, type: "employee", email: "emp@example.com", name: "Alice Tran", employee_id: "emp-1" },
  ],
};

const SAMPLE_CREATE_REQUEST: CreateInterviewRequest = {
  round_name: "Technical Round 1",
  start: "2099-06-15T10:00:00+07:00",
  end: "2099-06-15T11:00:00+07:00",
  timezone: "Asia/Ho_Chi_Minh",
  mode: "google_meet",
  interviewer_ids: ["emp-1", "emp-2"],
  notes: "Technical assessment",
};

const SAMPLE_CONFLICT: CalendarConflict = {
  id: CONFLICT_ID,
  interview_id: INTERVIEW_ID,
  candidate_id: CANDIDATE_ID,
  calendar_event_id: "evt-001",
  local_snapshot: { status: "confirmed" },
  remote_snapshot: { status: "cancelled" },
  conflict_details: { etag_mismatch: true },
  status: "unresolved",
  resolved_by: null,
  resolved_at: null,
  created_at: "2099-06-15T10:00:00Z",
  updated_at: "2099-06-15T10:00:00Z",
};

function mockFetch(response: Partial<Response>) {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({}),
      ...response,
    }),
  );
}

function mockFetchError(status: number, errorCode: string, detail: string) {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue({
      ok: false,
      status,
      json: async () => ({ error_code: errorCode, detail }),
    }),
  );
}

describe("createInterview", () => {
  afterEach(() => vi.restoreAllMocks());

  it("POSTs to /candidates/{id}/create-interview with correct body", async () => {
    mockFetch({ json: async () => SAMPLE_INTERVIEW_RESPONSE });
    const result = await createInterview(CANDIDATE_ID, SAMPLE_CREATE_REQUEST);

    expect(result).toEqual(SAMPLE_INTERVIEW_RESPONSE);
    const fetchCall = (vi.mocked(fetch) as unknown as ReturnType<typeof vi.fn>).mock.calls[0];
    expect(fetchCall[0]).toContain(`/candidates/${CANDIDATE_ID}/create-interview`);
    expect(fetchCall[1]?.method).toBe("POST");
    expect(fetchCall[1]?.headers?.["Content-Type"]).toBe("application/json");
    expect(JSON.parse(fetchCall[1]?.body)).toEqual(SAMPLE_CREATE_REQUEST);
  });

  it("returns 201 InterviewResponse on success", async () => {
    mockFetch({ status: 201, json: async () => SAMPLE_INTERVIEW_RESPONSE });
    const result = await createInterview(CANDIDATE_ID, SAMPLE_CREATE_REQUEST);
    expect(result.status).toBe("scheduled");
    expect(result.round_name).toBe("Technical Round 1");
  });

  it("throws ApiError on 409 conflict", async () => {
    mockFetchError(409, "CALENDAR_GRANT_MISSING", "Google Calendar chưa được cấp quyền");
    await expect(createInterview(CANDIDATE_ID, SAMPLE_CREATE_REQUEST)).rejects.toThrow(ApiError);
    await expect(createInterview(CANDIDATE_ID, SAMPLE_CREATE_REQUEST)).rejects.toMatchObject({
      statusCode: 409,
      errorCode: "CALENDAR_GRANT_MISSING",
    });
  });
});

describe("completeInterview", () => {
  afterEach(() => vi.restoreAllMocks());

  it("POSTs to /candidates/{id}/interviews/{interviewId}/complete", async () => {
    mockFetch({ json: async () => ({ ...SAMPLE_INTERVIEW_RESPONSE, status: "completed" }) });
    const result = await completeInterview(CANDIDATE_ID, INTERVIEW_ID);
    expect(result.status).toBe("completed");
    const fetchCall = (vi.mocked(fetch) as unknown as ReturnType<typeof vi.fn>).mock.calls[0];
    expect(fetchCall[0]).toContain(`/candidates/${CANDIDATE_ID}/interviews/${INTERVIEW_ID}/complete`);
    expect(fetchCall[1]?.method).toBe("POST");
  });

  it("throws ApiError on 404 interview not found", async () => {
    mockFetchError(404, "INTERVIEW_NOT_FOUND", "Interview không tồn tại");
    await expect(completeInterview(CANDIDATE_ID, INTERVIEW_ID)).rejects.toThrow(ApiError);
  });
});

describe("cancelInterview", () => {
  afterEach(() => vi.restoreAllMocks());

  it("POSTs to /candidates/{id}/interviews/{interviewId}/cancel", async () => {
    mockFetch({ json: async () => ({ ...SAMPLE_INTERVIEW_RESPONSE, status: "cancelled" }) });
    const result = await cancelInterview(CANDIDATE_ID, INTERVIEW_ID);
    expect(result.status).toBe("cancelled");
    const fetchCall = (vi.mocked(fetch) as unknown as ReturnType<typeof vi.fn>).mock.calls[0];
    expect(fetchCall[0]).toContain(`/candidates/${CANDIDATE_ID}/interviews/${INTERVIEW_ID}/cancel`);
    expect(fetchCall[1]?.method).toBe("POST");
  });
});

describe("createReplacementInterview", () => {
  afterEach(() => vi.restoreAllMocks());

  it("POSTs to /candidates/{id}/interviews/{interviewId}/replacement with correct body", async () => {
    mockFetch({ status: 201, json: async () => SAMPLE_INTERVIEW_RESPONSE });
    const result = await createReplacementInterview(CANDIDATE_ID, INTERVIEW_ID, SAMPLE_CREATE_REQUEST);
    expect(result.id).toBe(INTERVIEW_ID);
    const fetchCall = (vi.mocked(fetch) as unknown as ReturnType<typeof vi.fn>).mock.calls[0];
    expect(fetchCall[0]).toContain(`/candidates/${CANDIDATE_ID}/interviews/${INTERVIEW_ID}/replacement`);
    expect(fetchCall[1]?.method).toBe("POST");
    expect(JSON.parse(fetchCall[1]?.body)).toEqual(SAMPLE_CREATE_REQUEST);
  });
});

describe("listCalendarConflicts", () => {
  afterEach(() => vi.restoreAllMocks());

  it("GETs /api/recruitment/calendar-conflicts with no params", async () => {
    const listResponse: CalendarConflictListResponse = { conflicts: [SAMPLE_CONFLICT], total_count: 1 };
    mockFetch({ json: async () => listResponse });
    const result = await listCalendarConflicts();
    expect(result.conflicts).toHaveLength(1);
    expect(result.conflicts[0].id).toBe(CONFLICT_ID);
    const fetchCall = (vi.mocked(fetch) as unknown as ReturnType<typeof vi.fn>).mock.calls[0];
    expect(fetchCall[0]).toContain("/api/recruitment/calendar-conflicts");
    expect(fetchCall[0]).not.toContain("?");
  });

  it("passes status and candidate_id query params", async () => {
    mockFetch({ json: async () => ({ conflicts: [], total_count: 0 }) });
    await listCalendarConflicts({ status: "unresolved", candidate_id: CANDIDATE_ID });
    const fetchCall = (vi.mocked(fetch) as unknown as ReturnType<typeof vi.fn>).mock.calls[0];
    expect(fetchCall[0]).toContain("status=unresolved");
    expect(fetchCall[0]).toContain("candidate_id=" + CANDIDATE_ID);
  });
});

describe("getCalendarConflict", () => {
  afterEach(() => vi.restoreAllMocks());

  it("GETs /api/recruitment/calendar-conflicts/{conflictId}", async () => {
    mockFetch({ json: async () => SAMPLE_CONFLICT });
    const result = await getCalendarConflict(CONFLICT_ID);
    expect(result.id).toBe(CONFLICT_ID);
    const fetchCall = (vi.mocked(fetch) as unknown as ReturnType<typeof vi.fn>).mock.calls[0];
    expect(fetchCall[0]).toContain(`/api/recruitment/calendar-conflicts/${CONFLICT_ID}`);
  });
});

describe("resolveCalendarConflict", () => {
  afterEach(() => vi.restoreAllMocks());

  it("POSTs to /api/recruitment/calendar-conflicts/{conflictId}/resolve with choice", async () => {
    mockFetch({ json: async () => ({ ...SAMPLE_CONFLICT, status: "resolved", resolved_by: "user-1", resolved_at: "2099-06-15T11:00:00Z" }) });
    const result = await resolveCalendarConflict(CONFLICT_ID, { choice: "keep_google" });
    expect(result.status).toBe("resolved");
    const fetchCall = (vi.mocked(fetch) as unknown as ReturnType<typeof vi.fn>).mock.calls[0];
    expect(fetchCall[0]).toContain(`/api/recruitment/calendar-conflicts/${CONFLICT_ID}/resolve`);
    expect(fetchCall[1]?.method).toBe("POST");
    expect(JSON.parse(fetchCall[1]?.body)).toEqual({ choice: "keep_google" });
  });
});
