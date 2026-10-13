import { test, expect } from "@playwright/test";
import { login, unique, createViaApi } from "./helpers.js";

test("menu is a drawer on phones", async ({ page }) => {
  await login(page);
  const nav = page.getByRole("navigation", { name: "Navegación principal" });
  const menu = page.getByRole("button", { name: "Menú" });
  await expect(menu).toBeVisible();
  await expect(nav).not.toBeInViewport();

  await menu.click();
  await expect(nav).toBeInViewport();
  await nav.getByRole("link", { name: "Direcciones IP" }).click();
  await expect(page).toHaveURL(/#\/ipam$/);
  await expect(nav).not.toBeInViewport();
});

test("inventory rows become cards without horizontal scrolling", async ({ page }) => {
  await login(page);
  await createViaApi(page, "hardware", { name: unique("phone"), ip_address: "10.99.1.5", tags: "mobile" });
  await page.goto("/#/inventory/hardware");
  await expect(page.getByText("10.99.1.5").first()).toBeVisible();
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
  expect(overflow).toBeLessThanOrEqual(1);
});

test("map page fits the screen and filters open on demand", async ({ page }) => {
  await login(page, "/map");
  await expect(page.getByRole("heading", { name: "Mapa de dispositivos" })).toBeVisible();
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
  expect(overflow).toBeLessThanOrEqual(1);
  const filters = page.getByRole("button", { name: "Filtros" });
  await expect(page.getByText("Mostrar inventario")).toBeHidden();
  await filters.click();
  await expect(page.getByText("Mostrar inventario")).toBeVisible();
});
