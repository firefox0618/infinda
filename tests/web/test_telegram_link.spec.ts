import { expect, test } from "@playwright/test";

import { createE2eCredentials, registerViaAuthPage } from "./e2e-auth";

test("user can create telegram link token from profile modal", async ({ page }) => {
  const credentials = createE2eCredentials("e2e-telegram");

  await registerViaAuthPage(page, {
    name: "E2E Telegram User",
    email: credentials.email,
    password: credentials.password,
  });

  await page.getByTestId("cabinet-open-profile-button").click();
  await expect(page.getByRole("heading", { name: "Настройки профиля" })).toBeVisible();

  await page.getByTestId("telegram-create-link-button").click();

  await expect(page.getByText("Ссылка привязки готова.")).toBeVisible();
  await expect(page.getByRole("link", { name: "Открыть бота" })).toBeVisible();
  await expect(page.getByRole("link", { name: "Открыть бота" })).toHaveAttribute(
    "href",
    /https:\/\/t\.me\/.+\?start=link_/,
  );
});
