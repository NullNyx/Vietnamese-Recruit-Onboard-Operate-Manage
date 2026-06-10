/**
 * @vitest-environment jsdom
 */
import "@testing-library/jest-dom";
import { render, screen, waitFor } from "@testing-library/react";
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
  ToastProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

// Mock fetch globally
const mockFetch = vi.fn();
global.fetch = mockFetch;

// Dynamically import the page component
let AttendancePage: React.ComponentType;

beforeEach(async () => {
  mockFetch.mockReset();
  vi.clearAllMocks();
  
  // Import the page component lazily
  const pageModule = await import("../page");
  AttendancePage = pageModule.default;
});

describe("EmployeeAttendancePage UI states", () => {
  it("renders page header", async () => {
    mockFetch.mockImplementation(() => new Promise(() => {})); // Never resolves
    
    render(<AttendancePage />);
    
    expect(screen.getByText("Chấm công")).toBeInTheDocument();
    expect(screen.getByText("Check-in/check-out và xem lịch sử chấm công")).toBeInTheDocument();
  });

  it("shows empty state when no record", async () => {
    mockFetch
      .mockResolvedValueOnce({ ok: true, json: async () => null })
      .mockResolvedValueOnce({ ok: true, json: async () => ({ records: [], year: 2026, month: 6 }) });

    render(<AttendancePage />);

    await waitFor(() => {
      expect(screen.getByText("Chưa điểm danh")).toBeInTheDocument();
      expect(screen.getByText("Bạn chưa check-in hôm nay")).toBeInTheDocument();
    });
  });

  it("shows checked-in state", async () => {
    const record = {
      id: "test-id",
      employee_id: "test-emp-id",
      work_date: "2026-06-10",
      check_in_at: "2026-06-10T08:00:00Z",
      check_out_at: null,
      check_in_ip: "192.168.1.100",
      check_out_ip: null,
      source: "WEB",
      created_at: "2026-06-10T08:00:00Z",
      updated_at: "2026-06-10T08:00:00Z",
    };

    mockFetch
      .mockResolvedValueOnce({ ok: true, json: async () => record })
      .mockResolvedValueOnce({ ok: true, json: async () => ({ records: [record], year: 2026, month: 6 }) });

    render(<AttendancePage />);

    await waitFor(() => {
      expect(screen.getAllByText("Đã check-in").length).toBeGreaterThan(0);
      expect(screen.getByText(/Check-in:/)).toBeInTheDocument();
    });
  });

  it("shows completed state", async () => {
    const record = {
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

    mockFetch
      .mockResolvedValueOnce({ ok: true, json: async () => record })
      .mockResolvedValueOnce({ ok: true, json: async () => ({ records: [record], year: 2026, month: 6 }) });

    render(<AttendancePage />);

    await waitFor(() => {
      expect(screen.getAllByText("Hoàn thành").length).toBeGreaterThanOrEqual(2);
    });
  });

  it("shows error state when blocked by network (403)", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 403,
      json: async () => ({
        error_code: "OFFICE_NETWORK_REQUIRED",
        detail: "Attendance check-in is only allowed from approved office network.",
      }),
    });

    render(<AttendancePage />);

    await waitFor(() => {
      expect(screen.getByText("Lỗi mạng")).toBeInTheDocument();
      expect(screen.getByText(/Attendance check-in is only allowed/)).toBeInTheDocument();
    });
  });

  it("shows Check-in button when empty state", async () => {
    mockFetch
      .mockResolvedValueOnce({ ok: true, json: async () => null })
      .mockResolvedValueOnce({ ok: true, json: async () => ({ records: [], year: 2026, month: 6 }) });

    render(<AttendancePage />);

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /Check-in/i })).toBeInTheDocument();
    });
  });

  it("shows Check-out button when checked-in state", async () => {
    const record = {
      id: "test-id",
      employee_id: "test-emp-id",
      work_date: "2026-06-10",
      check_in_at: "2026-06-10T08:00:00Z",
      check_out_at: null,
      check_in_ip: "192.168.1.100",
      source: "WEB",
    };

    mockFetch
      .mockResolvedValueOnce({ ok: true, json: async () => record })
      .mockResolvedValueOnce({ ok: true, json: async () => ({ records: [], year: 2026, month: 6 }) });

    render(<AttendancePage />);

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /Check-out/i })).toBeInTheDocument();
    });
  });

  it("shows disabled button when completed state", async () => {
    const record = {
      id: "test-id",
      employee_id: "test-emp-id",
      work_date: "2026-06-10",
      check_in_at: "2026-06-10T08:00:00Z",
      check_out_at: "2026-06-10T17:00:00Z",
      check_in_ip: "192.168.1.100",
      check_out_ip: "192.168.1.100",
      source: "WEB",
    };

    mockFetch
      .mockResolvedValueOnce({ ok: true, json: async () => record })
      .mockResolvedValueOnce({ ok: true, json: async () => ({ records: [], year: 2026, month: 6 }) });

    render(<AttendancePage />);

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /Đã hoàn thành/i })).toBeInTheDocument();
    });
  });

  it("renders history section", async () => {
    mockFetch
      .mockResolvedValueOnce({ ok: true, json: async () => null })
      .mockResolvedValueOnce({ ok: true, json: async () => ({ records: [], year: 2026, month: 6 }) });

    render(<AttendancePage />);

    await waitFor(() => {
      expect(screen.getByText("Lịch sử chấm công")).toBeInTheDocument();
    });
  });

  it("shows empty history message when no records", async () => {
    mockFetch
      .mockResolvedValueOnce({ ok: true, json: async () => null })
      .mockResolvedValueOnce({ ok: true, json: async () => ({ records: [], year: 2026, month: 6 }) });

    render(<AttendancePage />);

    await waitFor(() => {
      expect(screen.getByText("Chưa có bản ghi chấm công trong tháng này.")).toBeInTheDocument();
    });
  });

  it("renders history records in table", async () => {
    const records = [
      {
        id: "1",
        employee_id: "test-emp-id",
        work_date: "2026-06-10",
        check_in_at: "2026-06-10T08:00:00Z",
        check_out_at: "2026-06-10T17:00:00Z",
        check_in_ip: "192.168.1.100",
        check_out_ip: "192.168.1.100",
        source: "WEB",
      },
      {
        id: "2",
        employee_id: "test-emp-id",
        work_date: "2026-06-09",
        check_in_at: "2026-06-09T08:00:00Z",
        check_out_at: null,
        check_in_ip: "192.168.1.100",
        source: "WEB",
      },
    ];

    mockFetch
      .mockResolvedValueOnce({ ok: true, json: async () => null })
      .mockResolvedValueOnce({ ok: true, json: async () => ({ records, year: 2026, month: 6 }) });

    render(<AttendancePage />);

    await waitFor(() => {
      expect(screen.getAllByText("Hoàn thành").length).toBeGreaterThan(0);
      expect(screen.getAllByText("Đã check-in").length).toBeGreaterThan(0);
    });
  });
});
