// @vitest-environment jsdom
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { ConnectionPanel } from "../components/gmail/connection-panel";

vi.mock("@/lib/utils", () => ({
  cn: (...classes: (string | boolean | undefined | null)[]) =>
    classes.filter(Boolean).join(" "),
}));

describe("ConnectionPanel", () => {
  it("shows loading state initially", () => {
    render(
      <ConnectionPanel
        status={null}
        email={null}
        loading={true}
        error={null}
        onConnect={vi.fn()}
        onDisconnect={vi.fn()}
        onRetry={vi.fn()}
        connectLoading={false}
        disconnectLoading={false}
      />,
    );

    expect(screen.getByText("Đang kiểm tra kết nối...")).toBeDefined();
  });

  it("shows error state with retry button", () => {
    render(
      <ConnectionPanel
        status={null}
        email={null}
        loading={false}
        error="Network error"
        onConnect={vi.fn()}
        onDisconnect={vi.fn()}
        onRetry={vi.fn()}
        connectLoading={false}
        disconnectLoading={false}
      />,
    );

    expect(screen.getByText("Không thể kiểm tra trạng thái kết nối")).toBeDefined();
    expect(screen.getByText("Thử lại")).toBeDefined();
  });

  it("shows disconnected state with connect button", () => {
    render(
      <ConnectionPanel
        status="disconnected"
        email={null}
        loading={false}
        error={null}
        onConnect={vi.fn()}
        onDisconnect={vi.fn()}
        onRetry={vi.fn()}
        connectLoading={false}
        disconnectLoading={false}
      />,
    );

    expect(screen.getByText("Chưa kết nối Gmail")).toBeDefined();
    expect(screen.getByText("Kết nối Gmail")).toBeDefined();
  });

  it("shows connected state with email and disconnect button", () => {
    render(
      <ConnectionPanel
        status="connected"
        email="admin@example.com"
        loading={false}
        error={null}
        onConnect={vi.fn()}
        onDisconnect={vi.fn()}
        onRetry={vi.fn()}
        connectLoading={false}
        disconnectLoading={false}
      />,
    );

    expect(screen.getByText("Đã kết nối")).toBeDefined();
    expect(screen.getByText("admin@example.com")).toBeDefined();
    expect(screen.getByText("Ngắt kết nối")).toBeDefined();
  });

  it("shows reauthorization required state with reconnect button", () => {
    render(
      <ConnectionPanel
        status="reauthorization_required"
        email={null}
        loading={false}
        error={null}
        onConnect={vi.fn()}
        onDisconnect={vi.fn()}
        onRetry={vi.fn()}
        connectLoading={false}
        disconnectLoading={false}
      />,
    );

    expect(screen.getByText("Phiên kết nối đã hết hạn")).toBeDefined();
    expect(screen.getByText("Kết nối lại")).toBeDefined();
  });

  it("renders capability health cards when provided and connected", () => {
    const capabilities = [
      { capability: "gmail_ingestion", health: "unknown" as const, label: "Gmail ingestion" },
      { capability: "gmail_sending", health: "unknown" as const, label: "Gmail sending" },
    ];

    render(
      <ConnectionPanel
        status="connected"
        email="admin@example.com"
        loading={false}
        error={null}
        onConnect={vi.fn()}
        onDisconnect={vi.fn()}
        onRetry={vi.fn()}
        connectLoading={false}
        disconnectLoading={false}
        capabilities={capabilities}
      />,
    );

    // Connection status still rendered
    expect(screen.getByText("Đã kết nối")).toBeDefined();
    // Capability health cards rendered separately
    expect(screen.getByText("Gmail ingestion")).toBeDefined();
    expect(screen.getByText("Gmail sending")).toBeDefined();
  });

  it("renders compact variant correctly", () => {
    render(
      <ConnectionPanel
        status="connected"
        email="admin@example.com"
        loading={false}
        error={null}
        onConnect={vi.fn()}
        onDisconnect={vi.fn()}
        onRetry={vi.fn()}
        connectLoading={false}
        disconnectLoading={false}
        compact
      />,
    );

    // In compact mode, the email is shown rather than "Đã kết nối"
    expect(screen.getByText("admin@example.com")).toBeDefined();
    expect(screen.getByText("Ngắt")).toBeDefined();
  });
});
