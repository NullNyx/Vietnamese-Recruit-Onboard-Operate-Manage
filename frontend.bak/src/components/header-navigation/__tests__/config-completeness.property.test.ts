/**
 * @vitest-environment jsdom
 */
import { describe, it, expect, vi } from "vitest";
import * as fc from "fast-check";
import { render } from "@testing-library/react";
import React from "react";
import { MegaMenuPanel } from "../mega-menu-panel";
import type { NavGroup, NavLink } from "@/lib/header-nav-config";

/**
 * Feature: header-navigation-redesign, Property 9: Navigation config completeness
 * Validates: Requirements 10.1, 10.2
 *
 * For any navigation config, every link defined in the config should be rendered
 * as an anchor element in the DOM. This tests that the rendering logic doesn't
 * skip or lose any links.
 */

// Mock next/link to render a plain anchor element
vi.mock("next/link", () => ({
  __esModule: true,
  default: React.forwardRef<
    HTMLAnchorElement,
    { href: string; children?: React.ReactNode } & Record<string, unknown>
  >(function MockLink({ href, children, ...props }, ref) {
    return React.createElement(
      "a",
      { href, ref, ...props },
      children as React.ReactNode,
    );
  }),
}));

// --- Generators ---

/** Generate a valid path segment (lowercase letters and digits) */
const pathSegmentArb = fc
  .string({
    minLength: 1,
    maxLength: 8,
    unit: fc.constantFrom(
      ...Array.from("abcdefghijklmnopqrstuvwxyz0123456789"),
    ),
  })
  .filter((s) => s.length > 0);

/** Generate a valid href path like "/segment" or "/segment/segment" */
const hrefArb = fc
  .array(pathSegmentArb, { minLength: 1, maxLength: 3 })
  .map((segments) => "/" + segments.join("/"));

/** Generate a link label */
const labelArb = fc
  .string({ minLength: 1, maxLength: 20 })
  .filter((s) => s.trim().length > 0);

/** Generate a NavLink (without icon, since icons are optional and not relevant to href rendering) */
const navLinkArb: fc.Arbitrary<NavLink> = fc.record({
  href: hrefArb,
  label: labelArb,
});

/** Generate an array of NavLinks with unique hrefs */
const navLinksArb = fc
  .array(navLinkArb, { minLength: 1, maxLength: 10 })
  .map((links) => {
    // Deduplicate by href to avoid ambiguity in assertions
    const seen = new Set<string>();
    return links.filter((link) => {
      if (seen.has(link.href)) return false;
      seen.add(link.href);
      return true;
    });
  })
  .filter((links) => links.length > 0);

/** Generate a NavGroup with random links */
const navGroupArb: fc.Arbitrary<NavGroup> = navLinksArb.map((links) => ({
  id: "test-group",
  label: "Test Group",
  links,
  activeRoutes: ["/test"],
}));

describe("Feature: header-navigation-redesign, Property 9: Navigation config completeness", () => {
  it("every link in the nav config should have a corresponding anchor element with matching href in the rendered DOM", () => {
    fc.assert(
      fc.property(navGroupArb, (group) => {
        const { container } = render(
          React.createElement(MegaMenuPanel, {
            group,
            isOpen: true,
            onLinkClick: () => {},
          }),
        );

        const anchors = container.querySelectorAll("a[href]");
        const renderedHrefs = new Set(
          Array.from(anchors).map((a) => a.getAttribute("href")),
        );

        // Every link in the config must have a corresponding anchor
        for (const link of group.links) {
          expect(renderedHrefs.has(link.href)).toBe(true);
        }

        // The number of anchors should equal the number of links in config
        expect(anchors.length).toBe(group.links.length);
      }),
      { numRuns: 100 },
    );
  });

  it("when isOpen is false, no anchor elements should be rendered regardless of config", () => {
    fc.assert(
      fc.property(navGroupArb, (group) => {
        const { container } = render(
          React.createElement(MegaMenuPanel, {
            group,
            isOpen: false,
            onLinkClick: () => {},
          }),
        );

        const anchors = container.querySelectorAll("a[href]");
        expect(anchors.length).toBe(0);
      }),
      { numRuns: 100 },
    );
  });

  it("every rendered anchor should have a role='menuitem' attribute for accessibility", () => {
    fc.assert(
      fc.property(navGroupArb, (group) => {
        const { container } = render(
          React.createElement(MegaMenuPanel, {
            group,
            isOpen: true,
            onLinkClick: () => {},
          }),
        );

        const anchors = container.querySelectorAll("a[href]");

        for (const anchor of Array.from(anchors)) {
          expect(anchor.getAttribute("role")).toBe("menuitem");
        }
      }),
      { numRuns: 100 },
    );
  });
});
