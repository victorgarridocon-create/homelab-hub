import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { login, unique, createViaApi, PASSWORD } from "./helpers.js";

test("login rejects a bad password and accepts the right one", async ({ page }) => {
  await page.goto("/");
  await page.getByLabel("Usuario").fill("admin");
  await page.getByLabel("Contraseña").fill("wrong");
  await page.getByRole("button", { name: "Entrar" }).click();
  await expect(page.getByRole("alert")).toContainText("incorrectos");

  await page.getByLabel("Contraseña").fill(PASSWORD);
  await page.getByRole("button", { name: "Entrar" }).click();
  await expect(page.getByRole("heading", { name: "Resumen" })).toBeVisible();
});

test("create hardware, filter by tag and find it with the global search", async ({ page }) => {
  const name = unique("nas");
  await login(page, "/inventory/hardware");
  await page.getByRole("button", { name: "+ Agregar" }).click();

  const dialog = page.getByRole("dialog");
  await dialog.getByLabel("Nombre *").fill(name);
  await dialog.getByLabel("Dirección IP").fill("10.99.0.10");
  await dialog.getByLabel("Etiquetas").fill("rack-e2e, prod");
  await dialog.getByRole("button", { name: "Crear" }).click();

  await expect(page.getByText("Creado correctamente")).toBeVisible();
  const row = page.getByRole("row", { name: new RegExp(name) });
  await expect(row).toBeVisible();

  await row.getByRole("button", { name: "rack-e2e" }).click();
  await expect(page.getByText("Mostrando elementos con la etiqueta «rack-e2e»")).toBeVisible();

  const search = page.getByRole("combobox", { name: "Búsqueda global" });
  await search.fill("10.99.0.10");
  await page.getByRole("option", { name: new RegExp(name) }).click();
  await expect(page).toHaveURL(/#\/inventory\/hardware\/\d+/);
  await expect(page.getByLabel("Nombre *")).toHaveValue(name);
});

test("warns when an IP is already used by another host", async ({ page }) => {
  const other = unique("pve");
  await login(page);
  await createViaApi(page, "hardware", { name: other, ip_address: "10.99.0.77" });

  await page.goto("/#/inventory/hardware");
  await page.getByRole("button", { name: "+ Agregar" }).click();
  const dialog = page.getByRole("dialog");
  await dialog.getByLabel("Dirección IP").fill("10.99.0.77");
  await dialog.getByLabel("Dirección IP").blur();
  await expect(dialog.getByText(`Esta IP ya la usa: ${other}`)).toBeVisible();
});

test("asks before leaving a form with unsaved changes", async ({ page }) => {
  const hw = await (async () => {
    await login(page);
    return createViaApi(page, "hardware", { name: unique("edit") });
  })();
  await page.goto(`/#/inventory/hardware/${hw.id}`);
  await expect(page.getByLabel("Nombre *")).toHaveValue(hw.name);
  await page.waitForTimeout(400); // baseline snapshot is taken after the form settles
  await page.getByLabel("Ubicación").fill("Rack 3");

  await page.getByRole("navigation").getByRole("link", { name: "Mapa" }).click();
  const confirm = page.getByRole("dialog", { name: "Cambios sin guardar" });
  await expect(confirm).toBeVisible();
  await confirm.getByRole("button", { name: "Cancelar" }).click();
  await expect(page).toHaveURL(new RegExp(`/inventory/hardware/${hw.id}$`));
  await expect(page.getByLabel("Ubicación")).toHaveValue("Rack 3");

  await page.getByRole("button", { name: "Guardar" }).click();
  await expect(page.getByText("Actualizado correctamente")).toBeVisible();
  await page.getByRole("navigation").getByRole("link", { name: "Mapa" }).click();
  await expect(page).toHaveURL(/#\/map$/);
});

test("delete uses the in-app confirmation dialog", async ({ page }) => {
  await login(page);
  const hw = await createViaApi(page, "hardware", { name: unique("old") });
  await page.goto("/#/inventory/hardware");
  const row = page.getByRole("row", { name: new RegExp(hw.name) });
  await row.getByRole("button", { name: `Eliminar ${hw.name}` }).click();

  const dialog = page.getByRole("dialog");
  await expect(dialog).toContainText("¿Seguro que quieres eliminar este elemento?");
  await dialog.getByRole("button", { name: "Eliminar" }).click();
  await expect(row).toHaveCount(0);
});

test("documents render markdown and never run injected script", async ({ page }) => {
  await login(page);
  const res = await page.request.post("/api/docs", {
    data: {
      title: unique("doc"),
      content: "# Runbook\n\n- [x] backup\n\n<img src=x onerror=\"window.__xss=1\">\n\n[x](javascript:window.__xss=2)",
    },
  });
  const doc = (await res.json()).data;
  await page.goto(`/#/docs/${doc.id}`);
  const preview = page.locator(".editor-preview");
  await expect(preview.getByRole("heading", { name: "Runbook" })).toBeVisible();
  await expect(preview.getByRole("checkbox")).toBeChecked();
  await page.waitForTimeout(300);
  expect(await page.evaluate(() => window.__xss)).toBeUndefined();
  await expect(preview.locator("a")).not.toHaveAttribute("href", /javascript/);
});

test("theme and language choices persist", async ({ page }) => {
  await login(page);
  await page.getByLabel("Tema").selectOption("light");
  await expect(page.locator("html")).toHaveAttribute("data-theme", "light");
  await page.getByLabel("Tema").selectOption("dark");
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");

  await page.getByLabel("Idioma").selectOption("en");
  await expect(page.getByRole("navigation").getByRole("link", { name: "Home" })).toBeVisible();
  await page.reload();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
  await expect(page.getByRole("heading", { name: "Overview" })).toBeVisible();
  await page.getByLabel("Language").selectOption("es");
});

for (const [route, heading] of [
  ["/", "Resumen"],
  ["/inventory/hardware", "Equipos"],
  ["/ipam", "Direcciones IP"],
  ["/integrations", "Importar"],
  ["/docs", null],
  ["/map", "Mapa de dispositivos"],
]) {
  for (const theme of ["light", "dark"]) {
    test(`accessibility (axe) ${route} [${theme}]`, async ({ page }) => {
      await page.addInitScript((t) => localStorage.setItem("homelab-hub.theme", t), theme);
      await login(page, route);
      if (heading) await expect(page.getByRole("heading", { name: heading, level: 2 })).toBeVisible();
      await page.waitForLoadState("networkidle");
      const results = await new AxeBuilder({ page })
        .withTags(["wcag2a", "wcag2aa"])
        .exclude(".cy-container") // cytoscape canvas
        .analyze();
      const serious = results.violations.filter((v) => ["serious", "critical"].includes(v.impact));
      expect(serious.map((v) => `${v.id}: ${v.nodes.map((n) => n.target.join(" ")).slice(0, 3).join(" | ")}`)).toEqual([]);
    });
  }
}

test("deleting a host warns about its VMs and removes them", async ({ page }) => {
  await login(page);
  const hw = await createViaApi(page, "hardware", { name: unique("host") });
  const vm = await createViaApi(page, "vms", { name: unique("vm"), hardware_id: hw.id });
  await page.goto("/#/inventory/hardware");
  await page.getByRole("row", { name: new RegExp(hw.name) }).getByRole("button", { name: `Eliminar ${hw.name}` }).click();

  const dialog = page.getByRole("dialog");
  await expect(dialog).toContainText(`También se eliminará su máquina virtual: ${vm.name}`);
  await dialog.getByRole("button", { name: "Eliminar" }).click();
  await expect(page.getByText("Eliminado correctamente")).toBeVisible();
  const vms = await (await page.request.get("/api/vms")).json();
  expect(vms.data.some((v) => v.id === vm.id)).toBe(false);
});
