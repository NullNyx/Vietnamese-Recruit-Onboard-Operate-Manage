/**
 * Pure utility functions for focus management within mega menu panels.
 * Extracted for testability and reuse.
 */

/**
 * Calculates the next focus index when navigating within a menu using arrow keys.
 * Uses modular arithmetic to wrap around the menu items.
 *
 * @param currentIndex - The current focused item index (0-based)
 * @param direction - 'down' for ArrowDown, 'up' for ArrowUp
 * @param totalItems - Total number of items in the menu (N)
 * @returns The next focus index, wrapping around using modular arithmetic
 */
export function getNextFocusIndex(
  currentIndex: number,
  direction: "down" | "up",
  totalItems: number,
): number {
  if (totalItems <= 0) return 0;
  if (direction === "down") return (currentIndex + 1) % totalItems;
  return (currentIndex - 1 + totalItems) % totalItems;
}
