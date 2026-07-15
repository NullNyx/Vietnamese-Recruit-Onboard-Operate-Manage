import { defineConfig, devices } from "@playwright/test";

const baseURL = process.env.E2E_BASE_URL ?? "http://localhost:3000";
const hrState = process.env.E2E_HR_STORAGE_STATE;
const employeeState = process.env.E2E_EMPLOYEE_STORAGE_STATE;

const isCI = !!process.env.CI;

export default defineConfig({
  testDir: "./e2e",

  /* Only 1 worker locally to avoid overwhelming the Next.js dev server.
     CI can use the default (CPU-count-based) worker pool. */
  workers: isCI ? undefined : 1,

  /* Run tests within a project serially; projects may still run in parallel
     up to the worker limit. Set --fully-parallel on CLI for full parallelism. */
  fullyParallel: false,

  /* Retry on CI to handle flakes; retry locally once to reduce flake noise. */
  retries: isCI ? 2 : 1,

  /* Global timeout per test (including hooks, retries have their own budget). */
  timeout: 60000,

  /* Reporter for output. */
  reporter: isCI ? "html" : "list",

  /* Expect assertion timeout. */
  expect: {
    timeout: 15000,
  },

  /* Auto-start the Next.js dev server when running tests.
     Reuse an already-running server if one exists on port 3000. */
  webServer: {
    command: "npm run dev",
    port: 3000,
    reuseExistingServer: true,
    timeout: 120_000,
  },

  use: {
    baseURL,
    /* Each project provides its own storageState via env vars. */
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
    video: "retain-on-failure",
  },

  projects: [
    {
      name: "hr-desktop",
      use: { ...devices["Desktop Chrome"], storageState: hrState },
      grep: /@hr/,
    },
    {
      name: "hr-mobile",
      use: {
        ...devices["iPhone 12"],
        browserName: "chromium",
        storageState: hrState,
      },
      grep: /@hr/,
    },
    {
      name: "employee-desktop",
      use: { ...devices["Desktop Chrome"], storageState: employeeState },
      grep: /@employee/,
    },
    {
      name: "employee-mobile",
      use: {
        ...devices["iPhone 12"],
        browserName: "chromium",
        storageState: employeeState,
      },
      grep: /@employee/,
    },
  ],
});
