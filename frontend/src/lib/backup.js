import { inventoryApi } from "./api.js";
import { addToast } from "./stores.js";
import { confirmDialog } from "./dialog.js";
import { tr } from "./i18n.js";

export async function exportDatabase() {
  try {
    const data = await inventoryApi.get("/export");
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `homelab-export-${new Date().toISOString().slice(0, 10)}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  } catch (error) {
    addToast(tr("header.exportFailed", { error: error.message }), "error");
  }
}

/** Replaces the whole inventory with the JSON file, after confirmation. */
export async function importDatabase(file) {
  if (!file) return;
  let data;
  try {
    data = JSON.parse(await file.text());
  } catch {
    addToast(tr("header.importInvalid"), "error");
    return;
  }
  const ok = await confirmDialog(tr("header.importConfirm", { file: file.name }), {
    title: tr("header.import"),
    confirmLabel: tr("header.importReplace"),
    danger: true,
  });
  if (!ok) return;
  try {
    await inventoryApi.post("/import", data);
    addToast(tr("header.importDone"), "success");
    setTimeout(() => window.location.reload(), 800);
  } catch (error) {
    addToast(tr("header.importFailed", { error: error.message }), "error");
  }
}
