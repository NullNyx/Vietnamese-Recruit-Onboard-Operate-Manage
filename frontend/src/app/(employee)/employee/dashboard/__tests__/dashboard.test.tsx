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

// Mock fetch globally
const mockFetch = vi.fn();
global.fetch = mockFetch;

let DashboardPage: React.ComponentType;

beforeEach(async () => {
  mockFetch.mockReset();
  vi.clearAllMocks();

  const pageModule = await import("../page");
  DashboardPage = pageModule.default;
});

describe("EmployeeDashboardPage", () => {
  it("renders heading", async () => {
    mockFetch.mockImplementation(() => new Promise(() => {})); // never resolves

    render(<DashboardPage />);

    expect(screen.getByText("Tổng quan")).toBeInTheDocument();
    expect(
      screen.getByText("Chào mừng bạn đến với Employee Self-Service"),
    ).toBeInTheDocument();
  });

  it("renders all four quick action links", async () => {
    mockFetch.mockImplementation(() => new Promise(() => {}));

    render(<DashboardPage />);

    expect(screen.getByText("Hồ sơ cá nhân")).toBeInTheDocument();
    expect(screen.getByText("Tài liệu")).toBeInTheDocument();
    expect(screen.getByText("Chấm công")).toBeInTheDocument();
    expect(screen.getByText("Yêu cầu")).toBeInTheDocument();
  });

  it("quick action links point to correct routes", async () => {
    mockFetch.mockImplementation(() => new Promise(() => {}));

    render(<DashboardPage />);

    const profileLink = screen.getByText("Hồ sơ cá nhân").closest("a");
    expect(profileLink).toHaveAttribute("href", "/employee/profile");

    const docsLink = screen.getByText("Tài liệu").closest("a");
    expect(docsLink).toHaveAttribute("href", "/employee/documents");

    const attendanceLink = screen.getByText("Chấm công").closest("a");
    expect(attendanceLink).toHaveAttribute("href", "/employee/attendance");

    const requestsLink = screen.getByText("Yêu cầu").closest("a");
    expect(requestsLink).toHaveAttribute("href", "/employee/requests");
  });

  it("shows loading state for attendance status initially", async () => {
    mockFetch.mockImplementation(() => new Promise(() => {}));

    render(<DashboardPage />);

    expect(screen.getByText("Đang tải...")).toBeInTheDocument();
  });

  it("shows empty attendance state when no record", async () => {
    mockFetch.mockResolvedValueOnce({ ok: true, json: async () => null });

    render(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByText("Chưa check-in")).toBeInTheDocument();
      expect(
        screen.getByText("Chưa check-in hôm nay"),
      ).toBeInTheDocument();
    });
  });

  it("shows checked-in attendance state", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        check_in_at: "2026-06-10T08:00:00Z",
        check_out_at: null,
      }),
    });

    render(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByText("Đã check-in")).toBeInTheDocument();
    });
  });

  it("shows completed attendance state", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        check_in_at: "2026-06-10T08:00:00Z",
        check_out_at: "2026-06-10T17:00:00Z",
      }),
    });

    render(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByText("Đã hoàn tất")).toBeInTheDocument();
    });
  });

  it("shows error state when fetch fails", async () => {
    mockFetch.mockResolvedValueOnce({ ok: false, status: 500 });

    render(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByText("Không tải được")).toBeInTheDocument();
    });
  });

  it("shows AI Assistant hint", async () => {
    mockFetch.mockImplementation(() => new Promise(() => {}));

    render(<DashboardPage />);

    expect(screen.getByText("AI Assistant")).toBeInTheDocument();
  });

  it("requests card links to requests page", async () => {
    mockFetch.mockImplementation(() => new Promise(() => {}));

    render(<DashboardPage />);

    const requestsCard = screen.getByText("Yêu cầu chờ duyệt").closest("a");
    expect(requestsCard).toHaveAttribute("href", "/employee/requests");
  });
});
