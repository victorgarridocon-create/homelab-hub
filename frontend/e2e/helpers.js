import { expect } from "@playwright/test";

export const PASSWORD = "e2e-secret";

/** Log in through the API (shares cookies with the page) and open a route. */
export async function login(page, path = "/") {
  const res = await page.request.post("/api/auth/login", { data: { username: "admin", password: PASSWORD } });
  expect(res.ok()).toBeTruthy();
  await page.goto(`/#${path}`);
}

export const unique = (prefix) => `${prefix}-${Date.now().toString(36)}${Math.floor(Math.random() * 1000)}`;

export async function createViaApi(page, kind, data) {
  const res = await page.request.post(`/api/${kind}`, { data });
  expect(res.ok()).toBeTruthy();
  return (await res.json()).data;
}
