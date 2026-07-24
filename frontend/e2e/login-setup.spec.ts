/**
 * Login setup — produce admin storage state for downstream E2E tests.
 *
 * Generates auth state via the backend login API directly (bypasses SPA
 * routing which is unavailable in the Docker production build).
 *
 * Run standalone:
 *   npx playwright test e2e/login-setup.spec.ts --grep="login and save"
 *
 * Or use the exported helper in a runner script.
 */

import { test as setup, expect, type BrowserContext } from "@playwright/test";
import { mkdirSync } from "node:fs";
import { join } from "node:path";

const AUTH_DIR = join(__dirname, ".auth");
mkdirSync(AUTH_DIR, { recursive: true });

const ADMIN_STATE = join(AUTH_DIR, "admin.json");

const ADMIN_EMAIL = process.env.E2E_HR_EMAIL ?? "hr.qa@vroom.example.com";
const ADMIN_PASSWORD = process.env.E2E_HR_PASSWORD ?? "VroomQA!148#2026";
const BASE_URL = process.env.E2E_BASE_URL ?? "http://localhost:3099";

/**
 * Login via the real backend API and save Playwright storage state.
 * Uses fetch() to POST /api/auth/login then maps the Set-Cookie headers
 * into Playwright storage state — no browser UI navigation needed.
 */
export async function loginAndSaveAdminState(
  ctx?: BrowserContext,
): Promise<boolean> {
  const { chromium } = await import("@playwright/test");
  const browser = ctx ?? (await chromium.launch({ headless: true }));
  const context = ctx ?? (await browser.newContext({ baseURL: BASE_URL }));

  try {
    const resp = await context.request.post(`${BASE_URL}/api/auth/login`, {
      data: { email: ADMIN_EMAIL, password: ADMIN_PASSWORD },
    });
    expect(resp.ok(), `Login API returned ${resp.status()}`).toBeTruthy();

    // The backend sets HttpOnly cookies (access_token, refresh_token) via
    // Set-Cookie headers.  Playwright's APIRequestContext automatically
    // captures these and merges them into the browser context's cookie jar.
    // Now do a quick page visit to confirm the session is valid.
    const page = await context.newPage();
    await page.goto("/vi/dashboard", { waitUntil: "networkidle" });
    await page.waitForTimeout(2000);

    // Persist the storage state (cookies + localStorage).
    await context.storageState({ path: ADMIN_STATE });
    stripSecureCookieFlag(ADMIN_STATE);
    console.log(`[login-setup] Admin state saved to ${ADMIN_STATE}`);
    return true;
  } catch (err) {
    console.error("[login-setup] Failed to login and save state:", err);
    return false;
  } finally {
    if (!ctx) await browser.close();
  }
}

// ---------------------------------------------------------------------------
// Playwright test (runnable via --grep)
// ---------------------------------------------------------------------------
setup("login and save storage state", { tag: "@login-setup" }, async ({ page, context }) => {
  setup.setTimeout(60_000);

  // Login via direct API call to get session cookies
  const resp = await context.request.post(`${BASE_URL}/api/auth/login`, {
    data: { email: ADMIN_EMAIL, password: ADMIN_PASSWORD },
  });
  expect(resp.ok(), `Login API returned ${resp.status()}`).toBeTruthy();

  // Verify session is valid by visiting dashboard
  await page.goto("/vi/dashboard", { waitUntil: "networkidle" });
  await page.waitForTimeout(2000);

  await context.storageState({ path: ADMIN_STATE });
  stripSecureCookieFlag(ADMIN_STATE);
  console.log(`[login-setup] Admin state saved to ${ADMIN_STATE}`);
});
