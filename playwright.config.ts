import { defineConfig, devices } from "@playwright/test";

// E2E against the production build (`next build` first). The Python functions are Vercel-only, so these specs
// cover the pages a judge opens without a judge code; the API is covered by pytest.
export default defineConfig({
  testDir: "./e2e",
  timeout: 30_000,
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? [["list"], ["html", { open: "never" }]] : "list",
  use: { baseURL: "http://127.0.0.1:3123", trace: "retain-on-failure" },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: { command: "npm run start -- -p 3123", url: "http://127.0.0.1:3123/runs", reuseExistingServer: !process.env.CI },
});
