import { describe, it, expect } from "vitest";
import * as fc from "fast-check";
import { useActiveNavItem } from "./use-active-nav-item";
import type { NavGroup } from "@/lib/header-nav-config";

/**
 * Feature: header-navigation-redesign, Property 4: Active state determination from URL
 * Validates: Requirements 6.1, 6.4, 6.5
 *
 * For any URL path, the useActiveNavItem hook shall return at most one activeGroupId.
 * The active group is the one whose activeRoutes array contains a prefix that matches
 * the start of the URL. If no group's activeRoutes match the URL, activeGroupId shall be null.
 */

// --- Generators ---

/** Generate a valid path segment (lowercase letters, no slashes) */
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

/** Generate a NavLink (minimal, no icon needed for logic testing) */
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

/** Generate a NavGroup with unique id and random activeRoutes */
const navGroupArb = (index: number) =>
  fc
    .record({
      activeRoutes: fc.array(routePrefixArb, { minLength: 1, maxLength: 3 }),
    })
    .chain(({ activeRoutes }) =>
      fc
        .array(navLinkArb(activeRoutes[0]), { minLength: 1, maxLength: 4 })
        .map((links) => ({
          id: `group-${index}`,
          label: `Group ${index}`,
          links,
          activeRoutes,
        })),
    );

/** Generate an array of NavGroups (1 to 5 groups) */
const navGroupsArb = fc
  .integer({ min: 1, max: 5 })
  .chain((count) =>
    fc.tuple(...Array.from({ length: count }, (_, i) => navGroupArb(i))),
  )
  .map((groups) => groups as NavGroup[]);

/** Generate a random URL path (may or may not match any group) */
const randomPathArb = fc
  .array(pathSegmentArb, { minLength: 1, maxLength: 4 })
  .map((segments) => "/" + segments.join("/"));

/**
 * Generate a URL path that is guaranteed to match a specific group's activeRoutes.
 * This creates a path that starts with one of the group's route prefixes.
 */
const matchingPathArb = (group: NavGroup) =>
  fc
    .record({
      routeIndex: fc.integer({ min: 0, max: group.activeRoutes.length - 1 }),
      suffix: fc.array(pathSegmentArb, { minLength: 0, maxLength: 2 }),
    })
    .map(({ routeIndex, suffix }) => {
      const base = group.activeRoutes[routeIndex];
      return suffix.length > 0 ? base + "/" + suffix.join("/") : base;
    });

describe("Feature: header-navigation-redesign, Property 4: Active state determination from URL", () => {
  it("should return at most one activeGroupId for any URL and nav config", () => {
    fc.assert(
      fc.property(navGroupsArb, randomPathArb, (navGroups, pathname) => {
        const result = useActiveNavItem(navGroups, pathname);

        // At most one activeGroupId (it's either null or a single string)
        if (result.activeGroupId !== null) {
          // The active group must exist in the navGroups array
          const activeGroup = navGroups.find(
            (g) => g.id === result.activeGroupId,
          );
          expect(activeGroup).toBeDefined();
        }
      }),
      { numRuns: 100 },
    );
  });

  it("should return an activeGroupId whose activeRoutes contains a prefix matching the URL", () => {
    fc.assert(
      fc.property(navGroupsArb, randomPathArb, (navGroups, pathname) => {
        const result = useActiveNavItem(navGroups, pathname);

        if (result.activeGroupId !== null) {
          const activeGroup = navGroups.find(
            (g) => g.id === result.activeGroupId,
          )!;

          // The active group must have an activeRoutes prefix that matches the pathname,
          // OR a sub-link href that exactly matches the pathname
          const hasMatchingPrefix = activeGroup.activeRoutes.some(
            (route) => pathname === route || pathname.startsWith(route + "/"),
          );
          const hasMatchingSubLink = activeGroup.links.some(
            (link) => link.href === pathname,
          );

          expect(hasMatchingPrefix || hasMatchingSubLink).toBe(true);
        }
      }),
      { numRuns: 100 },
    );
  });

  it("should return null activeGroupId when no group's activeRoutes match and no sub-link matches", () => {
    fc.assert(
      fc.property(navGroupsArb, randomPathArb, (navGroups, pathname) => {
        const result = useActiveNavItem(navGroups, pathname);

        // Check if any group should match
        const anyGroupMatches = navGroups.some(
          (group) =>
            group.activeRoutes.some(
              (route) => pathname === route || pathname.startsWith(route + "/"),
            ) || group.links.some((link) => link.href === pathname),
        );

        if (!anyGroupMatches) {
          expect(result.activeGroupId).toBeNull();
        }
      }),
      { numRuns: 100 },
    );
  });

  it("should correctly activate a group when pathname matches one of its activeRoutes prefixes", () => {
    fc.assert(
      fc.property(
        navGroupsArb.chain((groups) => {
          // Pick a random group and generate a path matching its activeRoutes
          const groupIndex = Math.floor(Math.random() * groups.length);
          return fc.tuple(
            fc.constant(groups),
            matchingPathArb(groups[groupIndex]),
            fc.constant(groupIndex),
          );
        }),
        ([navGroups, pathname, expectedGroupIndex]) => {
          const result = useActiveNavItem(navGroups, pathname);

          // The result should have a non-null activeGroupId
          expect(result.activeGroupId).not.toBeNull();

          // The active group should be the expected one OR an earlier group
          // that also matches (first-match-wins semantics)
          if (result.activeGroupId !== null) {
            const activeGroup = navGroups.find(
              (g) => g.id === result.activeGroupId,
            )!;
            const activeGroupIdx = navGroups.indexOf(activeGroup);

            // The active group index should be <= expectedGroupIndex
            // because first-match-wins means an earlier group could match too
            expect(activeGroupIdx).toBeLessThanOrEqual(expectedGroupIndex);

            // The active group must actually match the pathname
            const hasMatchingPrefix = activeGroup.activeRoutes.some(
              (route) => pathname === route || pathname.startsWith(route + "/"),
            );
            const hasMatchingSubLink = activeGroup.links.some(
              (link) => link.href === pathname,
            );
            expect(hasMatchingPrefix || hasMatchingSubLink).toBe(true);
          }
        },
      ),
      { numRuns: 100 },
    );
  });

  it("should never return more than one active group (uniqueness invariant)", () => {
    fc.assert(
      fc.property(navGroupsArb, randomPathArb, (navGroups, pathname) => {
        const result = useActiveNavItem(navGroups, pathname);

        // The result type only allows one activeGroupId, but let's verify
        // the function doesn't somehow return an invalid state
        const matchingGroups = navGroups.filter(
          (g) => g.id === result.activeGroupId,
        );

        if (result.activeGroupId !== null) {
          // Exactly one group should match the returned ID
          expect(matchingGroups.length).toBe(1);
        } else {
          expect(matchingGroups.length).toBe(0);
        }
      }),
      { numRuns: 100 },
    );
  });
});
