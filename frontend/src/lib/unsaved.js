import { push } from "svelte-spa-router";
import { confirmDialog } from "./dialog.js";
import { tr } from "./i18n.js";

// Tracks whether a form has unsaved edits and asks before leaving it.
let dirty = false;

function onBeforeUnload(event) {
  if (!dirty) return;
  event.preventDefault();
  event.returnValue = ""; // Required by some browsers to show the native prompt
}

// In-app links (#/...) are intercepted so the user can stay on the form
async function onLinkClick(event) {
  if (!dirty || event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey) return;
  const link = event.target.closest?.('a[href^="#/"]');
  if (!link || link.target === "_blank") return;
  event.preventDefault();
  if (await confirmLeave()) push(link.getAttribute("href").slice(1));
}

export function setDirty(value) {
  if (value === dirty) return;
  dirty = value;
  if (dirty) {
    window.addEventListener("beforeunload", onBeforeUnload);
    document.addEventListener("click", onLinkClick, true);
  } else {
    window.removeEventListener("beforeunload", onBeforeUnload);
    document.removeEventListener("click", onLinkClick, true);
  }
}

/** Resolves true when there is nothing to lose or the user agrees to discard changes. */
export async function confirmLeave() {
  if (!dirty) return true;
  const ok = await confirmDialog(tr("unsaved.message"), {
    title: tr("unsaved.title"),
    confirmLabel: tr("unsaved.discard"),
    danger: true,
  });
  if (ok) setDirty(false);
  return ok;
}
