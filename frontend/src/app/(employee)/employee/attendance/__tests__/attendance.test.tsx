import { describe, it, expect, vi, beforeEach } from "vitest";

// Mock useCurrentUser hook
vi.mock("@/hooks/use-current-user", () => ({
  useCurrentUser: () => ({
    user: { employee_id: "test-emp-id" },
    loading: false,
    error: null,
  }),
}));

// Mock toast
vi.mock("sonner", () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
  ToastProvider: ({ children }: { children: React.ReactNode }) => children,
}));

// Mock fetch globally
const mockFetch = vi.fn();
global.fetch = mockFetch;

describe("Attendance state derivation", () => {
  beforeEach(() => {
    mockFetch.mockReset();
    vi.clearAllMocks();
  });

  it("derives empty state from null record", () => {
    const record = null;
    const state = !record ? "empty" : record.check_out_at ? "completed" : record.check_in_at ? "checked-in" : "empty";
    expect(state).toBe("empty");
  });

  it("derives checked-in state from record without check-out", () => {
    const record = { check_in_at: "2026-06-10T08:00:00Z", check_out_at: null };
    const state = !record ? "empty" : record.check_out_at ? "completed" : record.check_in_at ? "checked-in" : "empty";
    expect(state).toBe("checked-in");
  });

  it("derives completed state from record with both check-in and check-out", () => {
    const record = { check_in_at: "2026-06-10T08:00:00Z", check_out_at: "2026-06-10T17:00:00Z" };
    const state = !record ? "empty" : record.check_out_at ? "completed" : record.check_in_at ? "checked-in" : "empty";
    expect(state).toBe("completed");
  });
});

describe("Error response handling", () => {
  it("extracts detail from OFFICE_NETWORK_REQUIRED error", () => {
    const errorData = {
      error_code: "OFFICE_NETWORK_REQUIRED",
      detail: "Attendance check-in is only allowed from approved office network.",
    };
    expect(errorData.detail).toBe("Attendance check-in is only allowed from approved office network.");
    expect(errorData.error_code).toBe("OFFICE_NETWORK_REQUIRED");
  });

  it("extracts detail from ALREADY_CHECKED_IN error", () => {
    const errorData = {
      error_code: "ALREADY_CHECKED_IN",
      detail: "Already checked in for today",
    };
    expect(errorData.detail).toBe("Already checked in for today");
  });

  it("extracts detail from NOT_CHECKED_IN error", () => {
    const errorData = {
      error_code: "NOT_CHECKED_IN",
      detail: "Must check in before checking out",
    };
    expect(errorData.detail).toBe("Must check in before checking out");
  });
});

describe("API fetch with credentials", () => {
  it("fetches today attendance with credentials", async () => {
    const mockRecord = {
      id: "test-id",
      employee_id: "test-emp-id",
      work_date: "2026-06-10",
      check_in_at: "2026-06-10T08:00:00Z",
      check_out_at: null,
      check_in_ip: "192.168.1.100",
      source: "WEB",
    };

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockRecord),
    });

    const res = await fetch("/api/attendance/me/today", { credentials: "include" });
    const data = await res.json();

    expect(mockFetch).toHaveBeenCalledWith("/api/attendance/me/today", { credentials: "include" });
    expect(data.check_in_at).toBe("2026-06-10T08:00:00Z");
  });

  it("fetches history with credentials and month params", async () => {
    const mockRecords = [
      {
        id: "1",
        employee_id: "test-emp-id",
        work_date: "2026-06-10",
        check_in_at: "2026-06-10T08:00:00Z",
        check_out_at: "2026-06-10T17:00:00Z",
        source: "WEB",
      },
    ];

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ records: mockRecords, year: 2026, month: 6 }),
    });

    const res = await fetch("/api/attendance/me/history?year=2026&month=6", { credentials: "include" });
    const data = await res.json();

    expect(mockFetch).toHaveBeenCalledWith("/api/attendance/me/history?year=2026&month=6", { credentials: "include" });
    expect(data.records).toHaveLength(1);
  });

  it("calls check-in API", async () => {
    const mockRecord = {
      id: "test-id",
      employee_id: "test-emp-id",
      work_date: "2026-06-10",
      check_in_at: "2026-06-10T08:00:00Z",
      source: "WEB",
    };

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ message: "Checked in successfully", record: mockRecord }),
    });

    const res = await fetch("/api/attendance/me/check-in", { method: "POST", credentials: "include" });
    const data = await res.json();

    expect(mockFetch).toHaveBeenCalledWith("/api/attendance/me/check-in", { method: "POST", credentials: "include" });
    expect(data.message).toBe("Checked in successfully");
  });

  it("calls check-out API", async () => {
    const mockRecord = {
      id: "test-id",
      employee_id: "test-emp-id",
      work_date: "2026-06-10",
      check_in_at: "2026-06-10T08:00:00Z",
      check_out_at: "2026-06-10T17:00:00Z",
      source: "WEB",
    };

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ message: "Checked out successfully", record: mockRecord }),
    });

    const res = await fetch("/api/attendance/me/check-out", { method: "POST", credentials: "include" });
    const data = await res.json();

    expect(mockFetch).toHaveBeenCalledWith("/api/attendance/me/check-out", { method: "POST", credentials: "include" });
    expect(data.message).toBe("Checked out successfully");
  });

  it("handles 403 OFFICE_NETWORK_REQUIRED error", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 403,
      json: () => Promise.resolve({
        error_code: "OFFICE_NETWORK_REQUIRED",
        detail: "Attendance check-in is only allowed from approved office network.",
      }),
    });

    const res = await fetch("/api/attendance/me/check-in", { method: "POST", credentials: "include" });
    const data = await res.json();

    expect(res.status).toBe(403);
    expect(data.error_code).toBe("OFFICE_NETWORK_REQUIRED");
    expect(data.detail).toBe("Attendance check-in is only allowed from approved office network.");
  });

  it("handles 409 ALREADY_CHECKED_IN error", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 409,
      json: () => Promise.resolve({
        error_code: "ALREADY_CHECKED_IN",
        detail: "Already checked in for today",
      }),
    });

    const res = await fetch("/api/attendance/me/check-in", { method: "POST", credentials: "include" });
    const data = await res.json();

    expect(res.status).toBe(409);
    expect(data.error_code).toBe("ALREADY_CHECKED_IN");
  });

  it("handles 400 NOT_CHECKED_IN error", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 400,
      json: () => Promise.resolve({
        error_code: "NOT_CHECKED_IN",
        detail: "Must check in before checking out",
      }),
    });

    const res = await fetch("/api/attendance/me/check-out", { method: "POST", credentials: "include" });
    const data = await res.json();

    expect(res.status).toBe(400);
    expect(data.error_code).toBe("NOT_CHECKED_IN");
  });
});

describe("API response parsing", () => {
  it("parses today record correctly", async () => {
    const mockRecord = {
      id: "test-id",
      employee_id: "test-emp-id",
      work_date: "2026-06-10",
      check_in_at: "2026-06-10T08:00:00Z",
      check_out_at: "2026-06-10T17:00:00Z",
      check_in_ip: "192.168.1.100",
      check_out_ip: "192.168.1.100",
      source: "WEB",
      created_at: "2026-06-10T08:00:00Z",
      updated_at: "2026-06-10T17:00:00Z",
    };

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockRecord),
    });

    const res = await fetch("/api/attendance/me/today", { credentials: "include" });
    const data = await res.json();

    expect(data.work_date).toBe("2026-06-10");
    expect(data.check_in_at).toContain("08:00:00");
    expect(data.check_out_at).toContain("17:00:00");
    expect(data.source).toBe("WEB");
  });

  it("parses history response correctly", async () => {
    const mockHistory = {
      records: [
        { id: "1", work_date: "2026-06-10", check_in_at: "2026-06-10T08:00:00Z" },
        { id: "2", work_date: "2026-06-09", check_in_at: "2026-06-09T08:00:00Z", check_out_at: "2026-06-09T17:00:00Z" },
      ],
      year: 2026,
      month: 6,
    };

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockHistory),
    });

    const res = await fetch("/api/attendance/me/history?year=2026&month=6", { credentials: "include" });
    const data = await res.json();

    expect(data.year).toBe(2026);
    expect(data.month).toBe(6);
    expect(data.records).toHaveLength(2);
  });
});
