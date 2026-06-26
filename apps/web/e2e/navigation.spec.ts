import { test, expect } from "@playwright/test";

test.describe("Core navigation", () => {
  test("should display the dashboard", async ({ page }) => {
    await page.goto("/");
    await expect(page.locator("body")).toBeVisible();
  });

  test("should display the search page", async ({ page }) => {
    await page.goto("/search");
    await expect(page).toHaveURL(/search/);
  });

  test("should bound search date range inputs", async ({ page }) => {
    await page.goto("/search");

    const fromInput = page.locator("#created-at-from");
    const toInput = page.locator("#created-at-to");

    await toInput.fill("2026-06-20");
    await expect(fromInput).toHaveAttribute("max", "2026-06-20");

    await fromInput.fill("2026-06-10");
    await expect(toInput).toHaveAttribute("min", "2026-06-10");
  });

  test("should display the people page", async ({ page }) => {
    await page.goto("/people");
    await expect(page).toHaveURL(/people/);
  });

  test("should display the library page", async ({ page }) => {
    await page.goto("/library");
    await expect(page).toHaveURL(/library/);
  });

  test("should display the upload page", async ({ page }) => {
    await page.goto("/upload");
    await expect(page).toHaveURL(/upload/);
  });

  test("should navigate to files page", async ({ page }) => {
    await page.goto("/files");
    await expect(page).toHaveURL(/files/);
  });
});
