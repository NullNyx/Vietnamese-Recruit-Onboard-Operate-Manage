// @vitest-environment jsdom
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { CapabilityHealthCards } from "../components/gmail/capability-health-cards";

vi.mock("@/lib/utils", () => ({
  cn: (...classes: (string | boolean | undefined | null)[]) =>
    classes.filter(Boolean).join(" "),
}));

describe("CapabilityHealthCards", () => {
  it("renders capability health cards with correct labels", () => {
    const capabilities = [
      { capability: "gmail_ingestion", health: "unknown" as const, label: "Gmail ingestion" },
      { capability: "gmail_sending", health: "unknown" as const, label: "Gmail sending" },
      { capability: "calendar_sync", health: "unknown" as const, label: "Calendar sync" },
    ];

    render(<CapabilityHealthCards capabilities={capabilities} />);

    expect(screen.getByText("Gmail ingestion")).toBeDefined();
    expect(screen.getByText("Gmail sending")).toBeDefined();
    expect(screen.getByText("Calendar sync")).toBeDefined();
  });

  it("displays Unknown badge for unknown health state", () => {
    const capabilities = [
      { capability: "gmail_ingestion", health: "unknown" as const, label: "Gmail ingestion" },
    ];

    render(<CapabilityHealthCards capabilities={capabilities} />);

    expect(screen.getByText("Unknown")).toBeDefined();
  });

  it("displays Unavailable badge for unavailable health state", () => {
    const capabilities = [
      { capability: "gmail_ingestion", health: "unavailable" as const, label: "Gmail ingestion" },
    ];

    render(<CapabilityHealthCards capabilities={capabilities} />);

    expect(screen.getByText("Unavailable")).toBeDefined();
  });

  it("displays Healthy badge for healthy health state", () => {
    const capabilities = [
      { capability: "gmail_ingestion", health: "healthy" as const, label: "Gmail ingestion" },
    ];

    render(<CapabilityHealthCards capabilities={capabilities} />);

    expect(screen.getByText("Healthy")).toBeDefined();
  });

  it("shows loading state", () => {
      render(<CapabilityHealthCards capabilities={[]} loading={true} />);

    expect(screen.getByText("Đang kiểm tra trạng thái dịch vụ...")).toBeDefined();
  });

  it("returns null for empty capabilities when not loading", () => {
    const { container } = render(
      <CapabilityHealthCards capabilities={[]} />,
    );

    expect(container.firstChild).toBeNull();
  });

  it("renders capability description when provided", () => {
    const capabilities = [
      {
        capability: "gmail_ingestion",
        health: "unknown" as const,
        label: "Gmail ingestion",
        description: "Cannot verify service status",
      },
    ];

    render(<CapabilityHealthCards capabilities={capabilities} />);

    expect(screen.getByText("Cannot verify service status")).toBeDefined();
  });
});
