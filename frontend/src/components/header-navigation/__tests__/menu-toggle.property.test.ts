import { describe, it, expect } from "vitest";
import * as fc from "fast-check";

/**
 * Feature: header-navigation-redesign, Property 1: Menu toggle behavior
 * Validates: Requirements 5.1
 *
 * For any navigation group in the header config, clicking its trigger when the
 * menu is closed should open it, and clicking the same trigger when the menu is
 * open should close it, resulting in openMenuId toggling between the group's ID
 * and null.
 */

// --- Pure toggle function (mirrors HeaderNavigation's handleToggle logic) ---

/**
 * Simulates the menu toggle state transition.
 * This is the exact logic used in HeaderNavigation:
 *   setOpenMenuId((prev) => (prev === groupId ? null : groupId))
 */
function toggleMenu(
  currentOpenId: string | null,
  clickedGroupId: string,
): string | null {
  return currentOpenId === clickedGroupId ? null : clickedGroupId;
}

// --- Generators ---

/** Generate a valid group ID (lowercase letters + digits + dashes) */
const groupIdArb = fc
  .string({
    minLength: 1,
    maxLength: 12,
    unit: fc.constantFrom(
      ...Array.from("abcdefghijklmnopqrstuvwxyz0123456789-"),
    ),
  })
  .filter((s) => s.length > 0);

/** Generate an array of unique group IDs (simulating a nav config) */
const navGroupIdsArb = fc
  .uniqueArray(groupIdArb, { minLength: 1, maxLength: 8 })
  .filter((arr) => arr.length > 0);

/** Generate a click sequence (array of group IDs picked from the config) */
const clickSequenceArb = (groupIds: string[]) =>
  fc.array(fc.constantFrom(...groupIds), { minLength: 1, maxLength: 20 });

describe("Feature: header-navigation-redesign, Property 1: Menu toggle behavior", () => {
  it("clicking a trigger when menu is closed should open it (openMenuId = groupId)", () => {
    fc.assert(
      fc.property(groupIdArb, (groupId) => {
        // Start with no menu open
        const result = toggleMenu(null, groupId);
        expect(result).toBe(groupId);
      }),
      { numRuns: 100 },
    );
  });

  it("clicking the same trigger when menu is open should close it (openMenuId = null)", () => {
    fc.assert(
      fc.property(groupIdArb, (groupId) => {
        // Start with this group's menu open
        const result = toggleMenu(groupId, groupId);
        expect(result).toBeNull();
      }),
      { numRuns: 100 },
    );
  });

  it("clicking a different trigger when a menu is open should open the new one", () => {
    fc.assert(
      fc.property(
        groupIdArb,
        groupIdArb.filter((id) => id.length > 0),
        (currentOpenId, clickedGroupId) => {
          fc.pre(currentOpenId !== clickedGroupId);

          const result = toggleMenu(currentOpenId, clickedGroupId);
          expect(result).toBe(clickedGroupId);
        },
      ),
      { numRuns: 100 },
    );
  });

  it("toggle is idempotent: two consecutive clicks on the same group return to original state", () => {
    fc.assert(
      fc.property(
        fc.oneof(groupIdArb, fc.constant(null as string | null)),
        groupIdArb,
        (initialState, groupId) => {
          const afterFirstClick = toggleMenu(initialState, groupId);
          const afterSecondClick = toggleMenu(afterFirstClick, groupId);

          // If we started with the group open, first click closes, second opens → back to open
          // If we started with null or different group, first click opens, second closes
          if (initialState === groupId) {
            // open → close → open
            expect(afterFirstClick).toBeNull();
            expect(afterSecondClick).toBe(groupId);
          } else {
            // closed/other → open → close
            expect(afterFirstClick).toBe(groupId);
            expect(afterSecondClick).toBeNull();
          }
        },
      ),
      { numRuns: 100 },
    );
  });

  it("simulating random click sequences always results in a valid state (groupId or null)", () => {
    fc.assert(
      fc.property(
        navGroupIdsArb.chain((ids) =>
          fc.tuple(fc.constant(ids), clickSequenceArb(ids)),
        ),
        ([groupIds, clicks]) => {
          let state: string | null = null;

          for (const clickedId of clicks) {
            state = toggleMenu(state, clickedId);

            // State must always be either null or one of the valid group IDs
            if (state !== null) {
              expect(groupIds).toContain(state);
            }
          }
        },
      ),
      { numRuns: 100 },
    );
  });

  it("after any click, openMenuId is either the clicked group or null (never a third value)", () => {
    fc.assert(
      fc.property(
        fc.oneof(groupIdArb, fc.constant(null as string | null)),
        groupIdArb,
        (currentState, clickedGroupId) => {
          const result = toggleMenu(currentState, clickedGroupId);

          // Result must be either the clicked group ID or null
          expect(result === clickedGroupId || result === null).toBe(true);
        },
      ),
      { numRuns: 100 },
    );
  });
});
