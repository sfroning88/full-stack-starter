import { defineConfig, devices } from "@playwright/test";

const isCi = Boolean(process.env.CI);
const remoteBase = process.env.PLAYWRIGHT_BASE_URL?.trim();
const baseURL = remoteBase || "http://localhost:3000";
const useLocalWebServer = !remoteBase;
const vercelBypassSecret = process.env.VERCEL_AUTOMATION_BYPASS_SECRET;

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: true,
  retries: process.env.CI ? 1 : 0,
  workers: process.env.CI ? 2 : undefined,
  reporter: process.env.CI
    ? [["github"], ["json", { outputFile: "playwright-report/results.json" }]]
    : "list",
  globalSetup: "./e2e/global-setup.ts",
  timeout: 60_000,
  use: {
    baseURL,
    storageState: "e2e/.auth/user.json",
    trace: "on-first-retry",
    ...(vercelBypassSecret
      ? {
          extraHTTPHeaders: {
            "x-vercel-protection-bypass": vercelBypassSecret,
          },
        }
      : {}),
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
  ...(useLocalWebServer
    ? {
        webServer: {
          command: isCi ? "pnpm start" : "pnpm build && pnpm start",
          url: baseURL,
          timeout: isCi ? 120_000 : 180_000,
          reuseExistingServer: !isCi,
        },
      }
    : {}),
});
