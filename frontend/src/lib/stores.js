import { writable } from "svelte/store";

export const toasts = writable([]);

let toastId = 0;
export function addToast(message, type = "info") {
  const id = ++toastId;
  toasts.update((t) => [...t, { id, message, type }]);
  // Errors stay longer: they usually need to be read
  setTimeout(() => {
    toasts.update((t) => t.filter((toast) => toast.id !== id));
  }, type === "error" ? 8000 : 3000);
}

export function dismissToast(id) {
  toasts.update((t) => t.filter((toast) => toast.id !== id));
}
