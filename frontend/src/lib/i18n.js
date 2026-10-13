import { derived, get, writable } from "svelte/store";
import es from "../locales/es.json";
import en from "../locales/en.json";

const dictionaries = { es, en };
export const LOCALES = [
  { code: "es", label: "Español" },
  { code: "en", label: "English" },
];
const FALLBACK = "en";
const STORAGE_KEY = "homelab-hub.locale";

function initialLocale() {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored in dictionaries) return stored;
  } catch {
    // Storage unavailable (private mode): use the default
  }
  return "es";
}

export const locale = writable(initialLocale());

locale.subscribe((code) => {
  try {
    localStorage.setItem(STORAGE_KEY, code);
  } catch {
    // ignore
  }
  if (typeof document !== "undefined") document.documentElement.lang = code;
});

function lookup(dict, key) {
  return key.split(".").reduce((node, part) => (node == null ? undefined : node[part]), dict);
}

function translate(code, key, vars) {
  let text = lookup(dictionaries[code], key) ?? lookup(dictionaries[FALLBACK], key) ?? key;
  // Plural forms: { "one": "1 IP", "other": "{count} IPs" }
  if (text && typeof text === "object" && typeof text.other === "string" && Object.keys(text).every((k) => k === "one" || k === "other")) {
    text = vars?.count === 1 && "one" in text ? text.one : text.other;
  }
  if (vars && typeof text === "string") {
    text = text.replace(/\{(\w+)\}/g, (match, name) => (name in vars ? vars[name] : match));
  }
  return text;
}

/** Reactive translator: $t("common.save"), $t("inventory.copyOf", { name: "nas" }) */
export const t = derived(locale, ($locale) => (key, vars) => translate($locale, key, vars));

/** Non-reactive translation for plain JS modules. */
export function tr(key, vars) {
  return translate(get(locale), key, vars);
}

/** Localised date, e.g. "15 ene 2027". Accepts ISO strings. */
export function formatDate(value) {
  if (!value) return "";
  const date = new Date(value.length === 10 ? `${value}T00:00:00` : value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleDateString(get(locale), { year: "numeric", month: "short", day: "numeric" });
}
