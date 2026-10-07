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
    expect(page.getByTestId(TEST_IDS.volcanoesHeading)).toBeVisible(),
    expect(page.getByTestId(TEST_IDS.myProfileButton)).toBeVisible(),
  ]);
  const map = page.getByTestId(TEST_IDS.homeMap);
  await expect(map).toBeVisible();
  await expect(map.locator("canvas")).toBeVisible();
  const markers = map.getByTestId(TEST_IDS.homeMapMarker);
  if ((await markers.count()) === 0) {
    return;
  }
  const marker = markers.last();
  await expect(marker).toBeVisible();
  await marker.click();
  const popup = page.getByTestId(TEST_IDS.volcanoPopup);
  await expect(popup).toBeVisible();
  const deformation = popup.getByTestId(TEST_IDS.inferenceDeformationButton);
  const seismic = popup.getByTestId(TEST_IDS.inferenceSeismicButton);
  if ((await deformation.count()) > 0) {
    await deformation.click();
    await expect(page.getByTestId(TEST_IDS.inferenceDialog)).toBeVisible();
    await page.getByTestId(TEST_IDS.inferenceCloseButton).click();
  } else if ((await seismic.count()) > 0) {
    await seismic.click();
    await expect(page.getByTestId(TEST_IDS.inferenceDialog)).toBeVisible();
    await page.getByTestId(TEST_IDS.inferenceCloseButton).click();
  }
});

test("admin page renders completely", async ({ page }) => {
  await gotoAdmin(page);
  await Promise.all([
    expect(page.getByTestId(TEST_IDS.modelsHeading)).toBeVisible(),
    expect(page.getByTestId(TEST_IDS.ingestButton)).toBeVisible(),
    expect(page.getByTestId(TEST_IDS.refineButton)).toBeVisible(),
    expect(page.getByTestId(TEST_IDS.trainButton)).toBeVisible(),
    expect(page.getByTestId(TEST_IDS.batchButton)).toBeVisible(),
    expect(page.getByTestId(TEST_IDS.promoteButton)).toBeVisible(),
    expect(page.getByTestId(TEST_IDS.refreshButton)).toBeVisible(),
    expect(page.getByTestId(TEST_IDS.maxSamplesField)).toBeVisible(),
    expect(page.getByTestId(TEST_IDS.signalField)).toBeVisible(),
    expect(page.getByTestId(TEST_IDS.sourceField)).toBeVisible(),
    expect(page.getByTestId(TEST_IDS.stageField)).toBeVisible(),
    expect(page.getByTestId(TEST_IDS.loadAllModelsButton)).toBeVisible(),
  ]);
  const maxSamples = page.getByTestId(TEST_IDS.maxSamplesField);
  await maxSamples.fill("10");
  await expect(maxSamples).toHaveValue("10");
});

test("admin page back to dashboard link navigates to home", async ({
  page,
}) => {
  await gotoAdmin(page);
  await page.getByTestId(TEST_IDS.backToDashboardLink).click();
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
  await expect(page.getByTestId(TEST_IDS.volcanoesHeading)).toBeVisible();
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
