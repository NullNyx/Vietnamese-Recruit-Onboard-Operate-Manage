/**
 * Pure utility functions for header navigation keyboard logic.
 * Extracted for testability via property-based tests.
 */

/**
 * Computes the next group index for lateral keyboard navigation.
 * When ArrowRight/ArrowLeft is pressed while a menu is open,
 * it wraps around the group list using modular arithmetic.
 *
 * @param currentIndex - The index of the currently open group (0-based)
 * @param direction - 'right' for ArrowRight, 'left' for ArrowLeft
 * @param totalGroups - Total number of navigation groups (M)
 * @returns The index of the next group to open
 */
export function getNextGroupIndex(
  currentIndex: number,
  direction: "right" | "left",
  totalGroups: number,
): number {
  if (direction === "right") {
    return (currentIndex + 1) % totalGroups;
  }
  return (currentIndex - 1 + totalGroups) % totalGroups;
}
