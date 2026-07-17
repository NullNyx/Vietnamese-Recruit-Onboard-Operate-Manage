import { describe, it, expect } from "vitest";
import { useActiveNavItem } from "./use-active-nav-item";
import type { NavGroup } from "@/lib/header-nav-config";

const mockNavGroups: NavGroup[] = [
  {
    id: "nhan-su",
    label: "Nhân sự",
    links: [
      { href: "/employees", label: "Danh sách NV" },
      { href: "/settings/departments", label: "Phòng ban" },
      { href: "/settings/positions", label: "Chức vụ" },
    ],
    activeRoutes: [
      "/employees",
      "/settings/departments",
      "/settings/positions",
    ],
  },
  {
    id: "tuyen-dung",
    label: "Tuyển dụng",
    links: [
      { href: "/recruitment", label: "Pipeline" },
      { href: "/recruitment/candidates", label: "Ứng viên" },
      { href: "/recruitment/metrics", label: "Metrics" },
    ],
    activeRoutes: ["/recruitment"],
  },
  {
    id: "cham-cong",
    label: "Chấm công",
    links: [
      { href: "/attendance/checkin", label: "Check-in" },
      { href: "/attendance/schedules", label: "Lịch làm" },
      { href: "/attendance/leave", label: "Nghỉ phép" },
    ],
    activeRoutes: ["/attendance"],
  },
  {
    id: "luong",
    label: "Lương",
    links: [
      { href: "/payroll", label: "Bảng lương" },
      { href: "/payroll/config", label: "Cấu hình" },
    ],
    activeRoutes: ["/payroll"],
  },
];

describe("useActiveNavItem", () => {
  it("returns null for both fields when pathname does not match any group", () => {
    const result = useActiveNavItem(mockNavGroups, "/unknown-page");
    expect(result).toEqual({ activeGroupId: null, activeSubLinkHref: null });
  });

  it("returns the correct activeGroupId when pathname matches an activeRoute prefix", () => {
    const result = useActiveNavItem(mockNavGroups, "/attendance/checkin");
    expect(result.activeGroupId).toBe("cham-cong");
  });

  it("returns activeSubLinkHref when pathname exactly matches a sub-link href", () => {
    const result = useActiveNavItem(mockNavGroups, "/attendance/checkin");
    expect(result.activeSubLinkHref).toBe("/attendance/checkin");
  });

  it("returns activeGroupId but null activeSubLinkHref when pathname matches prefix but not a sub-link", () => {
    const result = useActiveNavItem(
      mockNavGroups,
      "/attendance/some-other-page",
    );
    expect(result.activeGroupId).toBe("cham-cong");
    expect(result.activeSubLinkHref).toBeNull();
  });

  it("returns the first matching group when multiple groups could match (first match wins)", () => {
    const groups: NavGroup[] = [
      {
        id: "group-a",
        label: "Group A",
        links: [{ href: "/shared/page", label: "Page" }],
        activeRoutes: ["/shared"],
      },
      {
        id: "group-b",
        label: "Group B",
        links: [{ href: "/shared/other", label: "Other" }],
        activeRoutes: ["/shared"],
      },
    ];
    const result = useActiveNavItem(groups, "/shared/page");
    expect(result.activeGroupId).toBe("group-a");
  });

  it("matches exact route without trailing slash", () => {
    const result = useActiveNavItem(mockNavGroups, "/employees");
    expect(result.activeGroupId).toBe("nhan-su");
    expect(result.activeSubLinkHref).toBe("/employees");
  });

  it("matches sub-paths of an activeRoute prefix", () => {
    const result = useActiveNavItem(mockNavGroups, "/recruitment/candidates");
    expect(result.activeGroupId).toBe("tuyen-dung");
    expect(result.activeSubLinkHref).toBe("/recruitment/candidates");
  });

  it("does not match partial prefix (e.g., /pay should not match /payroll)", () => {
    const result = useActiveNavItem(mockNavGroups, "/pay");
    expect(result.activeGroupId).toBeNull();
    expect(result.activeSubLinkHref).toBeNull();
  });

  it("handles empty navGroups array", () => {
    const result = useActiveNavItem([], "/employees");
    expect(result).toEqual({ activeGroupId: null, activeSubLinkHref: null });
  });

  it("handles root pathname '/'", () => {
    const result = useActiveNavItem(mockNavGroups, "/");
    expect(result).toEqual({ activeGroupId: null, activeSubLinkHref: null });
  });

  it("activates group when sub-link href matches even if not in activeRoutes", () => {
    const groups: NavGroup[] = [
      {
        id: "system",
        label: "Hệ thống",
        links: [
          { href: "/admin/users", label: "Users" },
          { href: "/gmail", label: "Gmail" },
        ],
        activeRoutes: ["/admin"],
      },
    ];
    // /gmail is a sub-link but not covered by activeRoutes prefix /admin
    const result = useActiveNavItem(groups, "/gmail");
    expect(result.activeGroupId).toBe("system");
    expect(result.activeSubLinkHref).toBe("/gmail");
  });

  it("returns at most one active group", () => {
    const result = useActiveNavItem(mockNavGroups, "/payroll/config");
    expect(result.activeGroupId).toBe("luong");
    expect(result.activeSubLinkHref).toBe("/payroll/config");
    // Verify only one group is active (no array, just a single value)
    expect(typeof result.activeGroupId).toBe("string");
  });
});
