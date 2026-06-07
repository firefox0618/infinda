import { expect, test } from "@playwright/test";

import { createE2eCredentials, registerViaAuthPage } from "./e2e-auth";

test("user can open renew modal and see subscription plans", async ({ page }) => {
  const credentials = createE2eCredentials("e2e-renew");

  await registerViaAuthPage(page, {
    name: "E2E Renew User",
    email: credentials.email,
    password: credentials.password,
  });

  await page.getByTestId("cabinet-open-renew-button").click();

  await expect(page.getByRole("heading", { name: "Продлить подписку" })).toBeVisible();
  await expect(page.getByText("1 месяц", { exact: true })).toBeVisible();
  await expect(page.getByText("3 месяца", { exact: true })).toBeVisible();
  await expect(page.getByText("6 месяцев", { exact: true })).toBeVisible();
  await expect(page.getByText("12 месяцев", { exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "Перейти к оплате" }).first()).toBeVisible();
});
