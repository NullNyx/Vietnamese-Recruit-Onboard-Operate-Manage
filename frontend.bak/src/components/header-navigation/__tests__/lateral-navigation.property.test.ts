import { describe, it, expect } from "vitest";
import * as fc from "fast-check";
import { getNextGroupIndex } from "../navigation-utils";

/**
 * Feature: header-navigation-redesign, Property 7: Lateral keyboard navigation between groups
 * Validates: Requirements 8.5
 *
 * For any header with M navigation groups, when a mega menu for group at index j is open,
 * pressing ArrowRight shall close the current menu, move focus to group at index (j + 1) % M,
 * and open that group's menu. Pressing ArrowLeft shall do the same for index (j - 1 + M) % M.
 */

// --- Generators ---

/** Generate a valid total group count M (1 to 10) */
const totalGroupsArb = fc.integer({ min: 1, max: 10 });

/** Generate a valid current position j given totalGroups M */
const positionArb = (totalGroups: number) =>
  fc.integer({ min: 0, max: totalGroups - 1 });

/** Generate a tuple of (totalGroups, currentIndex) where currentIndex is valid */
const groupAndPositionArb = totalGroupsArb.chain((M) =>
  positionArb(M).map((j) => ({ totalGroups: M, currentIndex: j })),
);

describe("Feature: header-navigation-redesign, Property 7: Lateral keyboard navigation between groups", () => {
  it("ArrowRight opens group at (j + 1) % M", () => {
    fc.assert(
      fc.property(groupAndPositionArb, ({ totalGroups, currentIndex }) => {
        const result = getNextGroupIndex(currentIndex, "right", totalGroups);
        const expected = (currentIndex + 1) % totalGroups;
        expect(result).toBe(expected);
      }),
      { numRuns: 100 },
    );
  });

  it("ArrowLeft opens group at (j - 1 + M) % M", () => {
    fc.assert(
      fc.property(groupAndPositionArb, ({ totalGroups, currentIndex }) => {
        const result = getNextGroupIndex(currentIndex, "left", totalGroups);
        const expected = (currentIndex - 1 + totalGroups) % totalGroups;
        expect(result).toBe(expected);
      }),
      { numRuns: 100 },
    );
  });

  it("result is always in range [0, M-1]", () => {
    fc.assert(
      fc.property(
        groupAndPositionArb,
        fc.constantFrom("right" as const, "left" as const),
        ({ totalGroups, currentIndex }, direction) => {
          const result = getNextGroupIndex(
            currentIndex,
            direction,
            totalGroups,
          );
          expect(result).toBeGreaterThanOrEqual(0);
          expect(result).toBeLessThan(totalGroups);
        },
      ),
      { numRuns: 100 },
    );
  });

  it("ArrowRight from last group wraps to first group", () => {
    fc.assert(
      fc.property(totalGroupsArb, (totalGroups) => {
        const lastIndex = totalGroups - 1;
        const result = getNextGroupIndex(lastIndex, "right", totalGroups);
        expect(result).toBe(0);
      }),
      { numRuns: 100 },
    );
  });

  it("ArrowLeft from first group wraps to last group", () => {
    fc.assert(
      fc.property(totalGroupsArb, (totalGroups) => {
        const result = getNextGroupIndex(0, "left", totalGroups);
        expect(result).toBe(totalGroups - 1);
      }),
      { numRuns: 100 },
    );
  });

  it("ArrowRight followed by ArrowLeft returns to original position", () => {
    fc.assert(
      fc.property(groupAndPositionArb, ({ totalGroups, currentIndex }) => {
        const afterRight = getNextGroupIndex(
          currentIndex,
          "right",
          totalGroups,
        );
        const backToOriginal = getNextGroupIndex(
          afterRight,
          "left",
          totalGroups,
        );
        expect(backToOriginal).toBe(currentIndex);
      }),
      { numRuns: 100 },
    );
  });

  it("M consecutive ArrowRight presses return to original position (full cycle)", () => {
    fc.assert(
      fc.property(groupAndPositionArb, ({ totalGroups, currentIndex }) => {
        let position = currentIndex;
        for (let i = 0; i < totalGroups; i++) {
          position = getNextGroupIndex(position, "right", totalGroups);
        }
        expect(position).toBe(currentIndex);
      }),
      { numRuns: 100 },
    );
  });
});
