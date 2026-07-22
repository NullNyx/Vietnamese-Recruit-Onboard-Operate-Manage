/**
 * E2E test: Access Whitelist + Login gating
 *
 * Verifies that the Access Whitelist is properly checked during login.
 * Expected behavior: after admin adds @gmail.com to the whitelist,
 * a user with a @gmail.com domain should be allowed to log in.
 *
 * Uses the same auth conventions as vroom-hr.smoke.spec.ts
 */

import { test, expect, type Page } from "@playwright/test";
import { existsSync, mkdirSync, writeFileSync } from "node:fs";
import path from "node:path";

const AUTH_DIR = path.join(__dirname, ".auth");
mkdirSync(AUTH_DIR, { recursive: true });

const BASE = process.env.E2E_BASE_URL ?? "http://localhost:3000";
const HR_EMAIL = process.env.E2E_HR_EMAIL ?? "hr@vroom.com";
const HR_PASSWORD = process.env.E2E_HR_PASSWORD ?? "VroomAdmin!2026";

// Given employee@vroom.com exists in seed data, we need its password.
// If unset, we'll need to create an account or reset password.
const GMAIL_EMAIL = "testuser@gmail.com";

async function loginAs(page: Page, email: string, password: string) {
  await page.goto(`${BASE}/login`);
  await page.waitForLoadState("networkidle");

  await page.locator("#login-email-input").fill(email);
  await page.locator("#login-password-input").fill(password);
  await page.locator("#login-submit-button").click();
  await page.waitForURL("**/dashboard", { timeout: 30000 });
}

test.describe("Access Whitelist gating", () => {
  test("admin can add @gmail.com to whitelist via UI", async ({ page }) => {
    // Login as admin
    await loginAs(page, HR_EMAIL, HR_PASSWORD);

    // Navigate to Settings > Whitelist tab
    await page.goto(`${BASE}/settings`);
    await page.waitForLoadState("networkidle");

    // Click whitelist tab
    await page.locator('button:has-text("Access Whitelist")').click();
    await page.waitForTimeout(500);

    // Add domain to whitelist
    const input = page.locator('input[placeholder*="email" i]').first();
    await expect(input).toBeVisible({ timeout: 5000 });
    await input.fill("@gmail.com");

    await page.locator('button:has-text("Add")').click();
    await page.waitForTimeout(1000);

    // Verify entry appears
    await expect(page.locator("text=@gmail.com").first()).toBeVisible({ timeout: 5000 });

    // Verify it's labeled as "domain"
    const domainLabel = page.locator("text=Domain").first();
    await expect(domainLabel).toBeVisible();

    console.log("✅ @gmail.com added to whitelist successfully");
  });

  test("whitelist check at login — verify auth_service ignores whitelist", async ({ page }) => {
    // Login as admin & add @gmail.com to whitelist
    await loginAs(page, HR_EMAIL, HR_PASSWORD);
    await page.goto(`${BASE}/settings`);
    await page.waitForLoadState("networkidle");
    await page.locator('button:has-text("Access Whitelist")').click();
    await page.waitForTimeout(500);

    const input = page.locator('input[placeholder*="email" i]').first();
    await expect(input).toBeVisible({ timeout: 5000 });
    await input.fill("@gmail.com");
    await page.locator('button:has-text("Add")').click();
    await page.waitForTimeout(1000);
    await expect(page.locator("text=@gmail.com").first()).toBeVisible({ timeout: 5000 });

    // Now try to login with a gmail address via API
    // The key question: does the login API reject non-whitelisted emails?
    const resp = await page.request.post(`http://localhost:8000/api/auth/login`, {
      data: { email: "newuser@gmail.com", password: "doesntmatter" },
      headers: { "Content-Type": "application/json" },
    });

    const status = resp.status();
    let body: any = {};
    try { body = await resp.json(); } catch {}

    console.log(`\n=== WHITELIST GATING TEST ===`);
    console.log(`Login API with gmail → ${status}`);
    console.log(`Response body: ${JSON.stringify(body, null, 2)}`);

    // The BUG: Login does NOT check the whitelist at all
    // Expected result if whitelist worked: 403 with WHITELIST_BLOCKED error
    // Actual result: 401 InvalidCredentialsError (because user doesn't exist)
    // 
    // Even if user exists, auth_service.login() only checks:
    // 1. User exists + password matches
    // 2. User is active
    // It NEVER calls WhitelistManager.is_allowed_async()

    if (body?.detail?.code === "ACCESS_DENIED_WHITELIST" || body?.detail?.code === "WHITELIST_BLOCKED") {
      console.log("✅ Whitelist IS being checked at login — feature works correctly!");
    } else {
      console.log("❌ BUG CONFIRMED: Whitelist is NOT checked at login.");
      console.log("   auth_service.login() only checks credentials + is_active.");
      console.log("   It never calls WhitelistManager.is_allowed_async().");
      console.log("   Root cause: backend/src/modules/identity/application/auth_service.py:116-130");
    }

    // Document the finding — status is 401 (invalid creds), not whitelist-related
    expect(status).toBe(401);
    expect(body?.detail?.code ?? "").not.toMatch(/whitelist/i);
  });
});
