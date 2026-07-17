/**
 * @vitest-environment jsdom
 */

import { afterEach, describe, expect, it, vi } from "vitest";

import { sendChatMessage, type ChatMessage } from "./assistant";

describe("sendChatMessage", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("strips tool messages and assistant placeholders before POST", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ messages: [], draft_action: null }),
    });
    vi.stubGlobal("fetch", fetchMock);

    const messages: ChatMessage[] = [
      { role: "user", content: "Co bao nhieu candidate dang reviewing?" },
      {
        role: "assistant",
        content: null,
        tool_calls: [
          {
            id: "tc_1",
            type: "function",
            function: { name: "count_candidates_by_status", arguments: "{}" },
          },
        ],
      },
      {
        role: "tool",
        content: '{"count": 5}',
        tool_call_id: "tc_1",
        name: "count_candidates_by_status",
      },
      { role: "assistant", content: "Dang reviewing co 5 candidate." },
      { role: "user", content: "Con interview_scheduled thi sao?" },
    ];

    await sendChatMessage(messages);

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(JSON.parse(String(init.body))).toEqual({
      messages: [
        { role: "user", content: "Co bao nhieu candidate dang reviewing?" },
        { role: "assistant", content: "Dang reviewing co 5 candidate." },
        { role: "user", content: "Con interview_scheduled thi sao?" },
      ],
    });
  });
});
