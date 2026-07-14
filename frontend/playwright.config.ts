import { defineConfig, devices } from "@playwright/test";

const baseURL = process.env.E2E_BASE_URL;
const hrState = process.env.E2E_HR_STORAGE_STATE;
const employeeState = process.env.E2E_EMPLOYEE_STORAGE_STATE;

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  reporter: process.env.CI ? "html" : "list",
  use: {
    baseURL,
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
        storageState: employeeState,
      },
      grep: /@employee/,
    },
  ],
});
