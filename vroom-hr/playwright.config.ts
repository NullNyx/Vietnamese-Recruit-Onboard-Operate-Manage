import { defineConfig, devices } from "@playwright/test";

/**
 * Vroom HR E2E config.
 *
 * The browser talks to a single same-origin host http://localhost:3000 — the
 * Node reverse proxy in `e2e/proxy.mjs` — so the backend's
 * `Secure; SameSite=Lax` HttpOnly auth cookie is carried and no cross-origin
 * CORS preflight is required (the FastAPI backend has no CORSMiddleware).
 *
 *   http://localhost:3000/api/* -> real FastAPI backend on :8000
 *   http://localhost:3000/*     -> `next dev` for vroom-hr on :3001
 *
 * `webServer.command` = e2e/start-servers.sh starts Next on :3001 then execs
 * the proxy on :3000 (Playwright supervises that single process).
 * Playwright 1.61 takes EITHER `port` OR `url` (not both); we use `port`.
 *
 * Storage state is produced from the REAL backend auth flow:
 *   - First-Run Setup UI wizard writes e2e/.auth/hr.json (real BE session)
 *   - HR provisions an Employee Account; the ESS login (+ change-password)
 *     flow writes e2e/.auth/employee.json
 * No hardcoded fake cookies.
 */

const isCI = !!process.env.CI;
const baseURL = process.env.E2E_BASE_URL ?? "http://localhost:3000";

export default defineConfig({
  testDir: "./e2e",
  // Single worker, NOT fully parallel — tests share on-disk state files
  // (e2e/.auth/{hr,employee}.json) produced earlier in the same run, so they
  // must execute in declaration order.
  workers: 1,
  fullyParallel: false,
  retries: 0,
  timeout: 90_000,
  expect: { timeout: 20_000 },
  reporter: [["list"], ["html", { open: "never" }]],

  use: {
    baseURL,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
    video: "retain-on-failure",
  },

  webServer: {
    command: process.env.E2E_START_COMMAND ?? "bash e2e/start-servers.sh",
    port: 3000,
    timeout: 150_000,
    reuseExistingServer: !isCI,
    env: {
      // Inlined into the Next client bundle: browser fetches same-origin
      // /api/* which the proxy forwards to the backend on :8000.
      NEXT_PUBLIC_API_URL: "http://localhost:3000",
      DISABLE_HMR: "true",
    },
  },

  projects: [
    {
      name: "vroom-hr-smoke",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
});