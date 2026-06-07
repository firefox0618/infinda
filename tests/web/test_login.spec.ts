import { test } from "@playwright/test";

import {
  createE2eCredentials,
  loginViaAuthPage,
  logoutFromCabinet,
  registerViaAuthPage,
} from "./e2e-auth";

test("user can login again after logout", async ({ page }) => {
  const credentials = createE2eCredentials("e2e-login");

  await registerViaAuthPage(page, {
    name: "E2E Login User",
    email: credentials.email,
    password: credentials.password,
  });

  await logoutFromCabinet(page);
  await loginViaAuthPage(page, credentials);
});
