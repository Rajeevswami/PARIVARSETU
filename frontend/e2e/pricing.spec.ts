import { expect, test } from "@playwright/test";

test("pricing is a public page", async ({ page }) => {
  await page.goto("/pricing");
  await expect(page.getByRole("heading", { name: "Pricing" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Premium" })).toBeVisible();
});
