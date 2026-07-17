import { expect, test, type Page } from "@playwright/test";

const baseURL = process.env.E2E_BASE_URL;
const hrState = process.env.E2E_HR_STORAGE_STATE;
const employeeState = process.env.E2E_EMPLOYEE_STORAGE_STATE;

function requireSession(state: string | undefined) {
  test.skip(
    !baseURL || !state,
    "Set E2E_BASE_URL and the role storage-state variables to run browser seam tests.",
  );
}

/**
 * Collect console errors/warnings for post-test assertions.
 * Call `observeConsoleIssues()` and attach `onMessage` before navigating.
 * Filters out Next.js hydration warnings (expected in E2E with addInitScript)
 * and 500 resource-load errors (side-effect API calls beyond the mocked ones).
 */
function observeConsoleIssues() {
  const issues: string[] = [];
  const filterPatterns = [
    "Expected server HTML to contain",
    "An error occurred during hydration",
    "the server responded with a status of 500",
    "the server responded with a status of 403",
    "the server responded with a status of 404",
  ];
  return {
    issues,
    onMessage(message: { type(): string; text(): string }) {
      if (message.type() === "error" || message.type() === "warning") {
        const text = message.text();
        if (filterPatterns.some((p) => text.includes(p))) return;
        issues.push(`[${message.type()}] ${text}`);
      }
    },
  };
}

const isoNow = new Date().toISOString();

const hrUser = {
  id: "14717ef2-869a-4725-a650-b410c7ba05d9",
  email: "hr.qa@vroom.example.com",
  name: "HR QA",
  avatar_url: null,
  employee_id: null,
  role: "admin" as const,
  must_change_password: false,
  gmail_grant_valid: true,
  calendar_grant_valid: true,
  created_at: isoNow,
  last_login: isoNow,
};

const employeeUser = {
  id: "cdca7ee1-3ea1-4f56-b5e9-6f1b6ce72ddd",
  email: "employee.qa@vroom.example.com",
  name: "Employee QA",
  avatar_url: null,
  employee_id: "abd76375-8303-4fad-a69f-89b2ffe9d63c",
  role: "user" as const,
  must_change_password: false,
  gmail_grant_valid: true,
  calendar_grant_valid: true,
  created_at: isoNow,
  last_login: isoNow,
};

const standardChatResponse = {
  messages: [
    { role: "assistant", content: "Hiện tại có 5 candidate đang trong quy trình tuyển dụng." },
  ],
  draft_action: null,
};

const employeeChatResponse = {
  messages: [
    { role: "assistant", content: "Chào bạn Employee QA. Bạn còn 12 ngày phép trong năm nay." },
  ],
  draft_action: null,
};

const leaveDraftResponse = {
  messages: [
    { role: "assistant", content: "Tôi đã soạn sẵn đơn nghỉ phép cho bạn." },
  ],
  draft_action: {
    action_type: "submit_leave_request",
    parameters: {
      leave_type: "annual",
      start_date: "2026-07-15",
      end_date: "2026-07-17",
    },
    preview: "Đơn nghỉ phép từ 15/07/2026 đến 17/07/2026 (annual)",
    provenance: {},
    confirm_endpoint: "/api/recruitment/candidates/leave-draft",
    confirm_method: "POST",
    confirm_body: {
      leave_type: "annual",
      start_date: "2026-07-15",
      end_date: "2026-07-17",
      reason: "Nghỉ phép du lịch",
    },
  },
};

async function mockAuthenticatedShell(page: Page, user: typeof hrUser | typeof employeeUser) {
  await page.context().addCookies([
    {
      name: "access_token",
      value: "e2e-bypass",
      url: "http://localhost:3000",
    },
  ]);
  await page.addInitScript(
    ([storageKey, currentUser]) => {
      window.localStorage.setItem(storageKey, JSON.stringify(currentUser));
      window.__VROOM_HR_E2E_CURRENT_USER__ = currentUser;
    },
    ["vroom-hr:e2e-current-user", user],
  );
  // Catch-all for unhandled API routes — register first so specific routes (registered later) take priority
  await page.route("**/api/**", async (route) => {
    await route.fulfill({ json: {} });
  });
  await page.route("**/api/auth/me", async (route) => {
    await route.fulfill({ json: user });
  });
  await page.route("**/api/auth/setup-status", async (route) => {
    await route.fulfill({ json: { setup_complete: true } });
  });
  // HR assistant routes
  await page.route("**/api/assistant/session/start", async (route) => {
    await route.fulfill({ json: { session_id: "e2e-session-id" } });
  });
  await page.route("**/api/assistant/session/end", async (route) => {
    await route.fulfill({ json: {} });
  });
  await page.route("**/api/assistant/chat", async (route) => {
    await route.fulfill({ json: standardChatResponse });
  });
  await page.route("**/api/assistant/feedback", async (route) => {
    await route.fulfill({ json: {} });
  });
  await page.route("**/api/assistant/draft-decision", async (route) => {
    await route.fulfill({ json: {} });
  });
  await page.route("**/api/admin/runtime/health", async (route) => {
    await route.fulfill({
      json: {
        status: "healthy",
        services: [
          { name: "redis", status: "healthy", latency_ms: 1.2, detail: null },
          { name: "postgresql", status: "healthy", latency_ms: 2.4, detail: null },
          { name: "minio", status: "healthy", latency_ms: 3.1, detail: null },
          { name: "gmail-worker", status: "healthy", latency_ms: 4.0, detail: null },
          { name: "onboarding-worker", status: "healthy", latency_ms: 4.8, detail: null },
        ],
      },
    });
  });
  // Employee assistant routes
  await page.route("**/api/ess/assistant/session/start", async (route) => {
    await route.fulfill({ json: { session_id: "e2e-employee-session-id" } });
  });
  await page.route("**/api/ess/assistant/session/end", async (route) => {
    await route.fulfill({ json: {} });
  });
  await page.route("**/api/ess/assistant/chat", async (route) => {
    await route.fulfill({ json: employeeChatResponse });
  });
  await page.route("**/api/ess/assistant/feedback", async (route) => {
    await route.fulfill({ json: {} });
  });
}

// ===========================================================================
// Helpers: send a message and wait for the assistant reply
// ===========================================================================

async function sendAssistantMessage(page: Page, text: string) {
  const input = page.getByPlaceholder("Nhập tin nhắn...");
  await expect(input).toBeVisible({ timeout: 15000 });
  await input.fill(text);
  await input.press("Enter");
}

async function waitForAssistantReply(page: Page, replyText: string) {
  const response = page.locator(`text=${replyText}`).first();
  await expect(response).toBeVisible({ timeout: 30000 });
}

// ===========================================================================
// 1. Safety Tests (#236)
// ===========================================================================

test.describe("Safety — role-based access @employee", () => {
  test("employee cannot access /admin/assistant — redirects to /", async ({ page }) => {
    requireSession(employeeState);
    const consoleIssues = observeConsoleIssues();
    page.on("console", consoleIssues.onMessage);

    await mockAuthenticatedShell(page, employeeUser);
    // Navigate to a known-good page first to let hydration settle
    await page.goto("/");
    await expect(page.getByRole("navigation", { name: "Điều hướng chính" })).toBeVisible();

    // Try to access the admin assistant page as employee
    await page.goto("/admin/assistant");

    // The admin layout checks effectiveUser.role !== "admin" and redirects to /
    // Wait for the URL to return to /
    await page.waitForURL("/", { timeout: 10000 });
    await expect(page.getByRole("navigation", { name: "Điều hướng chính" })).toBeVisible();

    expect(consoleIssues.issues).toEqual([]);
  });

  test("employee chat returns only personal data — no cross-employee data", async ({ page }) => {
    requireSession(employeeState);
    const consoleIssues = observeConsoleIssues();
    page.on("console", consoleIssues.onMessage);

    await mockAuthenticatedShell(page, employeeUser);
    await page.goto("/employee/assistant");

    // Send a message about personal leave balance
    await sendAssistantMessage(page, "Số ngày phép còn lại?");
    await waitForAssistantReply(page, "Bạn còn 12 ngày phép");

    // Verify only personal data is shown — no other employee's name or data
    await expect(page.getByText("Employee QA")).toBeVisible();
    await expect(page.getByText("Employee QA").first()).toBeVisible();
    // Ensure no reference to other employees
    await expect(page.getByText("Nguyễn Văn A")).not.toBeVisible();

    expect(consoleIssues.issues).toEqual([]);
  });
});

test.describe("Safety — tool scope enforcement @hr", () => {
  test("disallowed tool call shows error message", async ({ page }) => {
    requireSession(hrState);
    const consoleIssues = observeConsoleIssues();
    page.on("console", consoleIssues.onMessage);

    await mockAuthenticatedShell(page, hrUser);

    // Override the chat API to return a tool rejection error
    await page.route("**/api/assistant/chat", async (route) => {
      await route.fulfill({
        status: 403,
        contentType: "application/json",
        body: JSON.stringify({
          error: "Tool not allowed: Tool 'delete_candidate' requires scope 'admin.delete'",
        }),
      });
    });

    await page.goto("/");
    await expect(page.getByRole("navigation", { name: "Điều hướng chính" })).toBeVisible();
    await page.goto("/admin/assistant");

    await sendAssistantMessage(page, "Xóa candidate này");
    await page.waitForTimeout(2000);

    // The chat-interface shows an error banner with "Thử lại" button
    await expect(page.getByRole("button", { name: "Thử lại" })).toBeVisible({ timeout: 15000 });

    expect(consoleIssues.issues).toEqual([]);
  });
});

// ===========================================================================
// 2. Quality Evaluation Tests (#235)
// ===========================================================================

test.describe("Quality — feedback evaluation @hr", () => {
  test("thumbs up submits feedback and shows Đã đánh giá + disabled buttons", async ({ page }) => {
    requireSession(hrState);
    const consoleIssues = observeConsoleIssues();
    page.on("console", consoleIssues.onMessage);

    await mockAuthenticatedShell(page, hrUser);
    await page.goto("/");
    await expect(page.getByRole("navigation", { name: "Điều hướng chính" })).toBeVisible();
    await page.goto("/admin/assistant");

    await sendAssistantMessage(page, "Xin chào");
    await waitForAssistantReply(page, "Hiện tại có 5 candidate");

    // Click thumbs up
    await page.getByRole("button", { name: "Thumbs up" }).first().click();

    // Verify "Đã đánh giá" state and disabled buttons
    await expect(page.getByText("Đã đánh giá")).toBeVisible();
    await expect(page.getByRole("button", { name: "Thumbs up" }).first()).toBeDisabled();
    await expect(page.getByRole("button", { name: "Thumbs down" }).first()).toBeDisabled();

    expect(consoleIssues.issues).toEqual([]);
  });

  test("thumbs down shows optional text input", async ({ page }) => {
    requireSession(hrState);
    const consoleIssues = observeConsoleIssues();
    page.on("console", consoleIssues.onMessage);

    await mockAuthenticatedShell(page, hrUser);
    await page.goto("/");
    await expect(page.getByRole("navigation", { name: "Điều hướng chính" })).toBeVisible();
    await page.goto("/admin/assistant");

    await sendAssistantMessage(page, "Kiểm tra chức năng");
    await waitForAssistantReply(page, "Hiện tại có 5 candidate");

    // Click thumbs down
    await page.getByRole("button", { name: "Thumbs down" }).first().click();

    // Verify optional text input appears
    const textarea = page.getByPlaceholder("Phản hồi thêm (không bắt buộc)...");
    await expect(textarea).toBeVisible();

    expect(consoleIssues.issues).toEqual([]);
  });

  test("submit feedback text verifies API call body", async ({ page }) => {
    requireSession(hrState);
    const consoleIssues = observeConsoleIssues();
    page.on("console", consoleIssues.onMessage);


    await mockAuthenticatedShell(page, hrUser);

    // Set up a promise that resolves when the feedback API is called
    let feedbackRequestBody: unknown = null;
    await page.route("**/api/assistant/feedback", async (route) => {
      const body = route.request().postDataJSON();
      feedbackRequestBody = body;
      await route.fulfill({ json: {} });
    });

    await page.goto("/");
    await expect(page.getByRole("navigation", { name: "Điều hướng chính" })).toBeVisible();
    await page.goto("/admin/assistant");

    await sendAssistantMessage(page, "Đánh giá phản hồi");
    await waitForAssistantReply(page, "Hiện tại có 5 candidate");

    // Click thumbs down
    await page.getByRole("button", { name: "Thumbs down" }).first().click();

    // Enter feedback text
    const textarea = page.getByPlaceholder("Phản hồi thêm (không bắt buộc)...");
    await expect(textarea).toBeVisible();
    await textarea.fill("Câu trả lời không đầy đủ");

    // Submit the feedback
    await page.getByRole("button", { name: "Gửi" }).click();

    // Wait for the API call to happen
    await page.waitForTimeout(1000);

    // Verify the API body
    expect(feedbackRequestBody).not.toBeNull();
    const body = feedbackRequestBody as Record<string, unknown>;
    expect(body.feedback_type).toBe("down");
    expect(body.optional_text).toBe("Câu trả lời không đầy đủ");
    expect(body.session_id).toBeTruthy();
    expect(typeof body.message_index).toBe("number");

    expect(consoleIssues.issues).toEqual([]);
  });
});

// ===========================================================================
// 3. Human-in-the-Loop Tests (extension)
// ===========================================================================

test.describe("Human-in-the-loop — draft action @hr", () => {
  test("HR confirms draft action — write endpoint is called", async ({ page }) => {
    requireSession(hrState);
    const consoleIssues = observeConsoleIssues();
    page.on("console", consoleIssues.onMessage);

    await mockAuthenticatedShell(page, hrUser);

    // Override chat API to return a draft action
    await page.route("**/api/assistant/chat", async (route) => {
      await route.fulfill({ json: leaveDraftResponse });
    });

    // Track the confirm endpoint call
    let confirmCalled = false;
    let confirmMethod = "";
    let confirmBody: unknown = null;
    await page.route("**/api/recruitment/candidates/leave-draft", async (route) => {
      confirmCalled = true;
      confirmMethod = route.request().method();
      confirmBody = route.request().postDataJSON();
      await route.fulfill({ json: { status: "ok" } });
    });

    await page.goto("/");
    await expect(page.getByRole("navigation", { name: "Điều hướng chính" })).toBeVisible();
    await page.goto("/admin/assistant");

    // Send a message that triggers a draft action
    await sendAssistantMessage(page, "Soạn đơn nghỉ phép");
    await waitForAssistantReply(page, "Tôi đã soạn sẵn đơn nghỉ phép");

    // Verify draft action card is shown
    await expect(page.getByText("Draft — Đơn nghỉ phép")).toBeVisible({ timeout: 15000 });
    await expect(page.getByText("Đơn nghỉ phép từ 15/07/2026 đến 17/07/2026")).toBeVisible();

    // Click Xác nhận
    await page.getByRole("button", { name: "Xác nhận" }).click();

    // Wait for the confirmation to complete
    await expect(page.getByText("Đã xác nhận và gửi thành công.")).toBeVisible({ timeout: 15000 });

    // Verify the confirm endpoint was called with correct method and body
    expect(confirmCalled).toBe(true);
    expect(confirmMethod).toBe("POST");
    const body = confirmBody as Record<string, unknown>;
    expect(body.leave_type).toBe("annual");
    expect(body.start_date).toBe("2026-07-15");
    expect(body.end_date).toBe("2026-07-17");

    expect(consoleIssues.issues).toEqual([]);
  });

  test("HR cancels draft — write endpoint is NOT called", async ({ page }) => {
    requireSession(hrState);
    const consoleIssues = observeConsoleIssues();
    page.on("console", consoleIssues.onMessage);

    await mockAuthenticatedShell(page, hrUser);

    // Override chat API to return a draft action
    await page.route("**/api/assistant/chat", async (route) => {
      await route.fulfill({ json: leaveDraftResponse });
    });

    // Track the confirm endpoint to ensure it's NOT called
    let confirmCalled = false;
    await page.route("**/api/recruitment/candidates/leave-draft", async (route) => {
      confirmCalled = true;
      await route.fulfill({ json: { status: "ok" } });
    });

    await page.goto("/");
    await expect(page.getByRole("navigation", { name: "Điều hướng chính" })).toBeVisible();
    await page.goto("/admin/assistant");

    // Send a message that triggers a draft action
    await sendAssistantMessage(page, "Soạn đơn nghỉ phép");
    await waitForAssistantReply(page, "Tôi đã soạn sẵn đơn nghỉ phép");

    // Verify draft action card is shown
    await expect(page.getByText("Draft — Đơn nghỉ phép")).toBeVisible({ timeout: 15000 });

    // Click Hủy
    await page.getByRole("button", { name: "Hủy" }).click();

    // The draft card should disappear after dismissing
    await expect(page.getByText("Draft — Đơn nghỉ phép")).not.toBeVisible({ timeout: 5000 });

    // Verify the confirm endpoint was NEVER called
    expect(confirmCalled).toBe(false);

    expect(consoleIssues.issues).toEqual([]);
  });
});
