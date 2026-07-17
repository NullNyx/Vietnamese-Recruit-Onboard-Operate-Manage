import { describe, it, expect } from "vitest";
import * as fc from "fast-check";
import { useActiveNavItem } from "@/hooks/use-active-nav-item";
import type { NavGroup } from "@/lib/header-nav-config";

/**
 * Feature: header-navigation-redesign, Property 5: Sub-link active highlighting
 *
 * For any URL path that exactly matches a sub-link's href within a navigation group,
 * the matching sub-link shall be marked as active (highlighted).
 * No other sub-link in the same menu shall be marked active.
 *
 * **Validates: Requirements 6.2**
 */

// --- Generators ---

/** Generate a valid path segment (e.g., "employees", "payroll", "admin") */
const pathSegmentArb = fc
  .stringMatching(/^[a-z][a-z0-9-]{0,14}$/)
  .filter((s) => s.length >= 2);

/** Generate a valid href path with 1-3 segments (e.g., "/employees/import") */
const hrefArb = fc
  .array(pathSegmentArb, { minLength: 1, maxLength: 3 })
  .map((segments) => "/" + segments.join("/"));

/** Generate a NavLink with a given href */
function navLinkArb(href: string) {
  return fc.record({
    href: fc.constant(href),
    label: fc.string({ minLength: 1, maxLength: 20 }),
  });
}

/** Generate a NavGroup with unique sub-link hrefs */
const navGroupArb = fc
  .tuple(
    fc.string({ minLength: 2, maxLength: 10 }).filter((s) => /^[a-z]/.test(s)),
    fc.string({ minLength: 2, maxLength: 15 }),
    fc.uniqueArray(hrefArb, {
      minLength: 1,
      maxLength: 6,
      comparator: "IsStrictlyEqual",
    }),
  )
  .chain(([id, label, hrefs]) =>
    fc.tuple(...hrefs.map((href) => navLinkArb(href))).map((links) => ({
      id,
      label,
      links,
      // Use the first segment of each href as an active route prefix
      activeRoutes: Array.from(
        new Set(hrefs.map((h) => "/" + h.split("/")[1])),
      ),
    })),
  );

/**
 * Generate an array of NavGroups where all sub-link hrefs are unique across groups
 * AND activeRoutes prefixes don't overlap between groups.
 * This ensures the "first match wins" logic in the hook always picks the correct group.
 * Then pick one sub-link href as the "current URL".
 */
const testCaseArb = fc
  .array(navGroupArb, { minLength: 1, maxLength: 5 })
  .filter((groups) => {
    // Ensure all hrefs are unique across all groups
    const allHrefs = groups.flatMap((g) => g.links.map((l) => l.href));
    if (new Set(allHrefs).size !== allHrefs.length) return false;
    // Ensure all group IDs are unique
    const allIds = groups.map((g) => g.id);
    if (new Set(allIds).size !== allIds.length) return false;
    // Ensure activeRoutes prefixes don't overlap between groups.
    // A prefix from one group must not be a prefix of (or equal to) a prefix from another group.
    // This prevents ambiguity in the "first match wins" logic.
    for (let i = 0; i < groups.length; i++) {
      for (let j = 0; j < groups.length; j++) {
        if (i === j) continue;
        for (const routeI of groups[i].activeRoutes) {
          for (const routeJ of groups[j].activeRoutes) {
            // If one route is a prefix of another (with / boundary), they overlap
            if (
              routeI === routeJ ||
              routeJ.startsWith(routeI + "/") ||
              routeI.startsWith(routeJ + "/")
            ) {
              return false;
            }
          }
        }
      }
    }
    return true;
  })
  .chain((groups) => {
    // Collect all sub-link hrefs and pick one as the current URL
    const allLinks = groups.flatMap((g) =>
      g.links.map((l) => ({ groupId: g.id, href: l.href })),
    );
    return fc.record({
      groups: fc.constant(groups as NavGroup[]),
      selectedLink: fc.constantFrom(...allLinks),
    });
  });

// --- Property Tests ---

describe("Feature: header-navigation-redesign, Property 5: Sub-link active highlighting", () => {
  it("should mark the matching sub-link as active when URL exactly matches a sub-link href", () => {
    fc.assert(
      fc.property(testCaseArb, ({ groups, selectedLink }) => {
        const result = useActiveNavItem(groups, selectedLink.href);

        // The activeSubLinkHref should equal the chosen sub-link href
        expect(result.activeSubLinkHref).toBe(selectedLink.href);
      }),
      { numRuns: 100 },
    );
  });

  it("should mark only one sub-link as active (the one matching the URL)", () => {
    fc.assert(
      fc.property(testCaseArb, ({ groups, selectedLink }) => {
        const result = useActiveNavItem(groups, selectedLink.href);

        // Only the selected link's href should be the activeSubLinkHref
        // No other sub-link should be marked active
        expect(result.activeSubLinkHref).toBe(selectedLink.href);

        // Verify that the result only identifies one sub-link as active
        // by checking that the activeSubLinkHref is exactly the selected one
        // and not any other link in the same group
        const activeGroup = groups.find((g) => g.id === result.activeGroupId);
        if (activeGroup) {
          const activeLinksInGroup = activeGroup.links.filter(
            (l) => l.href === result.activeSubLinkHref,
          );
          expect(activeLinksInGroup).toHaveLength(1);
          expect(activeLinksInGroup[0].href).toBe(selectedLink.href);
        }
      }),
      { numRuns: 100 },
    );
  });

  it("should set activeGroupId to the group containing the matched sub-link", () => {
    fc.assert(
      fc.property(testCaseArb, ({ groups, selectedLink }) => {
        const result = useActiveNavItem(groups, selectedLink.href);

        // The activeGroupId should match the group containing the selected sub-link
        expect(result.activeGroupId).toBe(selectedLink.groupId);
      }),
      { numRuns: 100 },
    );
  });
});
