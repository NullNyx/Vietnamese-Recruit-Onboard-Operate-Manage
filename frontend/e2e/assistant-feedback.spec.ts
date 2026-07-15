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

// ---------------------------------------------------------------------------
// HR Assistant feedback (@hr)
// ---------------------------------------------------------------------------
test.describe("HR assistant feedback @hr", () => {
  test("shows thumbs up/down buttons on assistant messages", async ({ page }) => {
    requireSession(hrState);
    const consoleIssues = observeConsoleIssues();
    page.on("console", consoleIssues.onMessage);

    await page.goto("/admin/assistant");

    // Send a message to trigger assistant response
    const input = page.getByPlaceholder("Nhập tin nhắn...");
    await expect(input).toBeVisible();
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

    await page.goto("/admin/assistant");
    const input = page.getByPlaceholder("Nhập tin nhắn...");
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

    await page.goto("/admin/assistant");
    const input = page.getByPlaceholder("Nhập tin nhắn...");
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

    await page.goto("/employee/assistant");

    // Send a message as employee
    const input = page.getByPlaceholder("Nhập tin nhắn...");
    await expect(input).toBeVisible();
    await input.fill("Số ngày phép còn lại?");
    await input.press("Enter");

    // Wait for response
    const response = page.locator("text=còn").first();
    await expect(response).toBeVisible({ timeout: 30000 });

    // Verify feedback buttons
    await expect(page.getByRole("button", { name: "Thumbs up" }).first()).toBeVisible();
    await expect(page.getByRole("button", { name: "Thumbs down" }).first()).toBeVisible();
  });
});
