import { expect, test } from "@playwright/test";

import { createE2eCredentials, registerViaAuthPage } from "./e2e-auth";

test("user can register, open cabinet support and send a message", async ({ page }) => {
  const credentials = createE2eCredentials("e2e-user");
  const messageText = `E2E support message ${Date.now()}`;

  await registerViaAuthPage(page, {
    name: "E2E User",
    email: credentials.email,
    password: credentials.password,
  });

  await page.getByTestId("cabinet-tab-support").click();
  await expect(page.getByText("Поддержка онлайн")).toBeVisible();

  await page.getByTestId("support-message-input").fill(messageText);
  await page.getByTestId("support-send-button").click();

  await expect(page.getByText(messageText)).toBeVisible();
  await expect(page.getByText("Вы", { exact: true })).toBeVisible();
});
