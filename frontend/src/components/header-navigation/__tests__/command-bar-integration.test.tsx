/**
 * @vitest-environment jsdom
 */
import {
  describe,
  it,
  expect,
  vi,
  beforeAll,
  beforeEach,
  afterEach,
} from "vitest";
import {
  render,
  screen,
  fireEvent,
  waitFor,
  act,
  within,
} from "@testing-library/react";
import "@testing-library/jest-dom";

import { navItems } from "@/lib/navigation";

// --- Polyfills for jsdom (required by cmdk/radix) ---
beforeAll(() => {
  // ResizeObserver polyfill
  global.ResizeObserver = class ResizeObserver {
    observe() {}
    unobserve() {}
    disconnect() {}
  };

  // Pointer event polyfills
  if (!Element.prototype.hasPointerCapture) {
    Element.prototype.hasPointerCapture = () => false;
    Element.prototype.setPointerCapture = () => {};
    Element.prototype.releasePointerCapture = () => {};
  }

  // scrollIntoView polyfill
  if (!Element.prototype.scrollIntoView) {
    Element.prototype.scrollIntoView = () => {};
  }
});

// --- Mocks ---

// Mock next/navigation
const mockPush = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush }),
  usePathname: () => "/",
}));

// Mock useCurrentUser to return an admin user
vi.mock("@/hooks/use-current-user", () => ({
  useCurrentUser: () => ({
    user: {
      id: "1",
      email: "admin@vroom.hr",
      name: "Admin User",
      avatar_url: null,
      role: "admin" as const,
      gmail_grant_valid: false,
      calendar_grant_valid: false,
      created_at: "2024-01-01",
      last_login: "2024-01-01",
    },
    loading: false,
    error: null,
    refetch: vi.fn(),
  }),
}));

// Mock @tanstack/react-query
vi.mock("@tanstack/react-query", () => ({
  useQuery: vi.fn(),
  useQueryClient: () => ({ invalidateQueries: vi.fn() }),
  QueryClient: vi.fn(),
  QueryClientProvider: ({ children }: { children: React.ReactNode }) =>
    children,
}));

// Import after mocks
import { HeaderNavigation } from "../header-navigation";

describe("CommandBar integration with HeaderNavigation", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe("Keyboard shortcut (Ctrl+K / ⌘K) — Requirements 10.5", () => {
    it("opens CommandBar when Ctrl+K is pressed", async () => {
      render(<HeaderNavigation />);

      // CommandBar dialog should not be visible initially
      expect(
        screen.queryByPlaceholderText("Tìm kiếm trang..."),
      ).not.toBeInTheDocument();

      // Simulate Ctrl+K
      act(() => {
        fireEvent.keyDown(document, { key: "k", ctrlKey: true });
      });

      // CommandBar should now be visible
      await waitFor(() => {
        expect(
          screen.getByPlaceholderText("Tìm kiếm trang..."),
        ).toBeInTheDocument();
      });
    });

    it("opens CommandBar when ⌘K (Meta+K) is pressed", async () => {
      render(<HeaderNavigation />);

      expect(
        screen.queryByPlaceholderText("Tìm kiếm trang..."),
      ).not.toBeInTheDocument();

      // Simulate ⌘K (macOS)
      act(() => {
        fireEvent.keyDown(document, { key: "k", metaKey: true });
      });

      await waitFor(() => {
        expect(
          screen.getByPlaceholderText("Tìm kiếm trang..."),
        ).toBeInTheDocument();
      });
    });

    it("toggles CommandBar closed when Ctrl+K is pressed again", async () => {
      render(<HeaderNavigation />);

      // Open
      act(() => {
        fireEvent.keyDown(document, { key: "k", ctrlKey: true });
      });

      await waitFor(() => {
        expect(
          screen.getByPlaceholderText("Tìm kiếm trang..."),
        ).toBeInTheDocument();
      });

      // Close
      act(() => {
        fireEvent.keyDown(document, { key: "k", ctrlKey: true });
      });

      await waitFor(() => {
        expect(
          screen.queryByPlaceholderText("Tìm kiếm trang..."),
        ).not.toBeInTheDocument();
      });
    });
  });

  describe("CommandBar contains all navigation items — Requirements 10.5", () => {
    it("contains all navItems from navigation config", async () => {
      render(<HeaderNavigation />);

      // Open CommandBar
      act(() => {
        fireEvent.keyDown(document, { key: "k", ctrlKey: true });
      });

      await waitFor(() => {
        expect(
          screen.getByPlaceholderText("Tìm kiếm trang..."),
        ).toBeInTheDocument();
      });

      // Get the dialog container to scope queries
      const dialog = screen.getByRole("dialog");

      // Verify all navItems are present within the CommandBar dialog
      for (const item of navItems) {
        expect(
          within(dialog).getAllByText(item.label).length,
        ).toBeGreaterThanOrEqual(1);
      }
    });

    it("contains additional command bar items (recruitment/review, recruitment/metrics)", async () => {
      render(<HeaderNavigation />);

      // Open CommandBar
      act(() => {
        fireEvent.keyDown(document, { key: "k", ctrlKey: true });
      });

      await waitFor(() => {
        expect(
          screen.getByPlaceholderText("Tìm kiếm trang..."),
        ).toBeInTheDocument();
      });

      const dialog = screen.getByRole("dialog");

      // Verify additional items are present
      expect(within(dialog).getByText("Xem xét CV")).toBeInTheDocument();
      expect(within(dialog).getByText("Số liệu Pipeline")).toBeInTheDocument();
    });
  });

  describe("Item selection behavior — Requirements 10.6", () => {
    it("navigates to selected route when an item is selected", async () => {
      render(<HeaderNavigation />);

      // Open CommandBar
      act(() => {
        fireEvent.keyDown(document, { key: "k", ctrlKey: true });
      });

      await waitFor(() => {
        expect(
          screen.getByPlaceholderText("Tìm kiếm trang..."),
        ).toBeInTheDocument();
      });

      // Select an item — "Nhân viên" links to /employees
      // Use the dialog scope to avoid ambiguity
      const dialog = screen.getByRole("dialog");
      const employeeItem = within(dialog).getByText("Nhân viên");
      act(() => {
        fireEvent.click(employeeItem);
      });

      // Verify navigation was triggered
      await waitFor(() => {
        expect(mockPush).toHaveBeenCalledWith("/employees");
      });
    });

    it("closes CommandBar after item selection", async () => {
      render(<HeaderNavigation />);

      // Open CommandBar
      act(() => {
        fireEvent.keyDown(document, { key: "k", ctrlKey: true });
      });

      await waitFor(() => {
        expect(
          screen.getByPlaceholderText("Tìm kiếm trang..."),
        ).toBeInTheDocument();
      });

      // Select an item
      const dialog = screen.getByRole("dialog");
      const item = within(dialog).getByText("Nhân viên");
      act(() => {
        fireEvent.click(item);
      });

      // CommandBar should close
      await waitFor(() => {
        expect(
          screen.queryByPlaceholderText("Tìm kiếm trang..."),
        ).not.toBeInTheDocument();
      });
    });

    it("navigation and close happen synchronously on selection (within 300ms)", async () => {
      render(<HeaderNavigation />);

      // Open CommandBar
      act(() => {
        fireEvent.keyDown(document, { key: "k", ctrlKey: true });
      });

      await waitFor(() => {
        expect(
          screen.getByPlaceholderText("Tìm kiếm trang..."),
        ).toBeInTheDocument();
      });

      // Select an item — the onSelect handler calls router.push and onOpenChange(false)
      // synchronously, so navigation happens immediately (well within 300ms)
      const dialog = screen.getByRole("dialog");
      const item = within(dialog).getByText("Tổng quan");

      act(() => {
        fireEvent.click(item);
      });

      // Navigation should have been called immediately (synchronous)
      expect(mockPush).toHaveBeenCalledWith("/");

      // CommandBar should close
      await waitFor(() => {
        expect(
          screen.queryByPlaceholderText("Tìm kiếm trang..."),
        ).not.toBeInTheDocument();
      });
    });
  });

  describe("Search trigger button", () => {
    it("opens CommandBar when search button is clicked", async () => {
      render(<HeaderNavigation />);

      // Find and click the search trigger button
      const searchButton = screen.getByLabelText("Tìm kiếm (Ctrl+K)");

      await act(async () => {
        fireEvent.click(searchButton);
      });

      // CommandBar should open
      await waitFor(() => {
        expect(
          screen.getByPlaceholderText("Tìm kiếm trang..."),
        ).toBeInTheDocument();
      });
    });
  });
});
