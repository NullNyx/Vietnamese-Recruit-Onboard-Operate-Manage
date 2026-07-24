import { test, expect } from "@playwright/test";

/**
 * Minimal CI smoke — verifies the stack is healthy without the full
 * smoke spec.  This runs first so we know whether the webServer +
 * backend + Next are all wired correctly.
 */
test.describe("CI health-check", () => {
  test("backend setup-status returns JSON via proxy", async ({ page }) => {
    const base = process.env.E2E_BASE_URL || "http://localhost:3000";
    const r = await page.request.get(`${base}/api/auth/setup-status`);
    expect(r.status()).toBe(200);
    const body = await r.json();
    expect(typeof body.setup_complete).toBe("boolean");
  });

  test("setup page loads and renders wizard container", async ({ page }) => {
    await page.goto("/setup", { waitUntil: "networkidle" });
    // The wizard container must appear (either immediately or after
    // the setup-status fetch resolves).
    await expect(page.locator("#setup-wizard-container")).toBeVisible({ timeout: 30000 });
  });
});
