/**
 * @vitest-environment jsdom
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import "@testing-library/jest-dom/vitest";
import { render, screen } from "@testing-library/react";
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

});
