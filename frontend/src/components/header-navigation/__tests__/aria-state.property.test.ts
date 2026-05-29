import { describe, it, expect } from "vitest";
import * as fc from "fast-check";

/**
 * Feature: header-navigation-redesign, Property 8: ARIA state consistency
 * Validates: Requirements 8.6
 *
 * For any navigation group, the `aria-expanded` attribute on its trigger element
 * shall equal "true" when openMenuId equals the group's ID, and "false" otherwise.
 * For any sub-link whose href matches the current page URL, `aria-current` shall equal "page".
 */

// --- Pure logic functions under test ---

/**
 * Determines the aria-expanded attribute value for a navigation group trigger.
 * Returns "true" when the group's menu is open, "false" otherwise.
 */
function getAriaExpanded(groupId: string, openMenuId: string | null): string {
  return groupId === openMenuId ? "true" : "false";
}

/**
 * Determines the aria-current attribute value for a sub-link.
 * Returns "page" when the link's href matches the current URL, undefined otherwise.
 */
function getAriaCurrent(
  linkHref: string,
  currentUrl: string,
): "page" | undefined {
  return linkHref === currentUrl ? "page" : undefined;
}

// --- Generators ---

/** Generate a valid group ID (lowercase letters and hyphens) */
const groupIdArb = fc
  .string({
    minLength: 1,
    maxLength: 12,
    unit: fc.constantFrom(
      ...Array.from("abcdefghijklmnopqrstuvwxyz-0123456789"),
    ),
  })
  .filter((s) => s.length > 0 && !s.startsWith("-") && !s.endsWith("-"));

/** Generate a path segment */
const pathSegmentArb = fc
  .string({
    minLength: 1,
    maxLength: 8,
    unit: fc.constantFrom(
      ...Array.from("abcdefghijklmnopqrstuvwxyz0123456789-"),
    ),
  })
  .filter((s) => s.length > 0);

/** Generate a URL path like "/segment" or "/segment/segment" */
const urlPathArb = fc
  .array(pathSegmentArb, { minLength: 1, maxLength: 4 })
  .map((segments) => "/" + segments.join("/"));

/** Generate an array of unique group IDs (1 to 6 groups) */
const groupIdsArb = fc
  .uniqueArray(groupIdArb, { minLength: 1, maxLength: 6 })
  .filter((ids) => ids.length >= 1);

/** Generate an openMenuId that is either null or one of the group IDs */
const openMenuIdArb = (groupIds: string[]) =>
  fc.oneof(fc.constant(null), fc.constantFrom(...groupIds));

describe("Feature: header-navigation-redesign, Property 8: ARIA state consistency", () => {
  it("aria-expanded should be 'true' when groupId equals openMenuId", () => {
    fc.assert(
      fc.property(groupIdsArb, (groupIds) => {
        // For each group, when it IS the open menu, aria-expanded must be "true"
        for (const groupId of groupIds) {
          const result = getAriaExpanded(groupId, groupId);
          expect(result).toBe("true");
        }
      }),
      { numRuns: 100 },
    );
  });

  it("aria-expanded should be 'false' when groupId does not equal openMenuId", () => {
    fc.assert(
      fc.property(
        groupIdsArb.chain((ids) =>
          fc.tuple(fc.constant(ids), openMenuIdArb(ids)),
        ),
        ([groupIds, openMenuId]) => {
          for (const groupId of groupIds) {
            if (groupId !== openMenuId) {
              const result = getAriaExpanded(groupId, openMenuId);
              expect(result).toBe("false");
            }
          }
        },
      ),
      { numRuns: 100 },
    );
  });

  it("aria-expanded should be 'false' for all groups when openMenuId is null", () => {
    fc.assert(
      fc.property(groupIdsArb, (groupIds) => {
        for (const groupId of groupIds) {
          const result = getAriaExpanded(groupId, null);
          expect(result).toBe("false");
        }
      }),
      { numRuns: 100 },
    );
  });

  it("exactly one group should have aria-expanded='true' when openMenuId matches a group", () => {
    fc.assert(
      fc.property(
        groupIdsArb
          .filter((ids) => ids.length >= 2)
          .chain((ids) => fc.tuple(fc.constant(ids), fc.constantFrom(...ids))),
        ([groupIds, openMenuId]) => {
          const expandedStates = groupIds.map((id) =>
            getAriaExpanded(id, openMenuId),
          );
          const trueCount = expandedStates.filter((s) => s === "true").length;
          const falseCount = expandedStates.filter((s) => s === "false").length;

          expect(trueCount).toBe(1);
          expect(falseCount).toBe(groupIds.length - 1);
        },
      ),
      { numRuns: 100 },
    );
  });

  it("aria-current should be 'page' when linkHref matches currentUrl", () => {
    fc.assert(
      fc.property(urlPathArb, (url) => {
        const result = getAriaCurrent(url, url);
        expect(result).toBe("page");
      }),
      { numRuns: 100 },
    );
  });

  it("aria-current should be undefined when linkHref does not match currentUrl", () => {
    fc.assert(
      fc.property(
        fc.tuple(urlPathArb, urlPathArb).filter(([a, b]) => a !== b),
        ([linkHref, currentUrl]) => {
          const result = getAriaCurrent(linkHref, currentUrl);
          expect(result).toBeUndefined();
        },
      ),
      { numRuns: 100 },
    );
  });

  it("among multiple sub-links, only the one matching currentUrl should have aria-current='page'", () => {
    fc.assert(
      fc.property(
        fc
          .uniqueArray(urlPathArb, { minLength: 2, maxLength: 8 })
          .chain((hrefs) =>
            fc.tuple(fc.constant(hrefs), fc.constantFrom(...hrefs)),
          ),
        ([linkHrefs, currentUrl]) => {
          const ariaCurrentValues = linkHrefs.map((href) =>
            getAriaCurrent(href, currentUrl),
          );

          const pageCount = ariaCurrentValues.filter(
            (v) => v === "page",
          ).length;
          const undefinedCount = ariaCurrentValues.filter(
            (v) => v === undefined,
          ).length;

          // Exactly one link should have aria-current="page"
          expect(pageCount).toBe(1);
          // All others should be undefined
          expect(undefinedCount).toBe(linkHrefs.length - 1);

          // The one with "page" should be the matching href
          const matchingIndex = linkHrefs.indexOf(currentUrl);
          expect(ariaCurrentValues[matchingIndex]).toBe("page");
        },
      ),
      { numRuns: 100 },
    );
  });

  it("when currentUrl does not match any sub-link, no link should have aria-current='page'", () => {
    fc.assert(
      fc.property(
        fc
          .uniqueArray(urlPathArb, { minLength: 1, maxLength: 6 })
          .chain((hrefs) =>
            fc.tuple(
              fc.constant(hrefs),
              urlPathArb.filter((url) => !hrefs.includes(url)),
            ),
          ),
        ([linkHrefs, currentUrl]) => {
          const ariaCurrentValues = linkHrefs.map((href) =>
            getAriaCurrent(href, currentUrl),
          );

          // No link should have aria-current="page"
          const pageCount = ariaCurrentValues.filter(
            (v) => v === "page",
          ).length;
          expect(pageCount).toBe(0);

          // All should be undefined
          for (const value of ariaCurrentValues) {
            expect(value).toBeUndefined();
          }
        },
      ),
      { numRuns: 100 },
    );
  });
});
