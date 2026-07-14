/**
 * @vitest-environment jsdom
 */
import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";

vi.mock("next/navigation", () => ({
  usePathname: () => "/employees/550e8400-e29b-41d4-a716-446655440000",
}));

import { Breadcrumbs } from "./breadcrumbs";

describe("Breadcrumbs", () => {
  it("does not expose an internal identifier and accepts a display name", () => {
    render(
      <Breadcrumbs
        displayNames={{
          "550e8400-e29b-41d4-a716-446655440000": "Nguyễn Văn A",
        }}
      />,
    );

    expect(screen.getByText("Nguyễn Văn A")).toBeInTheDocument();
    expect(
      screen.queryByText("550e8400-e29b-41d4-a716-446655440000"),
    ).not.toBeInTheDocument();
  });

  it("uses a human-readable fallback when a display name is unavailable", () => {
    render(<Breadcrumbs />);

    expect(screen.getByText("Chi tiết")).toBeInTheDocument();
  });
});
