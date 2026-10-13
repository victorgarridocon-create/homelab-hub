// Visual review helper, not a regression test: SCREENSHOTS_DIR=/some/dir npx playwright test screenshots
import { test } from "@playwright/test";
import { login, createViaApi } from "./helpers.js";

const DIR = process.env.SCREENSHOTS_DIR;
test.skip(!DIR, "set SCREENSHOTS_DIR to capture screenshots");

async function seed(page) {
  const net = await page.request.get("/api/networks");
  if ((await net.json()).count) return;
  await createViaApi(page, "networks", { name: "LAN", subnet: "192.168.1.0/24", gateway: "192.168.1.1", vlan_id: 10, color: "#3b82f6" });
  const pve = await createViaApi(page, "hardware", { name: "pve01", hostname: "pve01.lan", ip_address: "192.168.1.10", os: "Proxmox VE 8.2", cpu: "Ryzen 7 5700G", ram_gb: 64, tags: "proxmox, rack", warranty_until: "2026-10-20", icon: "🖥️" });
  await createViaApi(page, "hardware", { name: "nas", hostname: "nas.lan", ip_address: "192.168.1.20", os: "TrueNAS", ram_gb: 32, tags: "storage", icon: "💾" });
  const vm = await createViaApi(page, "vms", { name: "docker01", hardware_id: pve.id, ip_address: "192.168.1.50", os: "Ubuntu 24.04", cpu_cores: 4, ram_gb: 8, tags: "docker" });
  await createViaApi(page, "vms", { name: "ha", hardware_id: pve.id, ip_address: "192.168.1.20", os: "HAOS", cpu_cores: 2, ram_gb: 4 });
  await createViaApi(page, "apps", { name: "grafana", vm_id: vm.id, port: 3000, tags: "monitoring", icon: "📈" });
  await createViaApi(page, "misc", { name: "dominio homelab.dev", category: "Dominio", renewal_date: "2026-10-05" });
  await page.request.post("/api/docs", { data: { title: "Runbook", content: "# Runbook\n\n**Reiniciar** el NAS:\n\n- [x] Backup\n- [ ] Apagar VMs\n\n```\nzpool status\n```\n\n| Host | IP |\n|---|---|\n| pve01 | 192.168.1.10 |" } });
}

for (const theme of ["light", "dark"]) {
  test(`screens ${theme}`, async ({ page }, info) => {
    const tag = `${info.project.name}-${theme}`;
    await page.addInitScript((t) => localStorage.setItem("homelab-hub.theme", t), theme);
    await login(page);
    await seed(page);
    await page.request.get("/api/status?refresh=1");
    const shot = async (name) => {
      await page.waitForTimeout(500);
      await page.screenshot({ path: `${DIR}/${tag}-${name}.png`, fullPage: false });
    };
    await page.goto("/#/"); await shot("1-dashboard");
    await page.goto("/#/inventory/hardware"); await shot("2-hardware");
    await page.goto("/#/inventory/vms"); await shot("3-vms");
    await page.getByRole("button", { name: "+ Agregar" }).click(); await shot("4-modal");
    await page.keyboard.press("Escape");
    await page.goto("/#/ipam"); await shot("5-ipam");
    await page.goto("/#/docs"); await page.getByText("Runbook").first().click(); await shot("6-docs");
    await page.goto("/#/map"); await page.waitForTimeout(800); await shot("7-map");
    if (info.project.name === "mobile") {
      await page.goto("/#/inventory/hardware");
      await page.getByRole("button", { name: "Menú" }).click(); await shot("8-drawer");
      await page.keyboard.press("Escape");
    }
    await page.goto("/#/inventory/hardware");
    await page.getByRole("row", { name: /nas/ }).getByRole("button", { name: /^Eliminar/ }).click().catch(() => {});
    await shot("9-confirm");
  });
}
