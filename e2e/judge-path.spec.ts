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

test("judge path lists the four stops with working links", async ({ page }) => {
  const errors = failOnPageErrors(page);
  await page.goto("/judge");
  await expect(page).toHaveTitle(/Judge path/);
  await expect(page.getByRole("heading", { level: 1, name: /Judge path/ })).toBeVisible();
  await expect(page.locator(".judge-steps > li")).toHaveCount(4);
  await expect(page.locator("#stop-1 a[href='/runs#program-h']")).toBeVisible();
  await expect(page.getByText("REFUSE · OUT_OF_TABLE")).toBeVisible();
  await expect(page.locator("footer [data-app-version]")).toHaveText(/^v\d+\.\d+\.\d+$/);
  for (const href of ["/runs#program-h", "/runs#measurement-h", "/runs#attempts-h", "/certificate/rec-db7x-20261031", "/certificate/rec-trieste-20261031", "/survey", "/deck"]) {
    await expect(page.locator(`main a[href='${href}']`).first()).toBeAttached();
    const res = await page.request.get(href.split("#")[0]);
    expect(res.ok()).toBeTruthy();
  }
  expect(errors).toEqual([]);
});
