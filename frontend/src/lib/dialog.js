import { writable } from "svelte/store";

// In-app replacements for window.alert/confirm/prompt: themed, translatable and accessible.
// Each returns a promise; DialogHost.svelte renders the current request.
export const dialog = writable(null);

function open(options) {
  return new Promise((resolve) => {
    dialog.set({ ...options, resolve });
  });
}

/** Resolves to true/false. Pass danger: true for destructive actions. */
export function confirmDialog(message, { title = "", confirmLabel = "", danger = false } = {}) {
  return open({ kind: "confirm", message, title, confirmLabel, danger });
}

/** Resolves to the entered text, or null when cancelled. */
export function promptDialog(message, { title = "", placeholder = "", value = "" } = {}) {
  return open({ kind: "prompt", message, title, placeholder, value });
}

/** Resolves once dismissed. */
export function alertDialog(message, { title = "" } = {}) {
  return open({ kind: "alert", message, title });
}

export function closeDialog(result) {
  dialog.update((current) => {
    current?.resolve(result);
    return null;
  });
}
