/**
 * @vitest-environment jsdom
 */
import "@testing-library/jest-dom";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, it, expect, vi, beforeEach } from "vitest";
import type { ReactNode } from "react";

// Mock sonner toast
vi.mock("sonner", () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}));

// Mock fetch globally
const mockFetch = vi.fn();
global.fetch = mockFetch;

// Lazy reference to page component
let RequestsPage: React.ComponentType;

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });
  return function Wrapper({ children }: { children: ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>
        {children}
      </QueryClientProvider>
    );
  };
}

beforeEach(async () => {
  mockFetch.mockReset();
  vi.clearAllMocks();

  const pageModule = await import("../page");
  RequestsPage = pageModule.default;
});

// ---- Sample data ----

const mockRequests = {
  requests: [
    {
      id: "leave-1",
      employee_id: "emp-1",
      request_type: "leave",
      status: "submitted",
      submitted_at: "2026-06-10T08:00:00Z",
      updated_at: "2026-06-10T08:00:00Z",
      work_date: null,
      start_time: null,
      end_time: null,
      duration_minutes: null,
      leave_type: "annual",
      start_date: "2026-06-15",
      end_date: "2026-06-16",
      reason: "Nghỉ phép năm 2 ngày",
      project_or_task: null,
      cancellation_reason: null,
    },
    {
      id: "ot-1",
      employee_id: "emp-1",
      request_type: "overtime",
      status: "approved",
      submitted_at: "2026-06-09T17:00:00Z",
      updated_at: "2026-06-10T09:00:00Z",
      work_date: "2026-06-10",
      start_time: "18:00",
      end_time: "20:30",
      duration_minutes: 150,
      leave_type: null,
      start_date: null,
      end_date: null,
      reason: "Xử lý báo cáo cuối quý",
      project_or_task: "Báo cáo Q2",
      cancellation_reason: null,
    },
    {
      id: "leave-2",
      employee_id: "emp-1",
      request_type: "leave",
      status: "rejected",
      submitted_at: "2026-06-01T08:00:00Z",
      updated_at: "2026-06-02T10:00:00Z",
      work_date: null,
      start_time: null,
      end_time: null,
      duration_minutes: null,
      leave_type: "sick",
      start_date: "2026-06-01",
      end_date: "2026-06-01",
      reason: "Bị ốm",
      project_or_task: null,
      cancellation_reason: null,
    },
  ],
};

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("EmployeeRequestsPage loading state", () => {
  it("shows skeleton while fetching", () => {
    mockFetch.mockImplementation(() => new Promise(() => {})); // never resolves

    render(<RequestsPage />, { wrapper: createWrapper() });

    // Page header renders immediately
    expect(screen.getByText("Yêu cầu của tôi")).toBeInTheDocument();

    // Skeleton rows should appear
    const skeletons = document.querySelectorAll(".animate-pulse");
    expect(skeletons.length).toBeGreaterThan(0);
  });
});

describe("EmployeeRequestsPage empty state", () => {
  it("shows empty message when no requests", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ requests: [] }),
    });

    render(<RequestsPage />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText("Chưa có yêu cầu nào.")).toBeInTheDocument();
    });
  });

  it("shows create button in empty state", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ requests: [] }),
    });

    render(<RequestsPage />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /Tạo yêu cầu/i })).toBeInTheDocument();
    });
  });
});

describe("EmployeeRequestsPage list items", () => {
  it("renders all request types and statuses", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockRequests,
    });

    render(<RequestsPage />, { wrapper: createWrapper() });

    // Wait for reason text — signals data has loaded
    await waitFor(() => {
      expect(screen.getByText("Nghỉ phép năm 2 ngày")).toBeInTheDocument();
    });

    // Status badges
    expect(screen.getByText("Đã gửi")).toBeInTheDocument();
    expect(screen.getByText("Đã duyệt")).toBeInTheDocument();
    expect(screen.getByText("Từ chối")).toBeInTheDocument();
  });

  it("renders reason text for each request", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockRequests,
    });

    render(<RequestsPage />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText("Nghỉ phép năm 2 ngày")).toBeInTheDocument();
      expect(screen.getByText("Xử lý báo cáo cuối quý")).toBeInTheDocument();
      expect(screen.getByText("Bị ốm")).toBeInTheDocument();
    });
  });

  it("shows cancel button only for submitted requests", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockRequests,
    });

    render(<RequestsPage />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText("Nghỉ phép năm 2 ngày")).toBeInTheDocument();
    });

    // The submitted request (leave-1) should have a cancel button
    // Other renderings of "Huỷ" come from the CreateRequestDialog cancel button text
    // Check the XCircle icon button specifically — only one visible
    const cancelButtons = screen.getAllByRole("button");
    const huyButtons = cancelButtons.filter(
      (btn) => btn.textContent?.includes("Huỷ") && !btn.textContent?.includes("Huỷ bỏ")
    );
    // At least one cancel button for submitted request
    expect(huyButtons.length).toBeGreaterThanOrEqual(1);
  });

  it("does not show cancel button for non-submitted requests", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        requests: [
          {
            ...mockRequests.requests[1], // approved overtime
          },
        ],
      }),
    });

    render(<RequestsPage />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText("Xử lý báo cáo cuối quý")).toBeInTheDocument();
    });

    // No card-level cancel buttons should exist for non-submitted
    // The only "Huỷ" text is in the create dialog's cancel button
    const cancelButtons = screen.getAllByRole("button");
    const huyButtons = cancelButtons.filter(
      (btn) => btn.textContent?.includes("Huỷ") && !btn.textContent?.includes("Huỷ bỏ")
    );
    // Only the dialog "Huỷ" button exists (inside CreateRequestDialog, not visible)
    // Since dialog is closed, its buttons aren't in the DOM
    expect(huyButtons.length).toBe(0);
  });
});

describe("EmployeeRequestsPage filter tabs", () => {
  it("defaults to 'Tất cả' and shows all items", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockRequests,
    });

    render(<RequestsPage />, { wrapper: createWrapper() });

    const allTab = screen.getByRole("tab", { name: /Tất cả/i });
    expect(allTab).toHaveAttribute("data-state", "active");

    await waitFor(() => {
      expect(screen.getByText("Nghỉ phép năm 2 ngày")).toBeInTheDocument();
      expect(screen.getByText("Xử lý báo cáo cuối quý")).toBeInTheDocument();
      expect(screen.getByText("Bị ốm")).toBeInTheDocument();
    });
  });

  it("filters to leave requests when clicking Nghỉ phép tab", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockRequests,
    });

    render(<RequestsPage />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText("Nghỉ phép năm 2 ngày")).toBeInTheDocument();
    });

    const leaveTab = screen.getByRole("tab", { name: /^Nghỉ phép$/ });
    await userEvent.click(leaveTab);

    expect(screen.getByText("Nghỉ phép năm 2 ngày")).toBeInTheDocument();
    expect(screen.getByText("Bị ốm")).toBeInTheDocument();
    expect(screen.queryByText("Xử lý báo cáo cuối quý")).not.toBeInTheDocument();
  });

  it("filters to overtime requests when clicking Tăng ca tab", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockRequests,
    });

    render(<RequestsPage />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText("Xử lý báo cáo cuối quý")).toBeInTheDocument();
    });

    const otTab = screen.getByRole("tab", { name: /Tăng ca/i });
    await userEvent.click(otTab);

    expect(screen.getByText("Xử lý báo cáo cuối quý")).toBeInTheDocument();
    expect(screen.queryByText("Nghỉ phép năm 2 ngày")).not.toBeInTheDocument();
    expect(screen.queryByText("Bị ốm")).not.toBeInTheDocument();
  });

  it("shows filter-specific empty message when no requests match", async () => {
    // Return only overtime requests, switch to leave tab
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        requests: [mockRequests.requests[1]], // only overtime
      }),
    });

    render(<RequestsPage />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText("Xử lý báo cáo cuối quý")).toBeInTheDocument();
    });

    const leaveTab = screen.getByRole("tab", { name: /^Nghỉ phép$/ });
    await userEvent.click(leaveTab);

    expect(screen.getByText("Chưa có đơn nghỉ phép nào.")).toBeInTheDocument();
  });
});

describe("EmployeeRequestsPage error state", () => {
  it("shows error message when fetch fails", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 500,
      json: async () => ({ detail: "Internal server error" }),
    });

    render(<RequestsPage />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText("Không thể tải dữ liệu")).toBeInTheDocument();
    });
  });

  it("calls toast.error on fetch failure", async () => {
    const { toast } = await import("sonner");

    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 500,
      json: async () => ({ detail: "Internal server error" }),
    });

    render(<RequestsPage />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalled();
    });
  });
});
