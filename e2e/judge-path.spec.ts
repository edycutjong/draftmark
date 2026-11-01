import { expect, test, type Page } from "@playwright/test";

function failOnPageErrors(page: Page): string[] {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  return errors;
}

test("landing loads and shows the current release", async ({ page }) => {
  const errors = failOnPageErrors(page);
  await page.goto("/");
  await expect(page).toHaveTitle(/DraftMark/);
  await expect(page.locator("footer [data-app-version]")).toHaveText(/^v\d+\.\d+\.\d+$/);
  expect(errors).toEqual([]);
});

test("pitch deck loads with the release stamp", async ({ page }) => {
  const errors = failOnPageErrors(page);
  await page.goto("/deck");
  await expect(page).toHaveTitle(/pitch deck/);
  await expect(page.locator("[data-app-version]").first()).toHaveText(/^v\d+\.\d+\.\d+$/);
  expect(errors).toEqual([]);
});

test("recorded runs page lists the real clips", async ({ page }) => {
  const errors = failOnPageErrors(page);
  await page.goto("/runs");
  await expect(page.getByText("dB7X").first()).toBeVisible();
  expect(errors).toEqual([]);
});

test("survey and evidence pages render", async ({ page }) => {
  const errors = failOnPageErrors(page);
  for (const path of ["/survey", "/evidence"]) {
    const res = await page.goto(path);
    expect(res?.status()).toBe(200);
    await expect(page.locator("main, body").first()).toBeVisible();
  }
  expect(errors).toEqual([]);
});

test("recorded run JSON is served", async ({ request }) => {
  const res = await request.get("/runs/rec-db7x-20261031.json");
  expect(res.ok()).toBeTruthy();
  const run = await res.json();
  expect(run.draft.frames.length).toBeGreaterThan(0);
});
