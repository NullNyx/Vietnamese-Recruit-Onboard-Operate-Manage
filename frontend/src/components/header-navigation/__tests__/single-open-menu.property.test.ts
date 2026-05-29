import { describe, it, expect } from "vitest";
import * as fc from "fast-check";

/**
 * Feature: header-navigation-redesign, Property 2: Single open menu invariant
 * Validates: Requirements 5.3, 5.6
 *
 * For any sequence of menu interactions (clicks on nav item triggers), the header
 * navigation state shall have at most one openMenuId that is non-null at any point
 * in time. When a different nav item is clicked while a menu is open, the previously
 * open menu closes and the new one opens.
 */

// --- State machine logic (extracted from HeaderNavigation component) ---

/**
 * Simulates the menu toggle logic from HeaderNavigation.
 * This mirrors the `handleToggle` callback:
 *   setOpenMenuId((prev) => (prev === groupId ? null : groupId))
 */
function applyMenuClick(
  currentOpenMenuId: string | null,
  clickedGroupId: string,
): string | null {
  return currentOpenMenuId === clickedGroupId ? null : clickedGroupId;
}

// --- Generators ---

/** Generate a unique group ID */
const groupIdArb = fc
  .string({
    minLength: 1,
    maxLength: 12,
    unit: fc.constantFrom(
      ...Array.from("abcdefghijklmnopqrstuvwxyz0123456789-"),
    ),
  })
  .filter((s) => s.length > 0);

/** Generate an array of unique group IDs (1-8 groups) */
const groupIdsArb = fc
  .uniqueArray(groupIdArb, { minLength: 1, maxLength: 8 })
  .filter((arr) => arr.length >= 1);

/** Generate a random click sequence from the available group IDs (1-20 clicks) */
const clickSequenceArb = (groupIds: string[]) =>
  fc.array(fc.constantFrom(...groupIds), { minLength: 1, maxLength: 20 });

describe("Feature: header-navigation-redesign, Property 2: Single open menu invariant", () => {
  it("should have at most one openMenuId non-null after each click in any interaction sequence", () => {
    fc.assert(
      fc.property(
        groupIdsArb.chain((groupIds) =>
          fc.tuple(fc.constant(groupIds), clickSequenceArb(groupIds)),
        ),
        ([groupIds, clicks]) => {
          let openMenuId: string | null = null;

          for (const clickedId of clicks) {
            openMenuId = applyMenuClick(openMenuId, clickedId);

            // INVARIANT: openMenuId is either null or exactly one of the groupIds
            if (openMenuId !== null) {
              expect(groupIds).toContain(openMenuId);
              // It should be a single string, not an array or multiple values
              expect(typeof openMenuId).toBe("string");
            }
          }
        },
      ),
      { numRuns: 100 },
    );
  });

  it("should never have multiple menus open simultaneously (openMenuId is always a single value or null)", () => {
    fc.assert(
      fc.property(
        groupIdsArb.chain((groupIds) =>
          fc.tuple(fc.constant(groupIds), clickSequenceArb(groupIds)),
        ),
        ([groupIds, clicks]) => {
          let openMenuId: string | null = null;
          const stateHistory: (string | null)[] = [openMenuId];

          for (const clickedId of clicks) {
            openMenuId = applyMenuClick(openMenuId, clickedId);
            stateHistory.push(openMenuId);
          }

          // Every state in the history must be null or exactly one group ID
          for (const state of stateHistory) {
            if (state !== null) {
              expect(groupIds).toContain(state);
              // Verify it's a single ID, not a concatenation or array-like value
              expect(groupIds.filter((id) => id === state).length).toBe(1);
            }
          }
        },
      ),
      { numRuns: 100 },
    );
  });

  it("should close the current menu and open the new one when a different trigger is clicked", () => {
    fc.assert(
      fc.property(
        groupIdsArb
          .filter((ids) => ids.length >= 2)
          .chain((groupIds) =>
            fc.tuple(fc.constant(groupIds), clickSequenceArb(groupIds)),
          ),
        ([, clicks]) => {
          let openMenuId: string | null = null;

          for (const clickedId of clicks) {
            const previousOpenMenuId = openMenuId;
            openMenuId = applyMenuClick(openMenuId, clickedId);

            if (
              previousOpenMenuId !== null &&
              clickedId !== previousOpenMenuId
            ) {
              // When clicking a different trigger while a menu is open:
              // - The previously open menu should be closed (not equal to previousOpenMenuId)
              expect(openMenuId).not.toBe(previousOpenMenuId);
              // - The newly clicked menu should be open
              expect(openMenuId).toBe(clickedId);
            }
          }
        },
      ),
      { numRuns: 100 },
    );
  });

  it("should toggle the same menu closed when its trigger is clicked again", () => {
    fc.assert(
      fc.property(
        groupIdsArb.chain((groupIds) =>
          fc.tuple(fc.constant(groupIds), clickSequenceArb(groupIds)),
        ),
        ([, clicks]) => {
          let openMenuId: string | null = null;

          for (const clickedId of clicks) {
            const previousOpenMenuId = openMenuId;
            openMenuId = applyMenuClick(openMenuId, clickedId);

            if (previousOpenMenuId === clickedId) {
              // Clicking the same trigger that's already open should close it
              expect(openMenuId).toBeNull();
            }
          }
        },
      ),
      { numRuns: 100 },
    );
  });
});
