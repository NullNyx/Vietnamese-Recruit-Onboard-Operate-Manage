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

function observeConsoleIssues() {
  const issues: string[] = [];
  return {
    issues,
    onMessage(message: { type(): string; text(): string }) {
      if (message.type() === "error" || message.type() === "warning") {
        issues.push(`[${message.type()}] ${message.text()}`);
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
  await page.route("**/api/auth/me", async (route) => {
    await route.fulfill({ json: user });
  });
  await page.route("**/api/auth/setup-status", async (route) => {
    await route.fulfill({ json: { setup_complete: true } });
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
}

test("HR can search with keyboard and return focus @hr", async ({ page }) => {
  requireSession(hrState);
  const consoleIssues = observeConsoleIssues();
  page.on("console", consoleIssues.onMessage);

  await mockAuthenticatedShell(page, hrUser);
  await page.goto("/");
  await expect(page.getByRole("navigation", { name: "Điều hướng chính" })).toBeVisible();

  const searchTrigger = page.getByRole("button", { name: "Tìm kiếm (Ctrl+K)" });
  await searchTrigger.focus();
  await page.keyboard.press("Control+K");

  const dialog = page.getByRole("dialog", { name: "Tìm kiếm trang" });
  await expect(dialog).toBeVisible();
  await expect(dialog).toHaveAccessibleDescription(
    "Tìm và mở nhanh các trang mà bạn có quyền truy cập.",
  );
  await expect(page.getByPlaceholder("Tìm kiếm trang...")).toBeFocused();

  await page.keyboard.press("Escape");
  await expect(dialog).toBeHidden();
  await expect(searchTrigger).toBeFocused();

});

test("Employee Account has named controls at mobile width @employee", async ({ page }) => {
  requireSession(employeeState);
  const consoleIssues = observeConsoleIssues();
  page.on("console", consoleIssues.onMessage);

  await mockAuthenticatedShell(page, employeeUser);
  await page.goto("/");
  await expect(page.getByRole("navigation", { name: "Điều hướng chính" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Tài khoản" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Tìm kiếm (Ctrl+K)" })).toBeVisible();

  if ((page.viewportSize()?.width ?? 0) <= 768) {
    await expect(page.getByRole("button", { name: "Mở menu" })).toBeVisible();
  } else {
    await expect(page.getByRole("button", { name: "Mở menu" })).toBeHidden();
  }


});
