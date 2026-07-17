import { describe, it, expect } from "vitest";
import * as fc from "fast-check";
import { getNextFocusIndex } from "../focus-utils";

/**
 * Feature: header-navigation-redesign, Property 6: Arrow key wrapping within menu
 * Validates: Requirements 8.4
 *
 * For any open mega menu with N sub-links, pressing ArrowDown when focus is on
 * link at index i shall move focus to link at index (i + 1) % N.
 * Pressing ArrowUp when focus is on link at index i shall move focus to
 * link at index (i - 1 + N) % N.
 */

// --- Generators ---

/** Generate a menu size N between 1 and 20 */
const menuSizeArb = fc.integer({ min: 1, max: 20 });

/** Generate a valid focus position i given a menu size N */
const focusPositionArb = (menuSize: number) =>
  fc.integer({ min: 0, max: menuSize - 1 });

describe("Feature: header-navigation-redesign, Property 6: Arrow key wrapping within menu", () => {
  it("ArrowDown moves focus to (i + 1) % N", () => {
    fc.assert(
      fc.property(
        menuSizeArb.chain((n) => fc.tuple(fc.constant(n), focusPositionArb(n))),
        ([totalItems, currentIndex]) => {
          const result = getNextFocusIndex(currentIndex, "down", totalItems);
          const expected = (currentIndex + 1) % totalItems;
          expect(result).toBe(expected);
        },
      ),
      { numRuns: 100 },
    );
  });

  it("ArrowUp moves focus to (i - 1 + N) % N", () => {
    fc.assert(
      fc.property(
        menuSizeArb.chain((n) => fc.tuple(fc.constant(n), focusPositionArb(n))),
        ([totalItems, currentIndex]) => {
          const result = getNextFocusIndex(currentIndex, "up", totalItems);
          const expected = (currentIndex - 1 + totalItems) % totalItems;
          expect(result).toBe(expected);
        },
      ),
      { numRuns: 100 },
    );
  });

  it("result is always in range [0, N-1]", () => {
    fc.assert(
      fc.property(
        menuSizeArb.chain((n) => fc.tuple(fc.constant(n), focusPositionArb(n))),
        fc.constantFrom("down" as const, "up" as const),
        ([totalItems, currentIndex], direction) => {
          const result = getNextFocusIndex(currentIndex, direction, totalItems);
          expect(result).toBeGreaterThanOrEqual(0);
          expect(result).toBeLessThan(totalItems);
        },
      ),
      { numRuns: 100 },
    );
  });

  it("ArrowDown from last item wraps to first item", () => {
    fc.assert(
      fc.property(menuSizeArb, (totalItems) => {
        const lastIndex = totalItems - 1;
        const result = getNextFocusIndex(lastIndex, "down", totalItems);
        expect(result).toBe(0);
      }),
      { numRuns: 100 },
    );
  });

  it("ArrowUp from first item wraps to last item", () => {
    fc.assert(
      fc.property(menuSizeArb, (totalItems) => {
        const result = getNextFocusIndex(0, "up", totalItems);
        expect(result).toBe(totalItems - 1);
      }),
      { numRuns: 100 },
    );
  });
});
