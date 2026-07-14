/**
 * @vitest-environment jsdom
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import "@testing-library/jest-dom/vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import React from "react";

// --- Mocks ---

const mockPush = vi.fn();
const mockPathname = vi.fn(() => "/");

vi.mock("next/navigation", () => ({
  usePathname: () => mockPathname(),
  useRouter: () => ({ push: mockPush }),
}));

vi.mock("next/link", () => ({
  __esModule: true,
  default: React.forwardRef<
    HTMLAnchorElement,
    { href: string; children?: React.ReactNode } & Record<string, unknown>
  >(function MockLink({ href, children, ...props }, ref) {
    return React.createElement(
      "a",
      { href, ref, ...props },
      children as React.ReactNode,
    );
  }),
}));

vi.mock("@/components/command-bar", () => ({
  CommandBar: () => null,
}));

// Mock useCurrentUser — we control the return value per test
const mockUseCurrentUser = vi.fn();
vi.mock("@/hooks/use-current-user", () => ({
  useCurrentUser: () => mockUseCurrentUser(),
}));

// Import the component under test AFTER mocks are set up
import { HeaderNavigation } from "../header-navigation";

// --- Test Data ---

const adminUser = {
  id: "1",
  email: "admin@vroom.vn",
  name: "Admin User",
  avatar_url: null,
  role: "admin" as const,
  gmail_grant_valid: false,
  calendar_grant_valid: false,
  created_at: "2024-01-01",
  last_login: "2024-01-01",
};

const employeeUser = {
  id: "2",
  email: "employee@vroom.vn",
  name: "Employee User",
  avatar_url: null,
  role: "user" as const,
  gmail_grant_valid: false,
  calendar_grant_valid: false,
  created_at: "2024-01-01",
  last_login: "2024-01-01",
};

// --- Tests ---

describe("Layout Integration: HeaderNavigation", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockPathname.mockReturnValue("/");
  });

  describe("Admin layout renders HeaderNavigation without AppSidebar", () => {
    it("renders admin navigation groups when user role is admin", () => {
      mockUseCurrentUser.mockReturnValue({
        user: adminUser,
        loading: false,
        error: null,
      });

      render(React.createElement(HeaderNavigation));

      // Admin nav groups should be present
      expect(screen.getByText("Nhân sự")).toBeInTheDocument();
      expect(screen.getByText("Tuyển dụng")).toBeInTheDocument();
      expect(screen.getByText("Chấm công")).toBeInTheDocument();
      expect(screen.getByText("Lương")).toBeInTheDocument();
      expect(screen.getByText("Hệ thống")).toBeInTheDocument();
    });

    it("renders the Vroom logo linking to admin dashboard", () => {
      mockUseCurrentUser.mockReturnValue({
        user: adminUser,
        loading: false,
        error: null,
      });

      render(React.createElement(HeaderNavigation));

      const logoLink = screen.getByRole("link", { name: /V\s*Vroom/i });
      expect(logoLink).toHaveAttribute("href", "/");
    });

    it("does not render any sidebar-related elements", () => {
      mockUseCurrentUser.mockReturnValue({
        user: adminUser,
        loading: false,
        error: null,
      });

      const { container } = render(React.createElement(HeaderNavigation));

      // No sidebar elements should exist
      expect(container.querySelector("[data-sidebar]")).toBeNull();
      expect(container.querySelector("aside")).toBeNull();
    });

    it("renders a navigation element with role=navigation", () => {
      mockUseCurrentUser.mockReturnValue({
        user: adminUser,
        loading: false,
        error: null,
      });

      render(React.createElement(HeaderNavigation));

      expect(screen.getByRole("navigation")).toBeInTheDocument();
    });
  });

  describe("Employee layout renders HeaderNavigation without EmployeeSidebar", () => {
    it("renders ESS navigation groups when user role is user", () => {
      mockUseCurrentUser.mockReturnValue({
        user: employeeUser,
        loading: false,
        error: null,
      });

      render(React.createElement(HeaderNavigation));

      // ESS nav groups should be present (only Hồ sơ — attendance/payroll not live)
      expect(screen.getByText("Hồ sơ")).toBeInTheDocument();
    });

    it("does NOT render admin-specific navigation groups", () => {
      mockUseCurrentUser.mockReturnValue({
        user: employeeUser,
        loading: false,
        error: null,
      });

      render(React.createElement(HeaderNavigation));

      // Admin-only groups should NOT be present
      expect(screen.queryByText("Nhân sự")).not.toBeInTheDocument();
      expect(screen.queryByText("Tuyển dụng")).not.toBeInTheDocument();
      expect(screen.queryByText("Hệ thống")).not.toBeInTheDocument();
    });

    it("renders the Vroom ESS logo linking to employee dashboard", () => {
      mockUseCurrentUser.mockReturnValue({
        user: employeeUser,
        loading: false,
        error: null,
      });

      render(React.createElement(HeaderNavigation));

      const logoLink = screen.getByRole("link", { name: /V\s*Vroom ESS/i });
      expect(logoLink).toHaveAttribute("href", "/employee/dashboard");
    });

    it("does not render any sidebar-related elements", () => {
      mockUseCurrentUser.mockReturnValue({
        user: employeeUser,
        loading: false,
        error: null,
      });

      const { container } = render(React.createElement(HeaderNavigation));

      expect(container.querySelector("[data-sidebar]")).toBeNull();
      expect(container.querySelector("aside")).toBeNull();
    });
  });

  describe("Unauthenticated state redirects to login", () => {
    it("redirects to /login when user is null", () => {
      mockUseCurrentUser.mockReturnValue({
        user: null,
        loading: false,
        error: null,
      });

      render(React.createElement(HeaderNavigation));

      expect(mockPush).toHaveBeenCalledWith("/login");
    });

    it("renders minimal header with no navigation items when unauthenticated", () => {
      mockUseCurrentUser.mockReturnValue({
        user: null,
        loading: false,
        error: null,
      });

      render(React.createElement(HeaderNavigation));

      // No nav groups should be rendered
      expect(screen.queryByText("Nhân sự")).not.toBeInTheDocument();
      expect(screen.queryByText("Hồ sơ")).not.toBeInTheDocument();
      expect(screen.queryByRole("navigation")).not.toBeInTheDocument();
    });

    it("renders error message when user fetch fails", () => {
      mockUseCurrentUser.mockReturnValue({
        user: null,
        loading: false,
        error: "Network error",
      });

      render(React.createElement(HeaderNavigation));

      expect(
        screen.getByText("Không thể tải thông tin người dùng"),
      ).toBeInTheDocument();
    });
  });

  describe("Role-based view switching", () => {
    it("admin role renders all 5 admin navigation groups", () => {
      mockUseCurrentUser.mockReturnValue({
        user: adminUser,
        loading: false,
        error: null,
      });

      render(React.createElement(HeaderNavigation));

      const adminGroups = [
        "Nhân sự",
        "Tuyển dụng",
        "Chấm công",
        "Lương",
        "Hệ thống",
      ];
      for (const group of adminGroups) {
        expect(screen.getByText(group)).toBeInTheDocument();
      }
    });

    it("user role renders ESS navigation groups (Hồ sơ only)", () => {
      mockUseCurrentUser.mockReturnValue({
        user: employeeUser,
        loading: false,
        error: null,
      });

      render(React.createElement(HeaderNavigation));

      // Only Hồ sơ is live; attendance/payroll hidden
      expect(screen.getByText("Hồ sơ")).toBeInTheDocument()
    });

    it("invalid role redirects to login", () => {
      mockUseCurrentUser.mockReturnValue({
        user: { ...adminUser, role: "invalid" },
        loading: false,
        error: null,
      });

      render(React.createElement(HeaderNavigation));

      expect(mockPush).toHaveBeenCalledWith("/login");
    });

    it("renders loading skeleton when user data is being fetched", () => {
      mockUseCurrentUser.mockReturnValue({
        user: null,
        loading: true,
        error: null,
      });

      const { container } = render(React.createElement(HeaderNavigation));

      // Should render a loading skeleton (animate-pulse element)
      expect(container.querySelector(".animate-pulse")).toBeInTheDocument();
      // Should NOT render any nav groups
      expect(screen.queryByText("Nhân sự")).not.toBeInTheDocument();
      expect(screen.queryByText("Hồ sơ")).not.toBeInTheDocument();
      });

      it("does not show an unread badge and opens an observable empty state", async () => {
        mockUseCurrentUser.mockReturnValue({
          user: adminUser,
          loading: false,
          error: null,
        });
        render(React.createElement(HeaderNavigation));
        expect(screen.queryByText("3")).not.toBeInTheDocument();
        fireEvent.click(screen.getByRole("button", { name: "Thông báo" }));
        expect(await screen.findByText("Bạn không có thông báo mới.")).toBeInTheDocument();
      });
    });
  });
