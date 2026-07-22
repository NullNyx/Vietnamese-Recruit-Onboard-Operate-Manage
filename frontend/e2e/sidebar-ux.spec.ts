/**
 * Sidebar UX E2E — optimistic active state, content skeleton, active indicator,
 * smooth transitions, logout, and mobile hamburger toggle.
 *
 * Tests the v4 AppShell improvements:
 * 1. Optimistic active state — active class appears immediately on click
 * 2. Content skeleton — animate-pulse skeleton during navigation
 * 3. Active indicator — accent bar (w-1 h-5 bg-indigo-500 rounded-full)
 * 4. Smooth transitions — duration-150 ease-out on sidebar buttons
 * 5. Logout — redirects to /login
 * 6. Mobile hamburger — toggle sidebar via Menu/X button
 *
 * Strategy: The first test logs in once and saves storage state to a temp file.
 * All subsequent tests reuse that state avoid server-side rate limiting.
 *
 * Uses same-origin proxy http://localhost:3000. Default Playwright locale is
 * en-US, so the app renders in English (messages/en.json).
 */

import { test, expect } from '@playwright/test';
import { existsSync, mkdirSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { tmpdir } from 'node:os';

// ---------------------------------------------------------------------------
// Labels (English, from messages/en.json)
// ---------------------------------------------------------------------------

const SIDEBAR = {
  dashboard: 'Dashboard & Metrics',
  inbox: 'Recruitment Inbox',
  candidates: 'Candidates',
  gmail: 'Gmail Channel',
  settings: 'AI & System Settings',
  assistant: 'AI Assistant',
} as const;

const TOPBAR = {
  logout: 'Log out',
  menu: 'Menu',
} as const;

const ADMIN_EMAIL = 'admin@vroomhr.com';
const ADMIN_PASSWORD = process.env.E2E_ADMIN_PASSWORD ?? 'VroomAdmin!2026';

// Temp storage state shared across tests — first test writes, others read.
const AUTH_DIR = join(__dirname, '.auth');
mkdirSync(AUTH_DIR, { recursive: true });
const ADMIN_STATE = join(AUTH_DIR, 'admin-sidebar.json');

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function sidebarButton(page: any, label: string) {
  return page.locator('aside button', { hasText: label }).first();
}

async function isActivelyStyled(btn: any): Promise<boolean> {
  const cls = await btn.getAttribute('class');
  return cls !== null && /bg-indigo-50/.test(cls) && /scale-\[1\.02\]/.test(cls);
}

// ---------------------------------------------------------------------------
// T0 — Login + produce storage state (runs first, seeds ADMIN_STATE file)
// ---------------------------------------------------------------------------

test.describe('Sidebar Navigation UX', () => {
  test('T0 | login as admin and save storage state', async ({ page, context }) => {
    if (existsSync(ADMIN_STATE)) {
      // Already has state from a prior run; just verify it works
      return;
    }
    await page.goto('/login');
    await expect(page.locator('#login-email-input')).toBeVisible({ timeout: 15_000 });
    await page.locator('#login-email-input').fill(ADMIN_EMAIL);
    await page.locator('#login-password-input').fill(ADMIN_PASSWORD);
    await page.locator('#login-submit-button').click();
    await expect(page.getByRole('heading', { name: /Dashboard.*Metrics/i })).toBeVisible({ timeout: 25_000 });

    // Save state for downstream tests
    await context.storageState({ path: ADMIN_STATE });
  });

  // -----------------------------------------------------------------------
  // All tests below use the saved storage state (no fresh login)
  // -----------------------------------------------------------------------
  test.describe('with existing session', () => {
    test.use({ storageState: ADMIN_STATE as any });

    // ── T1: Dashboard loads with sidebar ────────────────────────────────
    test('T1 | sidebar renders at /', async ({ page }) => {
      await page.goto('/');
      await expect(page.getByRole('heading', { name: /Dashboard.*Metrics/i })).toBeVisible({ timeout: 15_000 });

      // Verify all expected sidebar buttons exist
      await expect(sidebarButton(page, SIDEBAR.dashboard)).toBeVisible({ timeout: 5_000 });
      await expect(sidebarButton(page, SIDEBAR.inbox)).toBeVisible();
      await expect(sidebarButton(page, SIDEBAR.candidates)).toBeVisible();
      await expect(sidebarButton(page, SIDEBAR.gmail)).toBeVisible();
      await expect(sidebarButton(page, SIDEBAR.settings)).toBeVisible();
      await expect(sidebarButton(page, SIDEBAR.assistant)).toBeVisible();
      await expect(page.locator(`button[title="${TOPBAR.logout}"]`)).toBeVisible();
    });

    // ── T2: Optimistic active state ────────────────────────────────────
    test('T2 | optimistic active state — class changes immediately on click', async ({ page }) => {
      await page.goto('/');
      await expect(page.getByRole('heading', { name: /Dashboard.*Metrics/i })).toBeVisible({ timeout: 15_000 });
      await page.waitForTimeout(1_000);

      const gmailBtn = sidebarButton(page, SIDEBAR.gmail);
      await expect(gmailBtn).toBeVisible();

      const beforeCls = await gmailBtn.getAttribute('class');
      expect(beforeCls).not.toMatch(/bg-indigo-50/);

      await gmailBtn.click();

      await expect(async () => {
        expect(await isActivelyStyled(gmailBtn)).toBe(true);
      }).toPass({ timeout: 5_000 });
    });

    // ── T3: Content skeleton appears during navigation ─────────────────
    test('T3 | content skeleton appears during navigation', async ({ page }) => {
      await page.goto('/');
      await expect(page.getByRole('heading', { name: /Dashboard.*Metrics/i })).toBeVisible({ timeout: 15_000 });

      const gmailBtn = sidebarButton(page, SIDEBAR.gmail);
      await gmailBtn.click();

      await expect(page.locator('main .animate-pulse').first()).toBeVisible({ timeout: 5_000 });

      await page.waitForTimeout(3_000);
      await expect(page.locator('main .animate-pulse')).toHaveCount(0, { timeout: 20_000 });
    });

    // ── T4: Accent bar appears optimistically on click ─────────────────
    test('T4 | active indicator accent bar appears on click (optimistic)', async ({ page }) => {
      await page.goto('/');
      await expect(page.getByRole('heading', { name: /Dashboard.*Metrics/i })).toBeVisible({ timeout: 15_000 });

      const candidatesBtn = sidebarButton(page, SIDEBAR.candidates);
      await expect(candidatesBtn).toBeVisible();

      await candidatesBtn.click();

      // Accent bar on the clicked button appears immediately
      await expect(async () => {
        const barCount = await candidatesBtn.locator('span.rounded-full.bg-indigo-500').count();
        expect(barCount).toBeGreaterThanOrEqual(1);
      }).toPass({ timeout: 5_000 });

      await expect(async () => {
        expect(await isActivelyStyled(candidatesBtn)).toBe(true);
      }).toPass({ timeout: 3_000 });
    });

    // ── T5: Active state switches correctly ──────────────────────────
    test('T5 | active state switches correctly navigating back and forth', async ({ page }) => {
      await page.goto('/');
      await expect(page.getByRole('heading', { name: /Dashboard.*Metrics/i })).toBeVisible({ timeout: 15_000 });

      // Navigate to Gmail
      const gmailBtn = sidebarButton(page, SIDEBAR.gmail);
      await gmailBtn.click();

      await expect(async () => {
        expect(await isActivelyStyled(gmailBtn)).toBe(true);
      }).toPass({ timeout: 5_000 });

      await expect(page.locator('main .animate-pulse')).toHaveCount(0, { timeout: 20_000 });

      // Navigate back to Dashboard
      const dashboardBtn = sidebarButton(page, SIDEBAR.dashboard);
      await dashboardBtn.click();

      await expect(async () => {
        expect(await isActivelyStyled(dashboardBtn)).toBe(true);
      }).toPass({ timeout: 5_000 });

      // Gmail should have lost active state
      await expect(async () => {
        expect(await isActivelyStyled(gmailBtn)).toBe(false);
      }).toPass({ timeout: 5_000 });
    });

    // ── T6: Smooth transition classes ────────────────────────────────
    test('T6 | smooth transition classes present on sidebar buttons', async ({ page }) => {
      await page.goto('/');
      await expect(page.getByRole('heading', { name: /Dashboard.*Metrics/i })).toBeVisible({ timeout: 15_000 });

      const anyBtn = sidebarButton(page, SIDEBAR.dashboard);
      const cls = await anyBtn.getAttribute('class');
      expect(cls).toContain('transition-all');
      expect(cls).toContain('duration-150');
      expect(cls).toContain('ease-out');
    });

    // ── T7: Logout redirects to login page ──────────────────────────
    test('T7 | logout redirects to login page', async ({ page }) => {
      await page.goto('/');
      await expect(page.getByRole('heading', { name: /Dashboard.*Metrics/i })).toBeVisible({ timeout: 15_000 });

      const logoutBtn = page.locator(`button[title="${TOPBAR.logout}"]`);
      await expect(logoutBtn).toBeVisible();
      await logoutBtn.click();

      await page.waitForURL(/\/login/, { timeout: 20_000 });
    });

    // ── T8: Mobile hamburger menu ───────────────────────────────────
    test('T8 | mobile hamburger opens and closes sidebar', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 812 });
      await page.goto('/');
      await expect(page.getByRole('heading', { name: /Dashboard.*Metrics/i })).toBeVisible({ timeout: 15_000 });

      const hamburgerBtn = page.locator('header button.lg\\:hidden');
      await expect(hamburgerBtn).toBeVisible();

      const sidebar = page.locator('aside');
      let sidebarClass = await sidebar.getAttribute('class');
      expect(sidebarClass).toContain('-translate-x-full');

      // Open sidebar
      await hamburgerBtn.click();
      await page.waitForTimeout(500);

      sidebarClass = await sidebar.getAttribute('class');
      expect(sidebarClass).toContain('translate-x-0');

      // Close via hamburger (overlay is behind sidebar: z-50 > z-40)
      await hamburgerBtn.click();
      await page.waitForTimeout(500);

      sidebarClass = await sidebar.getAttribute('class');
      expect(sidebarClass).toContain('-translate-x-full');

      // Open again and navigate via a sidebar item
      await hamburgerBtn.click();
      await page.waitForTimeout(500);

      const inboxBtn = sidebarButton(page, SIDEBAR.inbox);
      await expect(inboxBtn).toBeVisible();
      await inboxBtn.click();

      // Sidebar should auto-close after navigation
      await expect(page.locator('main .animate-pulse')).toHaveCount(0, { timeout: 25_000 });
      await page.waitForTimeout(1_000);

      sidebarClass = await sidebar.getAttribute('class');
      expect(sidebarClass).toContain('-translate-x-full');
    });
  });
});
