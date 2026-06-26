import { test, expect } from "@playwright/test";

test.describe("Search filters", () => {
  test("prevents inverted created-at date ranges", async ({ page }) => {
    await page.goto("/search");

    const fromInput = page.getByLabel("From", { exact: true });
    const toInput = page.getByLabel("To", { exact: true });

    await toInput.fill("2026-06-20");
    await expect(fromInput).toHaveAttribute("max", "2026-06-20");

    await fromInput.fill("2026-06-10");
    await expect(toInput).toHaveAttribute("min", "2026-06-10");
  });
});
