/**
 * @vitest-environment jsdom
 */
import "@testing-library/jest-dom";
import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { MessageBubble } from "../message-bubble";
import { ChatMessage } from "@/lib/api/assistant";

describe("MessageBubble", () => {
  it("renders user message correctly", () => {
    const message = { role: "user" as const, content: "Hello AI" };
    render(<MessageBubble message={message as ChatMessage} />);
    
    expect(screen.getByText("Hello AI")).toBeInTheDocument();
    // User icon container usually has specific styling or we can check just the text
  });

  it("renders assistant message correctly", () => {
    const message = { role: "assistant" as const, content: "Hello HR" };
    render(<MessageBubble message={message as ChatMessage} />);
    
    expect(screen.getByText("Hello HR")).toBeInTheDocument();
  });

  it("returns null for tool message", () => {
    const message = { role: "tool" as const, content: "tool result", tool_call_id: "call_123" };
    const { container } = render(<MessageBubble message={message as ChatMessage} />);
    expect(container).toBeEmptyDOMElement();
  });

  it("shows loading indicator when assistant has tool_calls and no content", () => {
    const message: ChatMessage = { 
      role: "assistant", 
      content: null, 
      tool_calls: [{ id: "call_123", type: "function", function: { name: "search", arguments: "{}" } }] 
    };
    render(<MessageBubble message={message} />);
    
    expect(screen.getByText("Đang truy vấn dữ liệu...")).toBeInTheDocument();
  });
});
