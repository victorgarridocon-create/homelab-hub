import { defineConfig, devices } from "@playwright/test";

const PORT = process.env.E2E_PORT || 5055;

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false, // one shared throwaway database
  workers: 1,
  retries: 0,
  reporter: [["list"]],
  use: {
    baseURL: `http://127.0.0.1:${PORT}`,
    locale: "es-ES",
    trace: "retain-on-failure",
  },
  projects: [
    { name: "desktop", use: { ...devices["Desktop Chrome"], viewport: { width: 1366, height: 860 } }, testIgnore: /mobile\.spec\.js/ },
    { name: "mobile", use: { ...devices["Pixel 7"] }, testMatch: /(mobile|screenshots)\.spec\.js/ },
  ],
  webServer: {
    // Builds the frontend, then serves it from the Flask backend
    command: "npm run build && sh e2e/start-server.sh",
    url: `http://127.0.0.1:${PORT}/api/health`,
    reuseExistingServer: false,
    timeout: 120_000,
  },
});
