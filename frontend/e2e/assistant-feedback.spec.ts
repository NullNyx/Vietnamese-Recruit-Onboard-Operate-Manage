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

const assistantChatResponse = {
  messages: [
    { role: "assistant", content: "Hiện tại có 5 candidate đang trong quy trình tuyển dụng." },
  ],
  draft_action: null,
};

const employeeAssistantChatResponse = {
  messages: [
    { role: "assistant", content: "Bạn còn 7 ngày phép trong năm nay." },
  ],
  draft_action: null,
};

async function mockAuthenticatedShell(page: Page, user?: typeof hrUser | typeof employeeUser) {
  const currentUser = user ?? hrUser;
  const isHr = currentUser.role === "admin";

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
    ["vroom-hr:e2e-current-user", currentUser],
  );
  // Catch-all for unhandled API routes — register first so specific routes (registered later) take priority
  await page.route("**/api/**", async (route) => {
    await route.fulfill({ json: {} });
  });
  await page.route("**/api/auth/me", async (route) => {
    await route.fulfill({ json: currentUser });
  });
  await page.route("**/api/auth/setup-status", async (route) => {
    await route.fulfill({ json: { setup_complete: true } });
  });

  if (isHr) {
    await page.route("**/api/assistant/session/start", async (route) => {
      await route.fulfill({ json: { session_id: "e2e-session-id" } });
    });
    await page.route("**/api/assistant/session/end", async (route) => {
      await route.fulfill({ json: {} });
    });
    await page.route("**/api/assistant/chat", async (route) => {
      await route.fulfill({ json: assistantChatResponse });
    });
    await page.route("**/api/assistant/feedback", async (route) => {
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
  } else {
    await page.route("**/api/ess/assistant/session/start", async (route) => {
      await route.fulfill({ json: { session_id: "e2e-session-id" } });
    });
    await page.route("**/api/ess/assistant/session/end", async (route) => {
      await route.fulfill({ json: {} });
    });
    await page.route("**/api/ess/assistant/chat", async (route) => {
      await route.fulfill({ json: employeeAssistantChatResponse });
    });
    await page.route("**/api/ess/assistant/feedback", async (route) => {
      await route.fulfill({ json: {} });
    });
  }
}

// ---------------------------------------------------------------------------
// HR Assistant feedback (@hr)
// ---------------------------------------------------------------------------
test.describe("HR assistant feedback @hr", () => {
  test("shows thumbs up/down buttons on assistant messages", async ({ page }) => {
    requireSession(hrState);
    const consoleIssues = observeConsoleIssues();
    page.on("console", consoleIssues.onMessage);

    await mockAuthenticatedShell(page, hrUser);
    // Navigate to a known-good page first to let hydration settle,
    // then use client-side navigation to the assistant page.
    await page.goto("/");
    await expect(page.getByRole("navigation", { name: "Điều hướng chính" })).toBeVisible({ timeout: 15000 });
    await page.goto("/admin/assistant");

    // Send a message to trigger assistant response
    const input = page.getByPlaceholder("Nhập tin nhắn...");
    await expect(input).toBeVisible({ timeout: 15000 });
    await input.fill("Có bao nhiêu candidate đang reviewing?");
    await input.press("Enter");

    // Wait for assistant response to appear
    const response = page.locator("text=Hiện tại").first();
    await expect(response).toBeVisible({ timeout: 30000 });

    // Verify thumbs up/down buttons are present
    await expect(page.getByRole("button", { name: "Thumbs up" }).first()).toBeVisible();
    await expect(page.getByRole("button", { name: "Thumbs down" }).first()).toBeVisible();

    expect(consoleIssues.issues).toEqual([]);
  });

  test("clicking thumbs up submits feedback and shows Đã đánh giá", async ({ page }) => {
    requireSession(hrState);

    await mockAuthenticatedShell(page, hrUser);
    await page.goto("/");
    await expect(page.getByRole("navigation", { name: "Điều hướng chính" })).toBeVisible({ timeout: 15000 });
    await page.goto("/admin/assistant");
    const input = page.getByPlaceholder("Nhập tin nhắn...");
    await expect(input).toBeVisible({ timeout: 15000 });
    await input.fill("Xin chào");
    await input.press("Enter");

    const response = page.locator("text=Hiện tại").first();
    await expect(response).toBeVisible({ timeout: 30000 });

    // Click thumbs up
    await page.getByRole("button", { name: "Thumbs up" }).first().click();

    // Verify "Đã đánh giá" state and disabled buttons
    await expect(page.getByText("Đã đánh giá")).toBeVisible();
    await expect(page.getByRole("button", { name: "Thumbs up" }).first()).toBeDisabled();
    await expect(page.getByRole("button", { name: "Thumbs down" }).first()).toBeDisabled();
  });

  test("clicking thumbs down shows optional text input", async ({ page }) => {
    requireSession(hrState);

    await mockAuthenticatedShell(page, hrUser);
    await page.goto("/");
    await expect(page.getByRole("navigation", { name: "Điều hướng chính" })).toBeVisible({ timeout: 15000 });
    await page.goto("/admin/assistant");
    const input = page.getByPlaceholder("Nhập tin nhắn...");
    await expect(input).toBeVisible({ timeout: 15000 });
    await input.fill("Kiểm tra chức năng");
    await input.press("Enter");

    const response = page.locator("text=Hiện tại").first();
    await expect(response).toBeVisible({ timeout: 30000 });

    // Click thumbs down
    await page.getByRole("button", { name: "Thumbs down" }).first().click();

    // Verify optional text input appears
    const textarea = page.locator("textarea").last();
    await expect(textarea).toBeVisible();
  });
});

// ---------------------------------------------------------------------------
// Employee Assistant feedback (@employee)
// ---------------------------------------------------------------------------
test.describe("Employee assistant feedback @employee", () => {
  test("shows thumbs up/down on employee assistant messages", async ({ page }) => {
    requireSession(employeeState);
    const consoleIssues = observeConsoleIssues();
    page.on("console", consoleIssues.onMessage);

    await mockAuthenticatedShell(page, employeeUser);
    // Navigate to a known-good page first to let hydration settle,
    // then use client-side navigation to the employee assistant page.
    await page.goto("/");
    await expect(page.getByRole("navigation", { name: "Điều hướng chính" })).toBeVisible({ timeout: 15000 });
    await page.goto("/employee/assistant");

    // Send a message as employee
    const input = page.getByPlaceholder("Nhập tin nhắn...");
    await expect(input).toBeVisible({ timeout: 15000 });
    await input.fill("Số ngày phép còn lại?");
    await input.press("Enter");

    // Wait for response
    const response = page.locator("text=còn").first();
    await expect(response).toBeVisible({ timeout: 30000 });

    // Verify feedback buttons
    await expect(page.getByRole("button", { name: "Thumbs up" }).first()).toBeVisible();
    await expect(page.getByRole("button", { name: "Thumbs down" }).first()).toBeVisible();

    expect(consoleIssues.issues).toEqual([]);
  });
});
