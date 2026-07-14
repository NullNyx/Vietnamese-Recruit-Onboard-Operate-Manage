import { expect, test } from "@playwright/test";

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

test("HR can search with keyboard and return focus @hr", async ({ page }) => {
  requireSession(hrState);
  const consoleIssues = observeConsoleIssues();
  page.on("console", consoleIssues.onMessage);

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
  expect(consoleIssues.issues).toEqual([]);
});

test("Employee Account has named controls at mobile width @employee", async ({ page }) => {
  requireSession(employeeState);
  const consoleIssues = observeConsoleIssues();
  page.on("console", consoleIssues.onMessage);

  await page.goto("/");
  await expect(page.getByRole("navigation", { name: "Điều hướng chính" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Tài khoản" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Tìm kiếm (Ctrl+K)" })).toBeVisible();

  if ((page.viewportSize()?.width ?? 0) <= 768) {
    await expect(page.getByRole("button", { name: "Mở menu" })).toBeVisible();
  } else {
    await expect(page.getByRole("button", { name: "Mở menu" })).toBeHidden();
  }

  expect(consoleIssues.issues).toEqual([]);
});
