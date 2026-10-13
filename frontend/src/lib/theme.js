import { writable } from "svelte/store";

// "auto" follows the OS; "light"/"dark" force a theme through Pico's data-theme attribute
export const THEMES = ["auto", "light", "dark"];
const STORAGE_KEY = "homelab-hub.theme";

function initial() {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (THEMES.includes(stored)) return stored;
  } catch {
    // ignore
  }
  return "auto";
}

export const theme = writable(initial());

theme.subscribe((value) => {
  try {
    localStorage.setItem(STORAGE_KEY, value);
  } catch {
    // ignore
  }
  if (typeof document === "undefined") return;
  if (value === "auto") document.documentElement.removeAttribute("data-theme");
  else document.documentElement.setAttribute("data-theme", value);
});
