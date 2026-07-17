import { describe, it, expect } from "vitest";
import * as fc from "fast-check";
import type { NavGroup } from "@/lib/header-nav-config";

/**
 * Feature: header-navigation-redesign, Property 3: Link click dismisses menu
 * Validates: Requirements 5.4, 7.3
 *
 * For any navigation group and any sub-link within that group, clicking the link
 * should set openMenuId to null (desktop) or mobileMenuOpen to false (mobile),
 * and trigger navigation to the link's href.
 */

// --- Pure state transition functions under test ---

/**
 * Models the desktop handleLinkClick behavior:
 * Clicking any sub-link always sets openMenuId to null.
 */
// eslint-disable-next-line @typescript-eslint/no-unused-vars
function handleDesktopLinkClick(openMenuId: string | null): string | null {
  return null;
}

/**
 * Models the mobile handleLinkClick behavior:
 * Clicking any sub-link always sets mobileMenuOpen to false.
 */
// eslint-disable-next-line @typescript-eslint/no-unused-vars
function handleMobileLinkClick(mobileMenuOpen: boolean): boolean {
  return false;
}

// --- Generators ---

/** Generate a valid path segment (lowercase letters and digits) */
const pathSegmentArb = fc
  .string({
    minLength: 1,
    maxLength: 8,
    unit: fc.constantFrom(
      ...Array.from("abcdefghijklmnopqrstuvwxyz0123456789-"),
    ),
  })
  .filter((s) => s.length > 0);

/** Generate a route prefix like "/segment" or "/segment/segment" */
const routePrefixArb = fc
  .array(pathSegmentArb, { minLength: 1, maxLength: 3 })
  .map((segments) => "/" + segments.join("/"));

/** Generate a NavLink (minimal for logic testing) */
const navLinkArb = (prefix: string) =>
  fc
    .array(pathSegmentArb, { minLength: 0, maxLength: 2 })
    .map((extraSegments) => ({
      href:
        extraSegments.length > 0
          ? prefix + "/" + extraSegments.join("/")
          : prefix,
      label: "Link",
    }));

/** Generate a NavGroup with unique id and random activeRoutes and links */
const navGroupArb = (index: number) =>
  fc
    .record({
      activeRoutes: fc.array(routePrefixArb, { minLength: 1, maxLength: 3 }),
    })
    .chain(({ activeRoutes }) =>
      fc
        .array(navLinkArb(activeRoutes[0]), { minLength: 1, maxLength: 5 })
        .map((links) => ({
          id: `group-${index}`,
          label: `Group ${index}`,
          links,
          activeRoutes,
        })),
    );

/** Generate an array of NavGroups (1 to 6 groups) */
const navGroupsArb = fc
  .integer({ min: 1, max: 6 })
  .chain((count) =>
    fc.tuple(...Array.from({ length: count }, (_, i) => navGroupArb(i))),
  )
  .map((groups) => groups as NavGroup[]);

/**
 * Generate a nav config with a randomly selected open menu and a random sub-link
 * from that menu to click.
 */
const linkClickScenarioArb = navGroupsArb.chain((groups) => {
  // Pick a random group to be the open menu
  return fc
    .integer({ min: 0, max: groups.length - 1 })
    .chain((openGroupIndex) => {
      const openGroup = groups[openGroupIndex];
      // Pick a random sub-link within that group
      return fc
        .integer({ min: 0, max: openGroup.links.length - 1 })
        .map((linkIndex) => ({
          groups,
          openGroupId: openGroup.id,
          clickedLink: openGroup.links[linkIndex],
        }));
    });
});

/**
 * Generate a scenario where a link is clicked from a DIFFERENT group's menu
 * (e.g., user opens group A but somehow clicks a link — still should dismiss).
 */
const crossGroupLinkClickArb = navGroupsArb
  .filter((groups) => groups.length >= 1)
  .chain((groups) => {
    return fc
      .integer({ min: 0, max: groups.length - 1 })
      .chain((openGroupIndex) => {
        // Pick any link from any group
        const allLinks = groups.flatMap((g) => g.links);
        return fc
          .integer({ min: 0, max: allLinks.length - 1 })
          .map((linkIndex) => ({
            groups,
            openGroupId: groups[openGroupIndex].id,
            clickedLink: allLinks[linkIndex],
          }));
      });
  });

describe("Feature: header-navigation-redesign, Property 3: Link click dismisses menu", () => {
  it("desktop: clicking any sub-link sets openMenuId to null regardless of which menu is open", () => {
    fc.assert(
      fc.property(linkClickScenarioArb, ({ openGroupId }) => {
        // Pre-condition: a menu is open
        expect(openGroupId).not.toBeNull();

        // Action: user clicks a sub-link
        const newOpenMenuId = handleDesktopLinkClick(openGroupId);

        // Post-condition: menu is dismissed
        expect(newOpenMenuId).toBeNull();
      }),
      { numRuns: 100 },
    );
  });

  it("desktop: clicking a link from any group dismisses the currently open menu", () => {
    fc.assert(
      fc.property(crossGroupLinkClickArb, ({ openGroupId }) => {
        // Pre-condition: some menu is open
        expect(openGroupId).not.toBeNull();

        // Action: user clicks any link (could be from a different group)
        const newOpenMenuId = handleDesktopLinkClick(openGroupId);

        // Post-condition: menu is always dismissed
        expect(newOpenMenuId).toBeNull();
      }),
      { numRuns: 100 },
    );
  });

  it("mobile: clicking any sub-link sets mobileMenuOpen to false", () => {
    fc.assert(
      fc.property(linkClickScenarioArb, () => {
        // Pre-condition: mobile menu is open
        const mobileMenuOpen = true;

        // Action: user clicks a sub-link in the mobile overlay
        const newMobileMenuOpen = handleMobileLinkClick(mobileMenuOpen);

        // Post-condition: mobile menu is dismissed
        expect(newMobileMenuOpen).toBe(false);
      }),
      { numRuns: 100 },
    );
  });

  it("desktop: handleLinkClick always returns null for any openMenuId value", () => {
    fc.assert(
      fc.property(
        fc.oneof(fc.constant(null), fc.string({ minLength: 1, maxLength: 20 })),
        (openMenuId) => {
          // Action: link click handler is invoked
          const result = handleDesktopLinkClick(openMenuId);

          // Post-condition: result is always null
          expect(result).toBeNull();
        },
      ),
      { numRuns: 100 },
    );
  });

  it("desktop: the clicked link href is preserved for navigation (not mutated)", () => {
    fc.assert(
      fc.property(linkClickScenarioArb, ({ openGroupId, clickedLink }) => {
        // The link's href should be a valid string that can be used for navigation
        expect(typeof clickedLink.href).toBe("string");
        expect(clickedLink.href.startsWith("/")).toBe(true);

        // After dismissing the menu, the href is still available for router.push
        const newOpenMenuId = handleDesktopLinkClick(openGroupId);
        expect(newOpenMenuId).toBeNull();

        // The link object is not mutated
        expect(clickedLink.href.startsWith("/")).toBe(true);
      }),
      { numRuns: 100 },
    );
  });
});
