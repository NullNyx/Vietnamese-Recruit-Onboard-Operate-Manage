/**
 * @vitest-environment jsdom
 */
import "@testing-library/jest-dom";
import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { MessageBubble } from "../message-bubble";

describe("MessageBubble", () => {
  it("renders user message correctly", () => {
    const message = { role: "user", content: "Hello AI" };
    render(<MessageBubble message={message} />);
    
    expect(screen.getByText("Hello AI")).toBeInTheDocument();
    // User icon container usually has specific styling or we can check just the text
  });

  it("renders assistant message correctly", () => {
    const message = { role: "assistant", content: "Hello HR" };
    render(<MessageBubble message={message} />);
    
    expect(screen.getByText("Hello HR")).toBeInTheDocument();
  });

  it("returns null for tool message", () => {
    const message = { role: "tool", content: "tool result", tool_call_id: "call_123" };
    const { container } = render(<MessageBubble message={message} />);
    expect(container).toBeEmptyDOMElement();
  });

  it("shows loading indicator when assistant has tool_calls and no content", () => {
    const message = { 
      role: "assistant", 
      content: null, 
      tool_calls: [{ id: "call_123", type: "function", function: { name: "search", arguments: "{}" } }] 
    };
    render(<MessageBubble message={message as any} />);
    
    expect(screen.getByText("Đang truy vấn dữ liệu...")).toBeInTheDocument();
  });
});
