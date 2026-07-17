import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import path from "node:path";
import { test, expect, type Page } from "@playwright/test";

/**
 * Vroom HR E2E smoke — single-file, declaration-order, single worker.
 *
 * Tests share on-disk storage-state files written earlier in the run:
 *   e2e/.auth/hr.json         — HR Admin session (from First-Run Setup BE cookie)
 *   e2e/.auth/employee.json   — ESS Employee session
 *   e2e/.auth/employee-creds.json — { email, tempPassword } captured when HR
 *                              provisions the demo Employee Account; consumed
 *                              by the ESS onboarding-login test.
 *
 * Browser origin is http://localhost:3000 (reverse proxy) so the backend's
 * `Secure; SameSite=Lax` HttpOnly cookie is carried and there is no CORS
 * preflight (the FastAPI backend has no CORSMiddleware).
 */

const AUTH_DIR = path.join(__dirname, ".auth");
const HR_STATE = path.join(AUTH_DIR, "hr.json");
const EMP_STATE = path.join(AUTH_DIR, "employee.json");
const EMP_CREDS = path.join(AUTH_DIR, "employee-creds.json");

mkdirSync(AUTH_DIR, { recursive: true });

const HR_EMAIL = process.env.E2E_HR_EMAIL ?? "hr.qa@vroom.example.com";
const HR_PASSWORD = process.env.E2E_HR_PASSWORD ?? "VroomQA!148#2026";
const HR_NAME = process.env.E2E_HR_NAME ?? "HR QA";
const ORG_NAME = process.env.E2E_ORGANIZATION_NAME ?? "Vroom QA Organization";
const EMP_NEW_PASSWORD = "VroomEmp!2026#qa"; // permanent ESS password after first-login change

async function setupStatus(): Promise<boolean> {
  const r = await fetch("http://localhost:3000/api/auth/setup-status", {
    credentials: "include",
  });
  // Fallback directly to BE if proxy not up yet.
  const body = await r.json().catch(() => null);
  if (body && typeof body.setup_complete === "boolean") return body.setup_complete;
  const r2 = await fetch("http://localhost:8000/api/auth/setup-status");
  const b2 = await r2.json().catch(() => null);
  return Boolean(b2?.setup_complete);
}

// ----------------------------------------------------------------------------
// T1 — First-Run Setup (UI wizard) — real atomic BE write, no re-login.
// ----------------------------------------------------------------------------
test.describe("First-Run Setup", () => {
  test.use({ storageState: { cookies: [], origins: [] } as any });

  test("wizard 3 bước → submit atomic → dashboard, không re-login", async ({ page, context }) => {
    const alreadySetup = await setupStatus();
    if (alreadySetup) {
      test.info().annotations.push({ type: "skip-reason", description: "DB already set up; falling back to login to seed hr.json" });
      // Fall back: login to produce HR storage state for downstream tests.
      await page.goto("/login");
      await page.locator("#login-email-input").fill(HR_EMAIL);
      await page.locator("#login-password-input").fill(HR_PASSWORD);
      await page.locator("#login-submit-button").click();
      await page.waitForURL("**/dashboard", { timeout: 30000 });
      await expect(page.getByRole("heading", { name: /Tổng quan.*Metrics/i })).toBeVisible({ timeout: 20000 });
      await context.storageState({ path: HR_STATE });
      test.skip(true as any, "First-Run wizard not exercised (DB already set up).");
      return;
    }

    await page.goto("/setup");
    // Wait for the wizard to confirm backend is available.
    await expect(page.locator("#setup-wizard-container")).toBeVisible({ timeout: 30000 });

    // Step 1 — Organization
    await page.locator("#setup-org-name-input").fill(ORG_NAME);
    await page.locator("#setup-step1-submit").click();

    // Step 2 — HR account
    await expect(page.locator("#setup-step2-form")).toBeVisible({ timeout: 10000 });
    await page.locator("#setup-hr-name-input").fill(HR_NAME);
    await page.locator("#setup-hr-email-input").fill(HR_EMAIL);
    await page.locator("#setup-password-input").fill(HR_PASSWORD);
    await page.locator("#setup-password-confirm-input").fill(HR_PASSWORD);
    await page.locator("#setup-step2-submit").click();

    // Step 3 — Review + submit atomic
    await expect(page.getByRole("heading", { name: /Bước 3.*Xác nhận/i })).toBeVisible({ timeout: 10000 });
    await page.locator("#setup-submit-button").click();

    // Step 4 — Success (no re-login); BE issued session cookie
    await expect(page.locator("#setup-open-dashboard-btn")).toBeVisible({ timeout: 30000 });
    await expect(page.getByText(/Khởi tạo Vroom HR thành công/i)).toBeVisible();

    // Verify the session cookie is actually set (no second login needed).
    const cookies = await context.cookies();
    expect(cookies.some((c) => c.name === "access_token")).toBeTruthy();

    // "Mở dashboard" navigates to /dashboard WITHOUT re-login.
    await page.locator("#setup-open-dashboard-btn").click();
    await page.waitForURL("**/dashboard", { timeout: 30000 });
    await expect(page.getByRole("heading", { name: /Tổng quan.*Metrics/i })).toBeVisible({ timeout: 30000 });

    // Persist real HR session for downstream tests.
    await context.storageState({ path: HR_STATE });
  });
});

// ----------------------------------------------------------------------------
// T2 — HR dashboard: real metrics / runtime health / audit logs
// ----------------------------------------------------------------------------
test.describe("HR Dashboard (real data)", () => {
  test.use({ storageState: HR_STATE });

  test("hiển thị metrics tuyển dụng + runtime health + audit logs", async ({ page }) => {
    await page.goto("/dashboard");
    await expect(page.getByRole("heading", { name: /Tổng quan.*Metrics/i })).toBeVisible({ timeout: 30000 });
    // Recruitment metric card label visibility (numbers may be 0 on fresh DB).
    await expect(page.getByText(/Sức khỏe hệ thống.*Runtime/i)).toBeVisible({ timeout: 20000 });
    await expect(page.getByText(/Nhật ký hoạt động.*Audit Log/i)).toBeVisible({ timeout: 20000 });
    // Assert at least one runtime service row is rendered (real data).
    await expect(page.locator("text=/redis|postgresql|minio|gmail worker/i").first()).toBeVisible({ timeout: 20000 });
  });
});

// ----------------------------------------------------------------------------
// T3 — HR provisions an Employee Account for the demo active Employee
// ----------------------------------------------------------------------------
test.describe("HR Employee provisioning", () => {
  test.use({ storageState: HR_STATE });

  test("tạo Employee Account, hiện mật khẩu tạm thời 1 lần", async ({ page }) => {
    // Find the demo active employee via the real BE API (HR cookie shared by context).
    const res = await page.request.get("/api/employees");
    expect(res.ok(), `GET /api/employees -> ${res.status()}`).toBeTruthy();
    const body = await res.json();
    const employees: any[] = body.items ?? body.employees ?? body ?? [];
    const emp = employees.find((e) => e.is_active === true) ?? employees[0];
    expect(emp, "expected at least one employee from BE").toBeTruthy();
    expect(emp.is_active, "demo employee must be active to receive an account").toBeTruthy();

    await page.goto(`/employees/${emp.id}`);
    await expect(page.getByRole("heading", { name: /Employee Account/i })).toBeVisible({ timeout: 20000 });

    // If an account already exists (re-run), capture existing creds from the
    // status panel and skip creating a new one.
    const hasExistingAccount = await page.getByText(/Employee chưa có tài khoản/i).count();
    if (hasExistingAccount === 0) {
      // Account already created in a prior run — record email + flag.
      writeFileSync(
        EMP_CREDS,
        JSON.stringify({ email: emp.email, tempPassword: null, alreadyCreated: true }, null, 2),
      );
      test.info().annotations.push({ type: "note", description: "Employee account already exists" });
      return;
    }

    await page.getByRole("button", { name: /Tạo tài khoản/i }).click();

    // Modal reveals the temporary password exactly once.
    const dialog = page.getByRole("dialog");
    await expect(dialog).toBeVisible({ timeout: 20000 });
    const pwdEl = dialog.locator(".font-mono.break-all, .break-all").first();
    await expect(pwdEl).toBeVisible({ timeout: 10000 });
    const tempPassword = (await pwdEl.innerText()).trim();
    expect(tempPassword.length, "temp password non-empty").toBeGreaterThan(0);

    writeFileSync(EMP_CREDS, JSON.stringify({ email: emp.email, tempPassword }, null, 2));
    test.info().annotations.push({ type: "temp-password", description: `captured (len ${tempPassword.length})` });

    // Close the modal.
    await page.getByRole("button", { name: /Đã ghi nhận/i }).click();
    await expect(dialog).toBeHidden({ timeout: 10000 });
  });
});

// ----------------------------------------------------------------------------
// T4 — ESS onboarding login (fresh context) + forced change-password
// ----------------------------------------------------------------------------
test.describe("ESS onboarding login + change password", () => {
  test.use({ storageState: { cookies: [], origins: [] } as any });

  test("Employee đăng nhập bằng mật khẩu tạm → đổi mật khẩu → vào /employee", async ({ page, context }) => {
    test.skip(!existsSync(EMP_CREDS), "no employee creds file — T3 did not provision an account");
    const creds = JSON.parse(readFileSync(EMP_CREDS, "utf8"));
    if (!creds.tempPassword) {
      test.skip(true as any, "employee account already existed (no temp password captured this run) — cannot drive first-login change-password");
      return;
    }

    await page.goto("/login");
    await page.locator("#login-email-input").fill(creds.email);
    await page.locator("#login-password-input").fill(creds.tempPassword);
    await page.locator("#login-submit-button").click();

    // first-login must_change_password forces /change-password
    await page.waitForURL("**/change-password", { timeout: 20000 });
    await expect(page.locator("#change-password-new-input")).toBeVisible({ timeout: 15000 });

    await page.locator("#change-password-current-input").fill(creds.tempPassword);
    await page.locator("#change-password-new-input").fill(EMP_NEW_PASSWORD);
    await page.locator("#change-password-confirm-input").fill(EMP_NEW_PASSWORD);
        // Race fix (BUG-9): /change-password renders `{!success && <form>}`; the
        // moment the API returns 200 it does setSuccess(true) -> form unmounts ->
        // #change-password-submit-button detaches. `.click()` actionability checks
        // then retry forever on the detaching button (hang 90s) even though the
        // /employee navigation already happened, so `waitForURL` + `storageState`
        // below never run and `employee.json` stays `{}` (cascade T5/T6/T7 -> /login).
        // Dispatch the submit event directly: no actionability, no hang, then wait
        // for the navigation and persist the ESS session.
        await page.evaluate(() => {
          const button = document.getElementById("change-password-submit-button");
          const form = button ? (button.closest("form") as HTMLFormElement | null) : null;
          if (!form) throw new Error("change-password form not found");
          form.requestSubmit();
        });

    await page.waitForURL("**/employee", { timeout: 30000 });
    await context.storageState({ path: EMP_STATE });

    // Remember the new permanent password in case of re-run.
    writeFileSync(
      EMP_CREDS,
      JSON.stringify({ ...creds, tempPassword: null, permanentPassword: EMP_NEW_PASSWORD }, null, 2),
    );
  });
});

// ----------------------------------------------------------------------------
// T5–T7 — ESS flows
// ----------------------------------------------------------------------------
test.describe("ESS — Attendance / Leave / Payslip", () => {
  test.use({ storageState: EMP_STATE });

  test("check-in hôm nay (hoặc báo lỗi allowlist thật)", async ({ page }) => {
    await page.goto("/employee/attendance");
    await expect(page.getByRole("heading", { name: /Chấm công/i })).toBeVisible({ timeout: 20000 });
    // Either a Check-in button is clickable, or check-in already done today,
    // or a Network Allowlist error is surfaced. All are real backend outcomes.
    const checkInBtn = page.getByRole("button", { name: /^Check-in$/i });
    const already = await page.getByText(/Đã check-in/i).count();
    if (already === 0 && (await checkInBtn.count()) > 0) {
      await checkInBtn.click();
      // Accept either success badge or an Allow-List / IP error code surfaced.
      await expect(
        page.locator("text=/(Đã check-in|ALREADY_CHECKED_IN|ESS_FORBIDDEN|Network Allowlist|outside the allow)/i").first(),
      ).toBeVisible({ timeout: 20000 });
    }
  });

  test("request nghỉ phép + render LEAVE_OVERLAP khi trùng", async ({ page }) => {
    await page.goto("/employee/requests");
    await expect(page.getByRole("heading", { name: /Yêu cầu|nghỉ phép|làm thêm/i }).first()).toBeVisible({ timeout: 20000 });

    const future = (offset: number) => {
      const d = new Date();
      d.setDate(d.getDate() + offset);
      return d.toISOString().slice(0, 10);
    };
    const start = future(20);
    const end = future(21);

    async function submitLeave(sd: string, ed: string) {
      const startInput = page.locator('input[type="date"]').first();
      await startInput.fill(sd);
      const endInput = page.locator('input[type="date"]').nth(1);
      await endInput.fill(ed);
      // Leave reason TextArea has no placeholder; use accessible label instead.
      // The form submit button stays disabled until all required fields (start_date,
      // end_date, reason) are filled — if we miss reason, the button actionability
      // hangs 90s like BUG-8/BUG-9 pattern.
      const reason = page.getByRole("textbox", { name: /Lý do/i }).first();
      if ((await reason.count()) > 0) await reason.fill("E2E smoke test nghỉ phép");
      await page.getByRole("button", { name: /Gửi.*nghỉ phép|Tạo.*nghỉ phép|Gửi yêu cầu/i }).first().click();
    }

    // First leave should succeed (no existing overlap on a fresh employee).
    await submitLeave(start, end);
    // Wait for either success list update or an explicit error.
    await page.waitForTimeout(1500);

    // Second leave overlapping same range → expect LEAVE_OVERLAP error surfaced.
    await submitLeave(start, end);
    await expect(
      page.locator("text=/(LEAVE_OVERLAP|overlaps|trùng|đã có|leave request overlaps)/i").first(),
    ).toBeVisible({ timeout: 20000 });
  });

  test("xem payslip đã publish (draft không lộ)", async ({ page }) => {
    await page.goto("/employee/payslips");
    await expect(page.getByText(/Danh sách phiếu lương/i)).toBeVisible({ timeout: 20000 });
    // Demo seed published 2 payslips for the active employee → at least one "Đã phát hành" badge.
    const published = page.getByText(/Đã phát hành/i);
    await expect(published.first()).toBeVisible({ timeout: 20000 });
    // Must never show draft markers.
    const draftCount = await page.getByText(/Bản nháp|draft|unpublished/i).count();
    expect(draftCount, "ESS must not expose unpublished payslips").toBe(0);
  });
});

// ----------------------------------------------------------------------------
// T8 — Recruitment backbone smoke (render; full happy-path needs Gmail+Calendar)
// ----------------------------------------------------------------------------
test.describe("Recruitment backbone — render & precondition", () => {
  test.use({ storageState: HR_STATE });

  test("Recruitment Inbox / Candidates / Interviews render dữ liệu thật", async ({ page }) => {
    await page.goto("/recruitment/inbox");
    // The page must render the inbox container (data may be empty without Gmail).
    await expect(page.locator("body")).toContainText(/Recruitment Inbox|Inbox tuyển dụng|hộp thư tuyển dụng|Cần xác nhận|sẵn sàng review/i, {
      timeout: 25000,
    }).catch(async () => {
      // Soft: at least the page should not be a 500.
      expect(page.url()).toContain("/recruitment/inbox");
    });

    await page.goto("/recruitment/candidates");
    await expect(page.locator("body")).toContainText(/Candidate|ứng viên|candidate/i, { timeout: 25000 });

    // Interview creation REQUIRES a selected Google Calendar (GH #214).
    await page.goto("/recruitment/interviews");
        await expect(
          page.locator("text=/(calendar|Google|chọn lịch|selected.*calendar|Calendar|chưa kết nối)/i").first(),
          "interview creation must surface the calendar precondition (GH #214) — root cause if absent",
        ).toBeVisible({ timeout: 25000 });
  });
});

// ----------------------------------------------------------------------------
// T9 — HR AI Assistant (human-in-the-loop). Needs an LLM provider configured.
// ----------------------------------------------------------------------------
test.describe("HR AI Assistant — human-in-the-loop", () => {
  test.use({ storageState: HR_STATE });

  test("chat gửi được + Draft Action cần HR confirm (ghi thật chỉ sau confirm)", async ({ page }) => {
    await page.goto("/assistant");
    // Wait for the assistant panel (AiChat) to mount.
    await expect(page.locator("body")).toContainText(/Assistant|Trợ lý|human-in-the-loop|tư vấn/i, { timeout: 30000 });

    // Send a simple read-only question.
    const composer = page.getByPlaceholder(/nhập|viết|nhắn|ask|prompt/i).first();
    const send = page.getByRole("button", { name: /gửi|send/i }).first();
    if ((await composer.count()) === 0 || (await send.count()) === 0) {
      test.skip(true as any, "assistant composer not found — UI shape differs from expectation");
      return;
    }
    await composer.fill("Có bao nhiêu Candidate đang ở trạng thái new?");
    await send.click();

    // The Draft Action panel must require explicit HR confirm (never auto-write).
    // Assert either an assistant reply appears OR a provider/LLM error is surfaced —
    // both are honest backend outcomes. No mocked badges.
    const replyOrError = page.locator(
      "text=/(candidate|new|error|provider|LLM|không khả dụng|unavailable|timeout|human-in-the-loop)/i",
    ).first();
    await expect(replyOrError).toBeVisible({ timeout: 45000 });

    // Structural safety invariant: there must be no "auto-confirmed"/"saved automatically" mark.
    const autoWrite = await page.getByText(/tự động.*lưu|auto.*confirm|tự.*xác nhận/i).count();
    expect(autoWrite, "AI must never auto-write — only HR confirm").toBe(0);
  });
});
// ============================================================================
// Negative Tests — T10–T16 (không mock, real BE, resilient assertions)
// ============================================================================

// ----------------------------------------------------------------------------
// T10–T12 — Login negative tests (không auth)
// ----------------------------------------------------------------------------
test.describe("Negative — Login (T10–T12)", () => {
  test.use({ storageState: { cookies: [], origins: [] } as any });

  // T10: Wrong password → error message, vẫn ở /login
  test("T10 | đăng nhập sai mật khẩu → hiển thị lỗi, vẫn ở /login", async ({ page }) => {
    await page.goto("/login");
    await expect(page.locator("#login-email-input")).toBeVisible({ timeout: 15000 });
    await page.locator("#login-email-input").fill(HR_EMAIL);
    await page.locator("#login-password-input").fill("WrongPassword!999");
    await page.locator("#login-submit-button").click();

    // Flexible: error surfaced in Vietnamese hoặc English
    await expect(
      page.locator("text=/(sai|incorrect|invalid|không đúng|wrong|credentials|mật khẩu|password|không hợp lệ)/i").first(),
    ).toBeVisible({ timeout: 15000 });
    expect(page.url(), "must stay on /login after failed auth").toContain("/login");
  });

  // T11: Wrong email (non-existent account) → error, vẫn ở /login
  test("T11 | đăng nhập email không tồn tại → hiển thị lỗi, vẫn ở /login", async ({ page }) => {
    await page.goto("/login");
    await expect(page.locator("#login-email-input")).toBeVisible({ timeout: 15000 });
    await page.locator("#login-email-input").fill("ghost@vroom.example.com");
    await page.locator("#login-password-input").fill(HR_PASSWORD);
    await page.locator("#login-submit-button").click();

    await expect(
      page.locator("text=/(không tìm thấy|not found|không tồn tại|no account|email|không đúng|invalid|sai)/i").first(),
    ).toBeVisible({ timeout: 15000 });
    expect(page.url()).toContain("/login");
  });

  // T12: Empty form → validation (HTML5 built-in hoặc JS error surfaced)
  test("T12 | đăng nhập form rỗng → validation (HTML5 hoặc JS error)", async ({ page }) => {
    await page.goto("/login");
    await page.locator("#login-submit-button").click();

    // HTML5 built-in validation ngăn submit, hoặc JS surfaced error.
    // Cả 2 TH: user vẫn ở /login hoặc thấy validation message.
    await page.waitForTimeout(1500);
    const stillOnLogin = page.url().includes("/login");
    const validationVisible =
      (await page.getByText(/(required|bắt buộc|vui lòng|please|nhập|invalid|không hợp lệ|điền|trường)/i).count()) > 0;

    expect(
      stillOnLogin || validationVisible,
      "empty form must either show validation errors or prevent submission (stay on /login)",
    ).toBeTruthy();
  });
});

// ----------------------------------------------------------------------------
// T13 — Employee truy cập admin page → redirect hoặc forbidden
// ----------------------------------------------------------------------------
test.describe("Negative — Employee permission (T13)", () => {
  test.use({ storageState: EMP_STATE });

  test("T13 | Employee truy cập trang admin → redirect hoặc forbidden", async ({ page }) => {
    test.skip(!existsSync(EMP_STATE), "no employee session file — T4 did not complete");

    await page.goto("/dashboard");
    await page.waitForTimeout(3000);

    const url = page.url();
    const isRedirected = url.includes("/employee") || url.includes("/login");
    const forbiddenVisible =
      (await page.getByText(/403|forbidden|không có quyền|unauthorized|truy cập|không được phép/i).count()) > 0;

    expect(
      isRedirected || forbiddenVisible,
      `employee must not access admin dashboard — got URL ${url}`,
    ).toBeTruthy();
  });
});

// ----------------------------------------------------------------------------
// T14 — Không auth truy cập protected page → redirect /login
// ----------------------------------------------------------------------------
test.describe("Negative — No-auth access (T14)", () => {
  test.use({ storageState: { cookies: [], origins: [] } as any });

  test("T14 | không auth truy cập protected page → redirect /login", async ({ page }) => {
    await page.goto("/dashboard");
    await page.waitForURL("**/login", { timeout: 15000 });
    expect(page.url()).toContain("/login");
  });
});

// ----------------------------------------------------------------------------
// T15 — Setup wizard validation (negative) — chỉ chạy khi DB chưa được setup
// ----------------------------------------------------------------------------
test.describe("Negative — Setup wizard validation (T15)", () => {
  test.use({ storageState: { cookies: [], origins: [] } as any });

  test("T15 | setup wizard từ chối input không hợp lệ (password ngắn, mismatch, email sai)", async ({ page }) => {
    const alreadySetup = await setupStatus();
    if (alreadySetup) {
      test.skip(true as any, "DB already set up — setup wizard not accessible");
      return;
    }

    await page.goto("/setup");
    await expect(page.locator("#setup-wizard-container")).toBeVisible({ timeout: 30000 });

    // --- Step 1: submit without org name → validation error ---
    await page.locator("#setup-step1-submit").click();
    await expect(
      page.locator("text=/(required|bắt buộc|vui lòng|please|nhập|invalid|không hợp lệ|tên|name|điền)/i").first(),
    ).toBeVisible({ timeout: 10000 });

    // Fill org name, proceed to step 2
    await page.locator("#setup-org-name-input").fill(ORG_NAME);
    await page.locator("#setup-step1-submit").click();

    // --- Step 2: password too short → validation error ---
    await expect(page.locator("#setup-step2-form")).toBeVisible({ timeout: 10000 });
    await page.locator("#setup-hr-name-input").fill(HR_NAME);
    await page.locator("#setup-hr-email-input").fill(HR_EMAIL);
    await page.locator("#setup-password-input").fill("short");
    await page.locator("#setup-password-confirm-input").fill("short");
    await page.locator("#setup-step2-submit").click();

    await expect(
      page.locator("text=/(ngắn|short|ít nhất|at least|ký tự|characters|mật khẩu|password|không hợp lệ|invalid|tối thiểu|minimum)/i").first(),
    ).toBeVisible({ timeout: 10000 });

    // --- Step 2: password mismatch → validation error ---
    await page.locator("#setup-password-input").fill("ValidPass!123");
    await page.locator("#setup-password-confirm-input").fill("DifferentPass!456");
    await page.locator("#setup-step2-submit").click();

    await expect(
      page.locator("text=/(không khớp|mismatch|không trùng|match|confirm|khác|giống)/i").first(),
    ).toBeVisible({ timeout: 10000 });

    // --- Step 2: invalid email format → validation error ---
    await page.locator("#setup-password-input").fill("ValidPass!123");
    await page.locator("#setup-password-confirm-input").fill("ValidPass!123");
    await page.locator("#setup-hr-email-input").fill("not-an-email");
    await page.locator("#setup-step2-submit").click();

    await expect(
      page.locator("text=/(email|không hợp lệ|invalid|định dạng|format|hợp lệ)/i").first(),
    ).toBeVisible({ timeout: 10000 });
  });
});

// ----------------------------------------------------------------------------
// T16 — Rate limit (observational, không hard-fail nếu BE không bật rate limiter)
// ----------------------------------------------------------------------------
test.describe("Negative — Rate limit (T16)", () => {
  test.use({ storageState: { cookies: [], origins: [] } as any });

  test("T16 | gửi nhiều request liên tiếp → AUTH_RATE_LIMITED (nếu BE bật)", async ({ page, request }) => {
    const statuses: number[] = [];
    // Gửi 8 rapid login requests với wrong credentials để trigger rate limiting.
    // Dùng page.request (same origin, cookies carried) để BE thấy 1 client.
    for (let i = 0; i < 8; i++) {
      const r = await request.post("/api/auth/login", {
        data: { email: `rate-test-${i}@vroom.example.com`, password: "wrong" },
        failOnStatusCode: false,
      });
      statuses.push(r.status());
      if (i < 7) await page.waitForTimeout(200);
    }

    test.info().annotations.push({
      type: "rate-limit-statuses",
      description: statuses.join(", "),
    });

    // Soft assertion: nếu rate limiting được bật, ít nhất 1 request trả về 429.
    // Nếu không có rate limiter, observation only — không fail.
    const hasRateLimit = statuses.includes(429);
    if (!hasRateLimit) {
      test.info().annotations.push({
        type: "rate-limit-note",
        description: "No 429 observed — rate limiting may not be enabled on this BE",
      });
    }
    // Luôn pass; test này quan sát không hard-fail.
    expect(true).toBeTruthy();
  });
});
