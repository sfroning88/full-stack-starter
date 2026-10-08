import { test, expect, type Page } from "@playwright/test";
import { TEST_IDS } from "@/lib/test-ids";
import { routes } from "@lib/routes";

async function gotoHome(page: Page) {
  await page.goto(routes.base.root);
  await expect(page.getByTestId(TEST_IDS.homeScreen)).toBeVisible();
}

async function gotoAdmin(page: Page) {
  await page.goto(routes.admin.root);
  await expect(page.getByTestId(TEST_IDS.adminScreen)).toBeVisible();
}

test("home page renders completely", async ({ page }) => {
  await gotoHome(page);
  await Promise.all([
    expect(page.getByTestId(TEST_IDS.homeMessagesHeading)).toBeVisible(),
    expect(page.getByTestId(TEST_IDS.homeMessages)).toBeVisible(),
    expect(page.getByTestId(TEST_IDS.myProfileButton)).toBeVisible(),
    expect(page.getByTestId(TEST_IDS.homeMessageButton)).toBeVisible(),
  ]);
});

test("admin page renders completely", async ({ page }) => {
  await gotoAdmin(page);
  await Promise.all([
    expect(page.getByTestId(TEST_IDS.adminMessagesHeading)).toBeVisible(),
    expect(page.getByTestId(TEST_IDS.adminToolbar)).toBeVisible(),
    expect(page.getByTestId(TEST_IDS.adminMessageButton)).toBeVisible(),
    expect(page.getByTestId(TEST_IDS.adminMessages)).toBeVisible(),
  ]);
});

test("admin page back to frontend link navigates to home", async ({ page }) => {
  await gotoAdmin(page);
  await page.getByTestId(TEST_IDS.backTofrontendLink).click();
  await expect(page).toHaveURL((url) => url.pathname === routes.base.root);
});

test("home page open admin link navigates to admin", async ({ page }) => {
  await gotoHome(page);
  const adminLink = page.getByTestId(TEST_IDS.openAdminLink);
  const isAdmin = await adminLink.isVisible();
  if (!isAdmin) {
    test.skip(true, "Playwright user is not a platform admin");
  }
  await adminLink.click();
  await expect(page).toHaveURL((url) => url.pathname === routes.admin.root);
});

test("unauthenticated visit to home stays in browser", async ({ browser }) => {
  const context = await browser.newContext({ storageState: undefined });
  const page = await context.newPage();
  await page.goto(routes.base.root);
  await expect(page).toHaveURL((url) => url.pathname === routes.base.root);
  await expect(page.getByTestId(TEST_IDS.homeScreen)).toBeVisible();
  await expect(page.getByTestId(TEST_IDS.homeMessagesHeading)).toBeVisible();
  await expect(page.getByTestId(TEST_IDS.homeMessages)).toBeVisible();
  await expect(page.getByTestId(TEST_IDS.openAdminLink)).toHaveCount(0);
  await expect(page.getByTestId(TEST_IDS.myProfileButton)).toHaveCount(0);
  await expect(page.getByTestId(TEST_IDS.createProfileLink)).toBeVisible();
  await page.getByTestId(TEST_IDS.createProfileLink).click();
  await expect(page.getByTestId(TEST_IDS.signupDialog)).toBeVisible();
  await expect(
    page.getByRole("button", { name: /complete registration/i }),
  ).toBeVisible();
  await page.getByTestId(TEST_IDS.signupCloseButton).click();
  await page.getByTestId(TEST_IDS.signInButton).click();
  await expect(page.getByTestId(TEST_IDS.loginDialog)).toBeVisible();
  await expect(page).toHaveURL((url) => url.pathname === routes.base.root);
  await context.close();
});

test("unauthenticated visit to admin returns to login", async ({ browser }) => {
  const context = await browser.newContext({ storageState: undefined });
  const page = await context.newPage();
  await page.goto(routes.admin.root);
  await expect(page).toHaveURL((url) => url.pathname === routes.auth.login);
  await context.close();
});
