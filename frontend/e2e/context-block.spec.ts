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

  // HR assistant session routes
  await page.route("**/api/assistant/session/start", async (route) => {
    await route.fulfill({ json: { session_id: "e2e-hr-session-id" } });
  });
  await page.route("**/api/assistant/session/end", async (route) => {
    await route.fulfill({ json: {} });
  });

  // Employee assistant session routes
  await page.route("**/api/ess/assistant/session/start", async (route) => {
    await route.fulfill({ json: { session_id: "e2e-employee-session-id" } });
  });
  await page.route("**/api/ess/assistant/session/end", async (route) => {
    await route.fulfill({ json: {} });
  });
  await page.route("**/api/ess/assistant/feedback", async (route) => {
    await route.fulfill({ json: {} });
  });
  await page.route("**/api/assistant/feedback", async (route) => {
    await route.fulfill({ json: {} });
  });

  // Dashboard stats (used by the HR dashboard page)
  await page.route("**/api/admin/stats*", async (route) => {
    await route.fulfill({
      json: { employees: 42, departments: 5, positions: 12 },
    });
  });

  // Runtime health check (used by admin pages)
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
}

// ---------------------------------------------------------------------------

  test.describe("HR context injection @hr", () => {
    test("HR assistant response includes organization context data", async ({ page }) => {
      requireSession(hrState);
      const consoleIssues = observeConsoleIssues();
      page.on("console", consoleIssues.onMessage);
  
      await mockAuthenticatedShell(page, hrUser);
  
      // Mock HR chat response with context-aware data (org stats + candidate pipeline)
      await page.route("**/api/assistant/chat", async (route) => {
        await route.fulfill({
          json: {
            messages: [
              {
                role: "assistant",
                content:
                  "Tổ chức Vroom QA Organization đang có 5 ứng viên trong pipeline. "
                  + "Trong đó: 2 ứng viên mới, 2 đang xem xét, 1 đã lên lịch phỏng vấn. "
                  + "Hiện có 3 vị trí đang tuyển dụng: Software Engineer, HR Manager, và Business Analyst.",
              },
            ],
            draft_action: null,
          },
        });
      });
  
      // Navigate to landing page first to let hydration settle
      await page.goto("/");
      await expect(page.getByRole("navigation", { name: "Điều hướng chính" })).toBeVisible();
      // Client-side navigation to HR assistant
      await page.goto("/admin/assistant");
  
      // Send a message to trigger assistant response with context
      const input = page.getByPlaceholder("Nhập tin nhắn...");
      await expect(input).toBeVisible({ timeout: 15000 });
      await input.fill("Xin chào");
      await input.press("Enter");
  
      // Verify response displays organization context data from the mocked backend
      await expect(page.getByText("Vroom QA Organization")).toBeVisible({ timeout: 30000 });
      await expect(page.getByText("5 ứng viên trong pipeline")).toBeVisible();
      await expect(page.getByText("Software Engineer")).toBeVisible();
      await expect(page.getByText("HR Manager")).toBeVisible();
  
      expect(consoleIssues.issues).toEqual([]);
    });

    test("HR session-start context timing — assistant_type sent on mount", async ({
      page,
    }) => {
      requireSession(hrState);
      const consoleIssues = observeConsoleIssues();
      page.on("console", consoleIssues.onMessage);
  
      await mockAuthenticatedShell(page, hrUser);
  
      // Track session/start calls — register AFTER mockAuthenticatedShell so this takes priority
      let sessionStartPayload: Record<string, unknown> | null = null;
      await page.route("**/api/assistant/session/start", async (route) => {
        const body = route.request().postDataJSON();
        sessionStartPayload = body;
        await route.fulfill({ json: { session_id: "e2e-hr-session-id" } });
      });
  
      // Navigate to HR assistant page
      await page.goto("/");
      await expect(page.getByRole("navigation", { name: "Điều hướng chính" })).toBeVisible();
      await page.goto("/admin/assistant");
  
      // Wait for chat interface to load
      const input = page.getByPlaceholder("Nhập tin nhắn...");
      await expect(input).toBeVisible({ timeout: 15000 });
  
      // Verify session/start was called on mount with correct context
      expect(sessionStartPayload).not.toBeNull();
      expect(sessionStartPayload!.assistant_type).toBe("hr");
  
      expect(consoleIssues.issues).toEqual([]);
    });
  });

// ---------------------------------------------------------------------------

test.describe("Employee context injection @employee", () => {
  test("employee assistant response includes personal context data", async ({ page }) => {
    requireSession(employeeState);
    const consoleIssues = observeConsoleIssues();
    page.on("console", consoleIssues.onMessage);

    await mockAuthenticatedShell(page, employeeUser);

    // Mock employee chat response with personal context (leave balance, profile)
    await page.route("**/api/ess/assistant/chat", async (route) => {
      await route.fulfill({
        json: {
          messages: [
            {
              role: "assistant",
              content:
                "Chào bạn Employee QA. Bạn thuộc phòng ban Engineering, vị trí Software Engineer. "
                + "Số ngày phép còn lại: 8/12 ngày (đã dùng 3, đang chờ duyệt 1). "
                + "Bạn có 2 yêu cầu đang chờ duyệt (1 nghỉ phép, 1 tăng ca).",
            },
          ],
          draft_action: null,
        },
      });
    });

    // Navigate to employee assistant page
    await page.goto("/employee/assistant");

    // Send a message to trigger assistant response with personal context
    const input = page.getByPlaceholder("Nhập tin nhắn...");
    await expect(input).toBeVisible({ timeout: 15000 });
    await input.fill("Thông tin của tôi");
    await input.press("Enter");

    // Verify response displays employee personal context data
    await expect(page.getByText("Employee QA")).toBeVisible({ timeout: 30000 });
    await expect(page.getByText("Software Engineer")).toBeVisible();
    await expect(page.getByText("8/12")).toBeVisible();

    expect(consoleIssues.issues).toEqual([]);
  });

  test("session-start context timing — context block sent on first open", async ({
    page,
  }) => {
    requireSession(employeeState);
    const consoleIssues = observeConsoleIssues();
    page.on("console", consoleIssues.onMessage);

    await mockAuthenticatedShell(page, employeeUser);

    // Track session/start calls — register AFTER mockAuthenticatedShell so this takes priority
    let sessionStartPayload: Record<string, unknown> | null = null;
    await page.route("**/api/ess/assistant/session/start", async (route) => {
      const body = route.request().postDataJSON();
      sessionStartPayload = body;
      await route.fulfill({ json: { session_id: "e2e-employee-session-id" } });
    });

    // Mock employee chat response
    await page.route("**/api/ess/assistant/chat", async (route) => {
      await route.fulfill({
        json: {
          messages: [
            {
              role: "assistant",
              content: "Chào bạn, tôi là trợ lý AI Nhân viên. Tôi có thể giúp gì cho bạn?",
            },
          ],
          draft_action: null,
        },
      });
    });

    await page.goto("/employee/assistant");

    // Wait for chat interface to load
    const input = page.getByPlaceholder("Nhập tin nhắn...");
    await expect(input).toBeVisible({ timeout: 15000 });

    // Verify session/start was called on mount with the correct assistant_type
    expect(sessionStartPayload).not.toBeNull();
    expect(sessionStartPayload!.assistant_type).toBe("employee");

    // Send a message and verify response works after session start
    await input.fill("Số ngày phép còn lại?");
    await input.press("Enter");

    const response = page.locator("text=trợ lý AI").first();
    await expect(response).toBeVisible({ timeout: 30000 });

    expect(consoleIssues.issues).toEqual([]);
  });
});
