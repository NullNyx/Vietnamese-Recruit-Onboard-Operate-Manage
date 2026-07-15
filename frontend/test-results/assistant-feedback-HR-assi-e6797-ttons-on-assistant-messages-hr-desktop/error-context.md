# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: assistant-feedback.spec.ts >> HR assistant feedback @hr >> shows thumbs up/down buttons on assistant messages
- Location: e2e/assistant-feedback.spec.ts:29:7

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: getByPlaceholder('Nhập tin nhắn...')
Expected: visible
Timeout: 5000ms
Error: element(s) not found

Call log:
  - Expect "toBeVisible" with timeout 5000ms
  - waiting for getByPlaceholder('Nhập tin nhắn...')

```

```yaml
- text: V
- heading "Vroom HR" [level=1]
- paragraph: Đăng nhập vào hệ thống
- img
- text: Không thể kiểm tra trạng thái khởi tạo Email
- textbox "Email":
  - /placeholder: name@company.com
- text: Mật khẩu
- textbox "Mật khẩu"
- button "Đăng nhập"
- region "Notifications alt+T"
- alert
```

# Test source

```ts
  1   | import { expect, test, type Page } from "@playwright/test";
  2   | 
  3   | const baseURL = process.env.E2E_BASE_URL;
  4   | const hrState = process.env.E2E_HR_STORAGE_STATE;
  5   | const employeeState = process.env.E2E_EMPLOYEE_STORAGE_STATE;
  6   | function requireSession(state: string | undefined) {
  7   |   test.skip(
  8   |     !baseURL || !state,
  9   |     "Set E2E_BASE_URL and the role storage-state variables to run browser seam tests.",
  10  |   );
  11  | }
  12  | 
  13  | function observeConsoleIssues() {
  14  |   const issues: string[] = [];
  15  |   return {
  16  |     issues,
  17  |     onMessage(message: { type(): string; text(): string }) {
  18  |       if (message.type() === "error" || message.type() === "warning") {
  19  |         issues.push(`[${message.type()}] ${message.text()}`);
  20  |       }
  21  |     },
  22  |   };
  23  | }
  24  | 
  25  | // ---------------------------------------------------------------------------
  26  | // HR Assistant feedback (@hr)
  27  | // ---------------------------------------------------------------------------
  28  | test.describe("HR assistant feedback @hr", () => {
  29  |   test("shows thumbs up/down buttons on assistant messages", async ({ page }) => {
  30  |     requireSession(hrState);
  31  |     const consoleIssues = observeConsoleIssues();
  32  |     page.on("console", consoleIssues.onMessage);
  33  | 
  34  |     await page.goto("/admin/assistant");
  35  | 
  36  |     // Send a message to trigger assistant response
  37  |     const input = page.getByPlaceholder("Nhập tin nhắn...");
> 38  |     await expect(input).toBeVisible();
      |                         ^ Error: expect(locator).toBeVisible() failed
  39  |     await input.fill("Có bao nhiêu candidate đang reviewing?");
  40  |     await input.press("Enter");
  41  | 
  42  |     // Wait for assistant response to appear
  43  |     const response = page.locator("text=Hiện tại").first();
  44  |     await expect(response).toBeVisible({ timeout: 30000 });
  45  | 
  46  |     // Verify thumbs up/down buttons are present
  47  |     await expect(page.getByRole("button", { name: "Thumbs up" }).first()).toBeVisible();
  48  |     await expect(page.getByRole("button", { name: "Thumbs down" }).first()).toBeVisible();
  49  | 
  50  |     expect(consoleIssues.issues).toEqual([]);
  51  |   });
  52  | 
  53  |   test("clicking thumbs up submits feedback and shows Đã đánh giá", async ({ page }) => {
  54  |     requireSession(hrState);
  55  | 
  56  |     await page.goto("/admin/assistant");
  57  |     const input = page.getByPlaceholder("Nhập tin nhắn...");
  58  |     await input.fill("Xin chào");
  59  |     await input.press("Enter");
  60  | 
  61  |     const response = page.locator("text=Hiện tại").first();
  62  |     await expect(response).toBeVisible({ timeout: 30000 });
  63  | 
  64  |     // Click thumbs up
  65  |     await page.getByRole("button", { name: "Thumbs up" }).first().click();
  66  | 
  67  |     // Verify "Đã đánh giá" state and disabled buttons
  68  |     await expect(page.getByText("Đã đánh giá")).toBeVisible();
  69  |     await expect(page.getByRole("button", { name: "Thumbs up" }).first()).toBeDisabled();
  70  |     await expect(page.getByRole("button", { name: "Thumbs down" }).first()).toBeDisabled();
  71  |   });
  72  | 
  73  |   test("clicking thumbs down shows optional text input", async ({ page }) => {
  74  |     requireSession(hrState);
  75  | 
  76  |     await page.goto("/admin/assistant");
  77  |     const input = page.getByPlaceholder("Nhập tin nhắn...");
  78  |     await input.fill("Kiểm tra chức năng");
  79  |     await input.press("Enter");
  80  | 
  81  |     const response = page.locator("text=Hiện tại").first();
  82  |     await expect(response).toBeVisible({ timeout: 30000 });
  83  | 
  84  |     // Click thumbs down
  85  |     await page.getByRole("button", { name: "Thumbs down" }).first().click();
  86  | 
  87  |     // Verify optional text input appears
  88  |     const textarea = page.locator("textarea").last();
  89  |     await expect(textarea).toBeVisible();
  90  |   });
  91  | });
  92  | 
  93  | // ---------------------------------------------------------------------------
  94  | // Employee Assistant feedback (@employee)
  95  | // ---------------------------------------------------------------------------
  96  | test.describe("Employee assistant feedback @employee", () => {
  97  |   test("shows thumbs up/down on employee assistant messages", async ({ page }) => {
  98  |     requireSession(employeeState);
  99  | 
  100 |     await page.goto("/employee/assistant");
  101 | 
  102 |     // Send a message as employee
  103 |     const input = page.getByPlaceholder("Nhập tin nhắn...");
  104 |     await expect(input).toBeVisible();
  105 |     await input.fill("Số ngày phép còn lại?");
  106 |     await input.press("Enter");
  107 | 
  108 |     // Wait for response
  109 |     const response = page.locator("text=còn").first();
  110 |     await expect(response).toBeVisible({ timeout: 30000 });
  111 | 
  112 |     // Verify feedback buttons
  113 |     await expect(page.getByRole("button", { name: "Thumbs up" }).first()).toBeVisible();
  114 |     await expect(page.getByRole("button", { name: "Thumbs down" }).first()).toBeVisible();
  115 |   });
  116 | });
  117 | 
```