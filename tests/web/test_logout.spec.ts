import { expect, test } from "@playwright/test";

import {
  createE2eCredentials,
  logoutFromCabinet,
  registerViaAuthPage,
} from "./e2e-auth";

test("user can logout from cabinet and gets redirected to auth", async ({ page }) => {
  const credentials = createE2eCredentials("e2e-logout");

  await registerViaAuthPage(page, {
    name: "E2E Logout User",
    email: credentials.email,
    password: credentials.password,
  });

  await logoutFromCabinet(page);
  await expect(page.getByRole("button", { name: "Регистрация" })).toBeVisible();
});
