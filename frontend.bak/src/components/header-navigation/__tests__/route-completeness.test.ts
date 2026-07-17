import { describe, it, expect } from "vitest";
import { adminNavConfig } from "@/lib/admin-nav-config";
import { essNavConfig } from "@/lib/ess-nav-config";
import { navItems, adminNavSection } from "@/lib/navigation";
import { employeeNavItems } from "@/lib/employee-navigation";

/**
 * Route Completeness Tests
 * Validates: Requirements 10.1, 10.2, 10.3, 10.4
 *
 * Verifies that all routes previously accessible via the sidebar navigation
 * are present in the new header navigation configs, ensuring no functionality
 * is lost during the redesign.
 */

/** Extract all hrefs from a HeaderNavConfig */
function getAllHrefs(config: typeof adminNavConfig): string[] {
  const hrefs: string[] = [config.logo.href];
  for (const group of config.groups) {
    for (const link of group.links) {
      hrefs.push(link.href);
    }
  }
  return hrefs;
}

  describe("Route Completeness: All existing routes are accessible in header nav", () => {
    const adminHrefs = getAllHrefs(adminNavConfig);

    describe("Admin routes (Requirement 10.1)", () => {


    it("should include all routes from the old navItems array", () => {
      // Old navItems: /, /employees, /settings/departments, /settings/positions, /gmail, /recruitment
      for (const item of navItems) {
        expect(
          adminHrefs,
          `Missing route "${item.href}" (${item.label}) from old navItems`,
        ).toContain(item.href);
      }
    });

    it("should include all routes from the old adminNavSection", () => {
      // Old adminNavSection items: /admin/whitelist, /admin/oauth, /admin/users, /admin/audit-logs
      for (const item of adminNavSection.items) {
        expect(
          adminHrefs,
          `Missing admin route "${item.href}" (${item.label}) from old adminNavSection`,
        ).toContain(item.href);
      }
    });

    it("should include the dashboard route (/) via logo link", () => {
      expect(adminNavConfig.logo.href).toBe("/");
    });

    it("should contain specific required admin routes per requirements", () => {
      // Requirement 10.1 explicitly lists these routes
      const requiredRoutes = [
        "/",
        "/employees",
        "/settings/departments",
        "/settings/positions",
        "/gmail",
        "/recruitment",
        "/admin/whitelist",
        "/admin/oauth",
        "/admin/users",
        "/admin/audit-logs",
      ];

      for (const route of requiredRoutes) {
        expect(
          adminHrefs,
          `Required admin route "${route}" is missing from header nav config`,
        ).toContain(route);
      }
    });
  });

  describe("Employee routes (Requirement 10.2)", () => {
    const essHrefs = getAllHrefs(essNavConfig);

    it("should include all routes from the old employeeNavItems array", () => {
      // Old employeeNavItems: /employee/dashboard, /employee/profile, /employee/documents
      for (const item of employeeNavItems) {
        expect(
          essHrefs,
          `Missing employee route "${item.href}" (${item.label}) from old employeeNavItems`,
        ).toContain(item.href);
      }
    });

    it("should include the employee dashboard route via logo link", () => {
      expect(essNavConfig.logo.href).toBe("/employee/dashboard");
    });

    it("should contain specific required employee routes per requirements", () => {
      // Requirement 10.2 explicitly lists these routes
      const requiredRoutes = [
        "/employee/dashboard",
        "/employee/profile",
        "/employee/documents",
      ];

      for (const route of requiredRoutes) {
        expect(
          essHrefs,
          `Required employee route "${route}" is missing from header nav config`,
        ).toContain(route);
      }
    });
  });

    describe("Active HR surfaces and retired placeholders", () => {
      it("keeps active attendance, request, and payslip surfaces in navigation", () => {
        expect(adminHrefs).toEqual(
          expect.arrayContaining([
            "/attendance",
            "/admin/employee-requests",
            "/payroll",
          ]),
        );

        const essHrefs = getAllHrefs(essNavConfig);
        expect(essHrefs).toEqual(
          expect.arrayContaining(["/employee/requests", "/employee/payslips"]),
        );
      });

      it("does not advertise placeholder attendance or payroll surfaces", () => {
        const retiredRoutes = [
          "/attendance/schedules",
          "/attendance/leave",
          "/attendance/overtime",
          "/attendance/holidays",
          "/payroll/config",
          "/payroll/allowances",
          "/payroll/tax",
        ];

        for (const route of retiredRoutes) {
          expect(
            adminHrefs,
            `Retired placeholder route "${route}" must not be in navigation`,
          ).not.toContain(route);
        }
      });
    });

    describe("Role-based route separation (Requirement 10.4)", () => {
      const essHrefs = getAllHrefs(essNavConfig);

      it("should NOT include admin-only routes in the ESS config", () => {

      const adminOnlyRoutes = [
        "/admin/whitelist",
        "/admin/oauth",
        "/admin/users",
        "/admin/audit-logs",
      ];

      for (const route of adminOnlyRoutes) {
        expect(
          essHrefs,
          `Admin-only route "${route}" should NOT be in ESS nav config`,
        ).not.toContain(route);
      }
    });

    it("admin routes should be grouped under the 'he-thong' group in admin config", () => {
      const heThongGroup = adminNavConfig.groups.find(
        (g) => g.id === "he-thong",
      );
      expect(heThongGroup).toBeDefined();

      const heThongHrefs = heThongGroup!.links.map((l) => l.href);
      expect(heThongHrefs).toContain("/admin/users");
      expect(heThongHrefs).toContain("/admin/whitelist");
      expect(heThongHrefs).toContain("/admin/oauth");
      expect(heThongHrefs).toContain("/admin/audit-logs");
    });
  });

  describe("Route mapping consistency (Requirement 10.3)", () => {
    it("admin config should map old navItems to appropriate groups", () => {
      // /employees -> nhan-su group
      const nhanSuGroup = adminNavConfig.groups.find((g) => g.id === "nhan-su");
      expect(nhanSuGroup).toBeDefined();
      expect(nhanSuGroup!.links.map((l) => l.href)).toContain("/employees");
      expect(nhanSuGroup!.links.map((l) => l.href)).toContain(
        "/settings/departments",
      );
      expect(nhanSuGroup!.links.map((l) => l.href)).toContain(
        "/settings/positions",
      );

      // /recruitment -> tuyen-dung group
      const tuyenDungGroup = adminNavConfig.groups.find(
        (g) => g.id === "tuyen-dung",
      );
      expect(tuyenDungGroup).toBeDefined();
      expect(tuyenDungGroup!.links.map((l) => l.href)).toContain(
        "/recruitment",
      );

      // /gmail -> he-thong group
      const heThongGroup = adminNavConfig.groups.find(
        (g) => g.id === "he-thong",
      );
      expect(heThongGroup).toBeDefined();
      expect(heThongGroup!.links.map((l) => l.href)).toContain("/gmail");
    });

    it("ESS config should map old employeeNavItems to appropriate groups", () => {
      // /employee/profile -> ho-so group
      const hoSoGroup = essNavConfig.groups.find((g) => g.id === "ho-so");
      expect(hoSoGroup).toBeDefined();
      expect(hoSoGroup!.links.map((l) => l.href)).toContain(
        "/employee/profile",
      );
      expect(hoSoGroup!.links.map((l) => l.href)).toContain(
        "/employee/documents",
      );
    });
  });
});
