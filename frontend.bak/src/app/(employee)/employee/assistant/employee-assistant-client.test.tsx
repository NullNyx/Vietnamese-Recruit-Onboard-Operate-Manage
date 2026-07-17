/**
 * @vitest-environment jsdom
 */
import "@testing-library/jest-dom";
import { forwardRef, useImperativeHandle } from "react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

const openDialog = vi.fn();

vi.mock("./employee-chat-area", () => ({
  EmployeeChatArea: ({ onOpenRequestDialog }: {
    onOpenRequestDialog: (values: unknown) => void;
  }) => (
    <button
      onClick={() =>
        onOpenRequestDialog({
          leave: {
            leave_type: "annual",
            start_date: "2026-07-15",
            end_date: "2026-07-17",
            reason: "việc gia đình",
          },
        })
      }
    >
      Draft handoff
    </button>
  ),
}));

vi.mock("../requests/create-request-dialog", () => ({
  CreateRequestDialog: forwardRef(function MockDialog(
    { defaultValues }: { defaultValues?: unknown },
    ref,
  ) {
    useImperativeHandle(ref, () => ({ open: openDialog, close: vi.fn() }));
    return <output data-testid="prefill">{JSON.stringify(defaultValues)}</output>;
  }),
}));

import { EmployeeAssistantClient } from "./employee-assistant-client";

describe("EmployeeAssistantClient", () => {
  it("keeps Draft Action values while opening the confirmation form", async () => {
    render(<EmployeeAssistantClient />);

    fireEvent.click(screen.getByRole("button", { name: "Draft handoff" }));

    await waitFor(() => expect(openDialog).toHaveBeenCalledOnce());
    expect(screen.getByTestId("prefill")).toHaveTextContent(
      '"start_date":"2026-07-15"',
    );
    expect(screen.getByTestId("prefill")).toHaveTextContent(
      '"reason":"việc gia đình"',
    );
  });
});
