import { chromium, type FullConfig } from "@playwright/test";
import path from "path";
import fs from "fs";

const email = process.env.PLAYWRIGHT_EMAIL;
const password = process.env.PLAYWRIGHT_PASSWORD;

const AUTH_FILE = path.join(__dirname, ".auth/user.json");

async function globalSetup(_config: FullConfig) {
  fs.mkdirSync(path.dirname(AUTH_FILE), { recursive: true });

  if (!email || !password) {
    throw new Error("PLAYWRIGHT_EMAIL and PLAYWRIGHT_PASSWORD must be set");
  }

  const postLoginUrl = (pathname: string) => pathname === "/";

  let browser: Awaited<ReturnType<typeof chromium.launch>> | undefined;
  try {
    browser = await chromium.launch();
    const context = await browser.newContext({
      ...(process.env.VERCEL_AUTOMATION_BYPASS_SECRET
        ? {
            extraHTTPHeaders: {
              "x-vercel-protection-bypass":
                process.env.VERCEL_AUTOMATION_BYPASS_SECRET,
            },
          }
        : {}),
    });
    const page = await context.newPage();

    const baseURL = _config.projects[0]?.use?.baseURL;
    if (!baseURL || typeof baseURL !== "string") {
      throw new Error("Playwright baseURL must be set for global setup");
    }

    await page.goto(new URL("/auth/login", baseURL).toString(), {
      waitUntil: "domcontentloaded",
    });
    const emailInput = page.locator('[name="email"]');
    const passwordInput = page.locator('[name="password"]');
    await emailInput.waitFor({ state: "visible" });
    await emailInput.fill(email);
    await passwordInput.waitFor({ state: "visible" });
    await passwordInput.fill(password);
    const submit = page.getByTestId("login-submit");
    await submit.waitFor({ state: "visible" });
    await page.waitForFunction(() => {
      const button = document.querySelector('[data-testid="login-submit"]');
      return button instanceof HTMLButtonElement && !button.disabled;
    });
    await Promise.all([
      page.waitForURL((url) => postLoginUrl(url.pathname), {
        waitUntil: "domcontentloaded",
        timeout: 30_000,
      }),
      submit.click(),
    ]);

    const landed = new URL(page.url()).pathname;
    if (landed === "/auth/login") {
      throw new Error("Failed to sign in");
    }

    await page.context().storageState({ path: AUTH_FILE });
  } finally {
    await browser?.close();
  }
}

export default globalSetup;
