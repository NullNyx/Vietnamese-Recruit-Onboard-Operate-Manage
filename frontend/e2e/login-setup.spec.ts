/**
 * Login setup — produce admin storage state for downstream E2E tests.
 *
 * Uses Playwright API (no browser UI) to authenticate against the real
 * FastAPI backend via the E2E reverse proxy and persist the session
 * cookies to ``.auth/admin.json``.
 *
 * Run standalone:
 *   npx playwright test --grep "login and save storage state"
 *
 * Or import ``setupLoginAndSaveState`` in a runner script.
 */

import { test as setup, expect } from "@playwright/test";
import { mkdirSync } from "node:fs";
import { join } from "node:path";

const AUTH_DIR = join(__dirname, ".auth");
mkdirSync(AUTH_DIR, { recursive: true });

const ADMIN_STATE = join(AUTH_DIR, "admin.json");

const ADMIN_EMAIL = process.env.E2E_HR_EMAIL ?? "hr.qa@vroom.example.com";
const ADMIN_PASSWORD = process.env.E2E_HR_PASSWORD ?? "VroomQA!148#2026";
const BASE_URL = process.env.E2E_BASE_URL ?? "http://localhost:3099";

/**
 * Login via the real backend API and save storage state.
 * Can be called from a runner script or Playwright setup project.
 */
export async function loginAndSaveAdminState(): Promise<boolean> {
  const { chromium } = await import("@playwright/test");
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ baseURL: BASE_URL });
  const page = await context.newPage();

  try {
    await page.goto("/login");
    await expect(page.locator("#login-email-input")).toBeVisible({ timeout: 15000 });
    await page.locator("#login-email-input").fill(ADMIN_EMAIL);
    await page.locator("#login-password-input").fill(ADMIN_PASSWORD);
    await page.locator("#login-submit-button").click();

    // Wait for redirect to dashboard
    await page.waitForURL("**/dashboard", { timeout: 30000 });
    await expect(
      page.getByRole("heading", { name: /T\u1ed5ng quan.*Metrics|Dashboard.*Metrics/i }),
    ).toBeVisible({ timeout: 20000 });

    await context.storageState({ path: ADMIN_STATE });
    console.log(`[login-setup] Admin state saved to ${ADMIN_STATE}`);
    return true;
  } catch (err) {
    console.error("[login-setup] Failed to login and save state:", err);
    return false;
  } finally {
    await browser.close();
  }
}

// ---------------------------------------------------------------------------
// Playwright test (runnable via --grep)
// ---------------------------------------------------------------------------
setup("login and save storage state", { tag: "@login-setup" }, async ({ page, context }) => {
  setup.setTimeout(60_000);

  await page.goto("/login");
  await expect(page.locator("#login-email-input")).toBeVisible({ timeout: 15000 });
  await page.locator("#login-email-input").fill(ADMIN_EMAIL);
  await page.locator("#login-password-input").fill(ADMIN_PASSWORD);
  await page.locator("#login-submit-button").click();

  await page.waitForURL("**/dashboard", { timeout: 30000 });
  await expect(
    page.getByRole("heading", { name: /T\u1ed5ng quan.*Metrics|Dashboard.*Metrics/i }),
  ).toBeVisible({ timeout: 20000 });

  await context.storageState({ path: ADMIN_STATE });
  console.log(`[login-setup] Admin state saved to ${ADMIN_STATE}`);
});
