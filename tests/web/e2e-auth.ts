import { expect, type Page } from "@playwright/test";

export type E2eCredentials = {
  email: string;
  password: string;
};

export function createE2eCredentials(prefix: string): E2eCredentials {
  const uniqueId = Date.now();

  return {
    email: `${prefix}-${uniqueId}@example.com`,
    password: "strong-pass-123",
  };
}

export async function registerViaAuthPage(
  page: Page,
  options: {
    name: string;
    email: string;
    password: string;
  },
) {
  await page.goto("/auth", { waitUntil: "domcontentloaded" });
  await page.getByRole("button", { name: "Регистрация" }).click();
  await page.getByTestId("register-name-input").fill(options.name);
  await page.getByTestId("register-email-input").fill(options.email);
  await page.getByTestId("register-password-input").fill(options.password);
  await page.getByTestId("register-password-confirm-input").fill(options.password);
  await page.getByTestId("register-terms-checkbox").setChecked(true, { force: true });
  await page.getByTestId("register-submit-button").click();

  await page.waitForURL("**/cabinet", { timeout: 20_000 });
  await expect(page.getByRole("heading", { name: "Обзор" })).toBeVisible();
}

export async function logoutFromCabinet(page: Page) {
  await page.getByTestId("cabinet-logout-button").click();
  await page.waitForURL("**/auth", { timeout: 20_000 });
  await expect(page.getByRole("button", { name: "Вход" })).toBeVisible();
}

export async function loginViaAuthPage(
  page: Page,
  credentials: E2eCredentials,
) {
  await page.goto("/auth", { waitUntil: "domcontentloaded" });
  await page.getByTestId("login-email-input").fill(credentials.email);
  await page.getByTestId("login-password-input").fill(credentials.password);
  await page.getByTestId("login-submit-button").click();

  await page.waitForURL("**/cabinet", { timeout: 20_000 });
  await expect(page.getByRole("heading", { name: "Обзор" })).toBeVisible();
}
