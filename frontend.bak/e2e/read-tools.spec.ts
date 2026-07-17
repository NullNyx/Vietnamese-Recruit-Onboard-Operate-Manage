import { expect, test, type Page } from "@playwright/test";

const baseURL = process.env.E2E_BASE_URL;
const hrState = process.env.E2E_HR_STORAGE_STATE;
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

async function mockAuthenticatedShell(page: Page, chatResponse?: string) {
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
    ["vroom-hr:e2e-current-user", hrUser],
  );
  // Catch-all for unhandled API routes — register first so specific routes (registered later) take priority
  await page.route("**/api/**", async (route) => {
    await route.fulfill({ json: {} });
  });
  await page.route("**/api/auth/me", async (route) => {
    await route.fulfill({ json: hrUser });
  });
  await page.route("**/api/auth/setup-status", async (route) => {
    await route.fulfill({ json: { setup_complete: true } });
  });
  await page.route("**/api/assistant/session/start", async (route) => {
    await route.fulfill({ json: { session_id: "e2e-session-id" } });
  });
  await page.route("**/api/assistant/session/end", async (route) => {
    await route.fulfill({ json: {} });
  });
  await page.route("**/api/assistant/chat", async (route) => {
    await route.fulfill({
      json: {
        messages: [
          {
            role: "assistant",
            content:
              chatResponse ??
              "Hiện tại có 5 candidate đang trong quy trình tuyển dụng.",
          },
        ],
        draft_action: null,
      },
    });
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

// ---------------------------------------------------------------------------
// HR Assistant Read-Tools (@hr)
// ---------------------------------------------------------------------------
test.describe("HR assistant read tools @hr", () => {
  test("#228 get_candidate_parsed_cv — shows parsed CV data", async ({ page }) => {
    requireSession(hrState);
    const consoleIssues = observeConsoleIssues();
    page.on("console", consoleIssues.onMessage);

    await mockAuthenticatedShell(
      page,
      "CV của Nguyễn Văn A:\n" +
        "- Kỹ năng: React, Python, PostgreSQL\n" +
        "- Kinh nghiệm: 5 năm tại FPT Software\n" +
        "- Học vấn: Đại học Bách Khoa Hà Nội (2015-2019)\n" +
        "- Tóm tắt: Full-stack developer với kinh nghiệm xây dựng hệ thống HR\n",
    );
    await page.goto("/");
    await expect(page.getByRole("navigation", { name: "Điều hướng chính" })).toBeVisible();
    await page.goto("/admin/assistant");

    // Send a question that triggers get_candidate_parsed_cv
    const input = page.getByPlaceholder("Nhập tin nhắn...");
    await expect(input).toBeVisible({ timeout: 15000 });
    await input.fill("Xem CV của Nguyễn Văn A");
    await input.press("Enter");

    // Verify CV data is displayed
    await expect(page.locator("text=Kỹ năng").first()).toBeVisible({ timeout: 30000 });
    await expect(page.locator("text=React").first()).toBeVisible();
    await expect(page.locator("text=Python").first()).toBeVisible();
    await expect(page.locator("text=PostgreSQL").first()).toBeVisible();
    await expect(page.locator("text=FPT Software").first()).toBeVisible();
    await expect(page.locator("text=Bách Khoa").first()).toBeVisible();

    expect(consoleIssues.issues).toEqual([]);
  });

  test("#229 list_interviews_for_candidate — shows interview schedule", async ({ page }) => {
    requireSession(hrState);
    const consoleIssues = observeConsoleIssues();
    page.on("console", consoleIssues.onMessage);

    await mockAuthenticatedShell(
      page,
      "Lịch phỏng vấn của Nguyễn Văn A:\n" +
        "1. 15/07/2026 09:00 — Phỏng vấn kỹ thuật tại Văn phòng Hồ Chí Minh (Trạng thái: Đã lên lịch)\n" +
        "2. 20/07/2026 14:00 — Phỏng vấn văn hóa qua Google Meet (Trạng thái: Đã lên lịch)\n" +
        "Tổng cộng: 2 buổi phỏng vấn",
    );
    await page.goto("/");
    await expect(page.getByRole("navigation", { name: "Điều hướng chính" })).toBeVisible();
    await page.goto("/admin/assistant");

    const input = page.getByPlaceholder("Nhập tin nhắn...");
    await expect(input).toBeVisible({ timeout: 15000 });
    await input.fill("Lịch phỏng vấn của Nguyễn Văn A");
    await input.press("Enter");

    // Verify interview schedule is displayed
    await expect(page.locator("text=15/07/2026").first()).toBeVisible({ timeout: 30000 });
    await expect(page.locator("text=09:00").first()).toBeVisible();
    await expect(page.locator("text=Google Meet").first()).toBeVisible();
    await expect(page.locator("text=Hồ Chí Minh").first()).toBeVisible();
    await expect(page.locator("text=2 buổi").first()).toBeVisible();

    expect(consoleIssues.issues).toEqual([]);
  });

  test("#230 get_onboarding_task_details — shows onboarding task progress", async ({ page }) => {
    requireSession(hrState);
    const consoleIssues = observeConsoleIssues();
    page.on("console", consoleIssues.onMessage);

    await mockAuthenticatedShell(
      page,
      "Tiến độ Onboarding của Trần Thị B (Nhân viên Kế Toán):\n" +
        "Trạng thái: Đang tiến hành — Hoàn thành 3/5 nhiệm vụ\n" +
        "✅ Ký hợp đồng lao động\n" +
        "✅ Cấp tài khoản email và các hệ thống\n" +
        "✅ Thiết lập máy tính và phần mềm\n" +
        "⏳ Đào tạo chính sách công ty\n" +
        "⏳ Giới thiệu với các phòng ban",
    );
    await page.goto("/");
    await expect(page.getByRole("navigation", { name: "Điều hướng chính" })).toBeVisible();
    await page.goto("/admin/assistant");

    const input = page.getByPlaceholder("Nhập tin nhắn...");
    await expect(input).toBeVisible({ timeout: 15000 });
    await input.fill("Xem tiến độ onboarding của Trần Thị B");
    await input.press("Enter");

    // Verify onboarding task details are displayed
    await expect(page.locator("text=3/5").first()).toBeVisible({ timeout: 30000 });
    await expect(page.locator("text=Ký hợp đồng").first()).toBeVisible();
    await expect(page.locator("text=Cấp tài khoản").first()).toBeVisible();
    await expect(page.locator("text=Thiết lập máy tính").first()).toBeVisible();
    await expect(page.locator("text=Đào tạo chính sách").first()).toBeVisible();

    expect(consoleIssues.issues).toEqual([]);
  });

  test("#231 list_job_openings — shows open job openings with headcount", async ({ page }) => {
    requireSession(hrState);
    const consoleIssues = observeConsoleIssues();
    page.on("console", consoleIssues.onMessage);

    await mockAuthenticatedShell(
      page,
      "Danh sách job openings đang mở:\n" +
        "1. Senior Frontend Developer (Phòng Kỹ thuật) — headcount: 2/5, Trạng thái: open\n" +
        "2. HR Manager (Phòng Nhân sự) — headcount: 1/2, Trạng thái: open\n" +
        "3. Product Designer (Phòng Sản phẩm) — headcount: 0/3, Trạng thái: open\n" +
        "Tổng cộng: 3 job openings.",
    );
    await page.goto("/");
    await expect(page.getByRole("navigation", { name: "Điều hướng chính" })).toBeVisible();
    await page.goto("/admin/assistant");

    const input = page.getByPlaceholder("Nhập tin nhắn...");
    await expect(input).toBeVisible({ timeout: 15000 });
    await input.fill("Danh sách job openings đang tuyển");
    await input.press("Enter");

    // Verify job openings are displayed
    await expect(page.locator("text=Senior Frontend Developer").first()).toBeVisible({ timeout: 30000 });
    await expect(page.locator("text=HR Manager").first()).toBeVisible();
    await expect(page.locator("text=Product Designer").first()).toBeVisible();
    await expect(page.locator("text=2/5").first()).toBeVisible();
    await expect(page.locator("text=3 job openings").first()).toBeVisible();

    expect(consoleIssues.issues).toEqual([]);
  });

  test("#232 get_department_info — shows department structure and positions", async ({ page }) => {
    requireSession(hrState);
    const consoleIssues = observeConsoleIssues();
    page.on("console", consoleIssues.onMessage);

    await mockAuthenticatedShell(
      page,
      "Thông tin phòng ban Kỹ thuật:\n" +
        "Mô tả: Phụ trách phát triển sản phẩm và hệ thống nội bộ\n" +
        "Số nhân viên: 12 người\n" +
        "Quản lý: Nguyễn Văn B (Technical Lead), Trần Văn C (Engineering Manager)\n" +
        "Các vị trí:\n" +
        "- Technical Lead: 2 nhân viên\n" +
        "- Senior Developer: 5 nhân viên\n" +
        "- Junior Developer: 5 nhân viên",
    );
    await page.goto("/");
    await expect(page.getByRole("navigation", { name: "Điều hướng chính" })).toBeVisible();
    await page.goto("/admin/assistant");

    const input = page.getByPlaceholder("Nhập tin nhắn...");
    await expect(input).toBeVisible({ timeout: 15000 });
    await input.fill("Xem thông tin phòng ban Kỹ thuật");
    await input.press("Enter");

    // Verify department info is displayed
    await expect(page.locator("text=Kỹ thuật").first()).toBeVisible({ timeout: 30000 });
    await expect(page.locator("text=12 người").first()).toBeVisible();
    await expect(page.locator("text=Nguyễn Văn B").first()).toBeVisible();
    await expect(page.locator("text=Technical Lead").first()).toBeVisible();
    await expect(page.locator("text=Senior Developer").first()).toBeVisible();
    await expect(page.locator("text=Junior Developer").first()).toBeVisible();

    expect(consoleIssues.issues).toEqual([]);
  });
});
