import { expect, test, type Page } from "@playwright/test";

// ---------------------------------------------------------------------------
// Environment / Secrets
// ---------------------------------------------------------------------------

const baseURL = process.env.E2E_BASE_URL;
const hrState = process.env.E2E_HR_STORAGE_STATE;
const employeeState = process.env.E2E_EMPLOYEE_STORAGE_STATE;

function requireSession(state: string | undefined) {
  test.skip(
    !baseURL || !state,
    "Set E2E_BASE_URL and the role storage-state variables to run visual snapshot tests.",
  );
}

// ---------------------------------------------------------------------------
// Shared mock users
// ---------------------------------------------------------------------------

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

// ---------------------------------------------------------------------------
// Mock data helpers
// ---------------------------------------------------------------------------

const mockEmployees = [
  {
    id: "1",
    full_name: "Nguyễn Văn An",
    email: "an.nguyen@company.com",
    phone: "0901234567",
    department_id: "d1",
    position_id: "p1",
    is_active: true,
    employee_code: "NV-001",
    created_at: "2025-01-15T00:00:00.000Z",
  },
  {
    id: "2",
    full_name: "Trần Thị Bình",
    email: "binh.tran@company.com",
    phone: "0901234568",
    department_id: "d2",
    position_id: "p2",
    is_active: true,
    employee_code: "NV-002",
    created_at: "2025-02-20T00:00:00.000Z",
  },
  {
    id: "3",
    full_name: "Lê Văn Cường",
    email: "cuong.le@company.com",
    phone: "0901234569",
    department_id: "d1",
    position_id: "p3",
    is_active: false,
    employee_code: "NV-003",
    created_at: "2025-03-10T00:00:00.000Z",
  },
];

const mockDepartments = [
  { id: "d1", name: "Kỹ thuật", head_count: 15, created_at: "2024-01-01T00:00:00.000Z" },
  { id: "d2", name: "Nhân sự", head_count: 8, created_at: "2024-01-01T00:00:00.000Z" },
  { id: "d3", name: "Kế toán", head_count: 5, created_at: "2024-01-01T00:00:00.000Z" },
];

const mockPositions = [
  { id: "p1", title: "Kỹ sư phần mềm", department_id: "d1", created_at: "2024-01-01T00:00:00.000Z" },
  { id: "p2", title: "Chuyên viên nhân sự", department_id: "d2", created_at: "2024-01-01T00:00:00.000Z" },
  { id: "p3", title: "Trưởng phòng kỹ thuật", department_id: "d1", created_at: "2024-01-01T00:00:00.000Z" },
];

const mockPayslips = {
  payslips: [
    {
      id: "ps-001",
      employee_id: "emp-001",
      period_month: "2025-06",
      gross_salary: "25000000",
      net_salary: "20100000",
      pit_amount: "3200000",
      status: "published" as const,
      created_at: "2025-06-30T00:00:00.000Z",
    },
    {
      id: "ps-002",
      employee_id: "emp-002",
      period_month: "2025-06",
      gross_salary: "18000000",
      net_salary: "14800000",
      pit_amount: "2100000",
      status: "draft" as const,
      created_at: "2025-06-30T00:00:00.000Z",
    },
    {
      id: "ps-003",
      employee_id: "emp-003",
      period_month: "2025-05",
      gross_salary: "35000000",
      net_salary: "27500000",
      pit_amount: "5200000",
      status: "published" as const,
      created_at: "2025-05-31T00:00:00.000Z",
    },
  ],
  total: 3,
};

const mockCandidates = {
  candidates: [
    {
      id: "c-001",
      name: "Hoàng Minh Tâm",
      email: "tam.hoang@email.com",
      phone: "0912345678",
      skills: ["React", "TypeScript", "Node.js", "PostgreSQL"],
      confidence_score: 0.92,
      job_opening_title: "Kỹ sư phần mềm Senior",
      status: "new",
      created_at: "2025-07-01T00:00:00.000Z",
    },
    {
      id: "c-002",
      name: "Phạm Thị Dung",
      email: "dung.pham@email.com",
      phone: "0912345679",
      skills: ["UI/UX", "Figma", "Design System"],
      confidence_score: 0.85,
      job_opening_title: "UI/UX Designer",
      status: "interview_scheduled",
      created_at: "2025-06-28T00:00:00.000Z",
    },
    {
      id: "c-003",
      name: "Vũ Đình Khang",
      email: "khang.vu@email.com",
      phone: "0912345680",
      skills: ["Python", "Django", "AWS", "Docker"],
      confidence_score: 0.78,
      job_opening_title: "Backend Developer",
      status: "cv_review",
      created_at: "2025-06-25T00:00:00.000Z",
    },
  ],
  total_count: 3,
};

const mockInboxItems = {
  items: [
    {
      id: "in-001",
      gmail_thread_id: "thread-abc123",
      gmail_message_id: "msg-abc123",
      sender_name: "Nguyễn Thị Lan",
      sender_email: "lan.nguyen@email.com",
      subject: "Ứng tuyển vị trí Kỹ sư phần mềm",
      snippet: "Tôi gửi kèm CV và mong muốn được ứng tuyển vào vị trí Kỹ sư phần mềm tại công ty.",
      inbox_status: "ready_for_review",
      prediction_intent: "job_application",
      confidence_raw: 0.94,
      confidence_calibrated: 0.91,
      has_attachments: true,
      attachments_metadata: [{ name: "CV_NguyenThiLan.pdf", type: "application/pdf", size: 245760 }],
      evidence: [{ signal: "Email chứa từ khóa ứng tuyển và CV đính kèm" }],
      source_hints: [{ key: "source", value: "direct" }],
      correction_history: [],
      is_retry_exhausted: false,
      dismissed: false,
      dismissed_at: null,
      processing_error: null,
      created_at: "2025-07-05T08:30:00.000Z",
    },
    {
      id: "in-002",
      gmail_thread_id: "thread-def456",
      gmail_message_id: "msg-def456",
      sender_name: null,
      sender_email: "hr@partner-company.com",
      subject: "Giới thiệu ứng viên tiềm năng",
      snippet: "Chúng tôi xin giới thiệu một số ứng viên tiềm năng cho vị trí đang tuyển.",
      inbox_status: "needs_classification",
      prediction_intent: "partner_referral",
      confidence_raw: 0.72,
      confidence_calibrated: 0.68,
      has_attachments: false,
      attachments_metadata: [],
      evidence: [{ signal: "Email từ domain đối tác, không có CV trực tiếp" }],
      source_hints: [{ key: "domain", value: "partner-company.com" }],
      correction_history: [],
      is_retry_exhausted: false,
      dismissed: false,
      dismissed_at: null,
      processing_error: null,
      created_at: "2025-07-04T14:15:00.000Z",
    },
    {
      id: "in-003",
      gmail_thread_id: "thread-ghi789",
      gmail_message_id: "msg-ghi789",
      sender_name: "Trần Văn Minh",
      sender_email: "minh.tran@email.com",
      subject: "Thư cảm ơn sau phỏng vấn",
      snippet: "Cảm ơn công ty đã dành thời gian phỏng vấn tôi vào tuần trước.",
      inbox_status: "resolved",
      prediction_intent: "thank_you",
      confidence_raw: 0.97,
      confidence_calibrated: 0.95,
      has_attachments: false,
      attachments_metadata: [],
      evidence: [{ signal: "Email chứa từ khóa cảm ơn sau phỏng vấn" }],
      source_hints: [],
      correction_history: [],
      is_retry_exhausted: false,
      dismissed: false,
      dismissed_at: null,
      processing_error: null,
      created_at: "2025-07-03T10:00:00.000Z",
    },
  ],
  total: 3,
};

// ---------------------------------------------------------------------------
// Auth + API mocking
// ---------------------------------------------------------------------------

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
  // Catch-all — registered first so specific routes override it
  await page.route("**/api/**", async (route) => {
    await route.fulfill({ json: {} });
  });
  await page.route("**/api/auth/me", async (route) => {
    await route.fulfill({ json: user });
  });
  await page.route("**/api/auth/setup-status", async (route) => {
    await route.fulfill({ json: { setup_complete: true } });
  });
}

/** Register dashboard-specific API mocks */
async function mockDashboardApi(page: Page) {
      await page.route("**/api/employees?*", async (route) => {
        await route.fulfill({ json: { items: mockEmployees, total: mockEmployees.length, page: 1, page_size: 20 } });
      });
  await page.route("**/api/employees?*", async (route) => {
    await route.fulfill({ json: { items: mockEmployees, total: mockEmployees.length, page: 1, page_size: 20 } });
  });
  // Also catch /api/employees without params (the GET list all)
  await page.route("**/api/employees", async (route, request) => {
    if (request.method() === "GET") {
      await route.fulfill({ json: { items: mockEmployees, total: mockEmployees.length, page: 1, page_size: 20 } });
    } else {
      await route.fallback();
    }
  });
  await page.route("**/api/departments", async (route) => {
    await route.fulfill({ json: mockDepartments });
  });
  await page.route("**/api/positions", async (route) => {
    await route.fulfill({ json: mockPositions });
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

/** Register employee-list-specific API mocks */
async function mockEmployeeListApi(page: Page) {
  await page.route("**/api/employees?*", async (route) => {
    await route.fulfill({ json: { items: mockEmployees, total: mockEmployees.length, page: 1, page_size: 20 } });
  });
  await page.route("**/api/employees", async (route, request) => {
    if (request.method() === "GET") {
      await route.fulfill({ json: { items: mockEmployees, total: mockEmployees.length, page: 1, page_size: 20 } });
    } else {
      await route.fallback();
    }
  });
  await page.route("**/api/departments", async (route) => {
    await route.fulfill({ json: mockDepartments });
  });
  await page.route("**/api/positions", async (route) => {
    await route.fulfill({ json: mockPositions });
  });
}

/** Register payroll-specific API mocks */
async function mockPayrollApi(page: Page) {
  await page.route("**/api/admin/payslips*", async (route) => {
    await route.fulfill({ json: mockPayslips });
  });
}

/** Register recruitment / candidate-specific API mocks */
async function mockRecruitmentApi(page: Page) {
  await page.route("**/api/recruitment/candidates*", async (route) => {
    await route.fulfill({ json: mockCandidates });
  });
}

/** Register inbox-specific API mocks */
async function mockInboxApi(page: Page) {
  await page.route("**/api/recruitment/inbox*", async (route) => {
    await route.fulfill({ json: mockInboxItems });
  });
}

// ---------------------------------------------------------------------------
// Dark mode helper
// ---------------------------------------------------------------------------

async function enableDarkMode(page: Page) {
  await page.evaluate(() => {
    localStorage.setItem("theme", "dark");
    document.documentElement.classList.add("dark");
  });
}

// ---------------------------------------------------------------------------
// Snapshot threshold
// ---------------------------------------------------------------------------

const SNAPSHOT_THRESHOLD = 0.15;

// ===========================================================================
// Visual Snapshot Tests
// ===========================================================================

test.describe("Visual snapshots — Login page @hr", () => {
  test.beforeEach(async ({ page }) => {
    requireSession(hrState);
  });

  test("Login page — light mode", async ({ page }) => {
    await page.goto("/login");
    // Wait for the login form to render (not just the loading spinner)
    await expect(page.getByRole("heading", { name: "Vroom HR" })).toBeVisible();
    await page.waitForTimeout(300); // Let animations settle
    await expect(page).toHaveScreenshot("login-light.png", {
      fullPage: true,
      maxDiffPixelRatio: SNAPSHOT_THRESHOLD,
    });
  });

  test("Login page — dark mode", async ({ page }) => {
    await page.goto("/login");
    await expect(page.getByRole("heading", { name: "Vroom HR" })).toBeVisible();
    // Toggle dark mode via the ThemeToggle button
    await page.getByRole("button", { name: "Chuyển đổi giao diện" }).click();
    await page.waitForTimeout(300); // Let CSS transition settle
    await expect(page).toHaveScreenshot("login-dark.png", {
      fullPage: true,
      maxDiffPixelRatio: SNAPSHOT_THRESHOLD,
    });
  });
});

test.describe("Visual snapshots — Dashboard (HR view) @hr", () => {
  test.beforeEach(async ({ page }) => {
    requireSession(hrState);
    await mockAuthenticatedShell(page, hrUser);
    await mockDashboardApi(page);
  });

  test("Dashboard — light mode @hr", async ({ page }) => {
    await page.goto("/");
    // Wait for sidebar nav and stats to render
    await expect(page.getByRole("navigation", { name: "Điều hướng chính" })).toBeVisible({ timeout: 15000 });
    await expect(page.getByText("Nhân viên").first()).toBeVisible();
    await page.waitForTimeout(500); // Let stagger animations settle
    await expect(page).toHaveScreenshot("dashboard-light.png", {
      fullPage: true,
      maxDiffPixelRatio: SNAPSHOT_THRESHOLD,
    });
  });

  test("Dashboard — dark mode @hr", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByRole("navigation", { name: "Điều hướng chính" })).toBeVisible({ timeout: 15000 });
    await expect(page.getByText("Nhân viên").first()).toBeVisible();
    await enableDarkMode(page);
    // Some components may need a re-render after theme change
    await page.waitForTimeout(300);
    await expect(page).toHaveScreenshot("dashboard-dark.png", {
      fullPage: true,
      maxDiffPixelRatio: SNAPSHOT_THRESHOLD,
    });
  });
});

test.describe("Visual snapshots — Employee list @hr", () => {
  test.beforeEach(async ({ page }) => {
    requireSession(hrState);
    await mockAuthenticatedShell(page, hrUser);
    await mockEmployeeListApi(page);
  });

    test("Employee list @hr", async ({ page }) => {
      await page.goto("/employees");
      await page.waitForLoadState("networkidle");
      await page.waitForTimeout(1500);
      await expect(page).toHaveScreenshot("employee-list-light.png", {
        fullPage: true,
        maxDiffPixelRatio: SNAPSHOT_THRESHOLD,
      });
    });
});

test.describe("Visual snapshots — Employee self-service dashboard @employee", () => {
  test.beforeEach(async ({ page }) => {
    requireSession(employeeState);
    await mockAuthenticatedShell(page, employeeUser);
  });

  test("Employee dashboard @employee", async ({ page }) => {
    await page.goto("/employee/dashboard");
    await page.waitForTimeout(500); // Let page load + animations settle
    await expect(page).toHaveScreenshot("employee-dashboard-light.png", {
      fullPage: true,
      maxDiffPixelRatio: SNAPSHOT_THRESHOLD,
    });
  });
});

test.describe("Visual snapshots — Payroll @hr", () => {
  test.beforeEach(async ({ page }) => {
    requireSession(hrState);
    await mockAuthenticatedShell(page, hrUser);
    await mockPayrollApi(page);
  });

  test("Payroll page @hr", async ({ page }) => {
    await page.goto("/payroll");
    await expect(page.getByText("Bảng lương")).toBeVisible({ timeout: 15000 });
    // Wait for table data or period cards to render
    await expect(page.getByText("Tổng phiếu lương")).toBeVisible();
    await page.waitForTimeout(300);
    await expect(page).toHaveScreenshot("payroll-light.png", {
      fullPage: true,
      maxDiffPixelRatio: SNAPSHOT_THRESHOLD,
    });
  });
});

test.describe("Visual snapshots — Recruitment @hr", () => {
  test.beforeEach(async ({ page }) => {
    requireSession(hrState);
    await mockAuthenticatedShell(page, hrUser);
    await mockRecruitmentApi(page);
  });

    test("Recruitment candidate list @hr", async ({ page }) => {
      await page.goto("/recruitment");
      await page.waitForLoadState("networkidle");
      await page.waitForTimeout(1500);
      await expect(page).toHaveScreenshot("recruitment-light.png", {
        fullPage: true,
        maxDiffPixelRatio: SNAPSHOT_THRESHOLD,
      });
    });
});

test.describe("Visual snapshots — Recruitment inbox @hr", () => {
  test.beforeEach(async ({ page }) => {
    requireSession(hrState);
    await mockAuthenticatedShell(page, hrUser);
    await mockInboxApi(page);
  });

  test("Recruitment inbox @hr", async ({ page }) => {
    await page.goto("/recruitment/inbox");
    await expect(page.getByText("Hộp thư tuyển dụng")).toBeVisible({ timeout: 15000 });
    await expect(page.getByText("Ứng tuyển vị trí")).toBeVisible();
    await page.waitForTimeout(300);
    await expect(page).toHaveScreenshot("recruitment-inbox-light.png", {
      fullPage: true,
      maxDiffPixelRatio: SNAPSHOT_THRESHOLD,
    });
  });
});
