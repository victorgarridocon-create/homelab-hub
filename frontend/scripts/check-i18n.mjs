// Verifies that every $t("key") used in src/ exists in all locales and that locales share the same keys.
import { readFileSync, readdirSync, statSync } from "node:fs";
import { join } from "node:path";

const SRC = new URL("../src/", import.meta.url).pathname;
const LOCALES = ["es", "en"];

// Keys built at runtime: $t(`types.${type}`) etc. Each prefix must contain these entries.
const DYNAMIC = {
  types: ["hardware", "vms", "apps", "storage", "networks", "misc", "shares", "documents"],
  typeSingular: ["hardware", "vms", "apps", "storage", "networks", "misc", "shares", "documents"],
  status: ["up", "down", "unknown"],
  "map.edges": ["hosts", "runs", "storage", "share"],
};

// Plural entries ({ one, other }) count as a single key
const PLURAL_FORMS = new Set(["zero", "one", "two", "few", "many", "other"]);
const isPlural = (v) => typeof v === "object" && "other" in v && Object.keys(v).every((k) => PLURAL_FORMS.has(k));
const isLeaf = (v) => typeof v !== "object" || isPlural(v);
const flatten = (obj, prefix = "") =>
  Object.entries(obj).flatMap(([k, v]) => (isLeaf(v) ? [`${prefix}${k}`] : flatten(v, `${prefix}${k}.`)));

const files = (dir) =>
  readdirSync(dir).flatMap((f) => {
    const p = join(dir, f);
    return statSync(p).isDirectory() ? files(p) : /\.(svelte|js)$/.test(f) ? [p] : [];
  });

const dicts = Object.fromEntries(
  LOCALES.map((l) => [l, new Set(flatten(JSON.parse(readFileSync(join(SRC, "locales", `${l}.json`), "utf8"))))])
);

const used = new Set();
for (const file of files(SRC)) {
  const text = readFileSync(file, "utf8");
  for (const m of text.matchAll(/\$t\(\s*["']([\w.]+)["']/g)) used.add(m[1]);
  for (const m of text.matchAll(/\$t\(\s*\w+\s*\?\s*["']([\w.]+)["']\s*:\s*["']([\w.]+)["']/g)) used.add(m[1]).add(m[2]);
}
for (const [prefix, keys] of Object.entries(DYNAMIC)) keys.forEach((k) => used.add(`${prefix}.${k}`));

let errors = 0;
for (const l of LOCALES) {
  for (const key of used) if (!dicts[l].has(key)) (errors++, console.error(`[${l}] missing: ${key}`));
  for (const other of LOCALES) {
    if (other === l) continue;
    for (const key of dicts[l]) if (!dicts[other].has(key)) (errors++, console.error(`[${other}] missing (present in ${l}): ${key}`));
  }
}
// Hardcoded UI text in Svelte templates (text nodes and user-facing attributes)
const ALLOWED_LITERALS = new Set([
  "Home Lab Hub", "Proxmox VE", "VMware ESXi", "Docker", "Ctrl K", "VLAN", "LXC", "VM", "IP", "Español", "English",
  "https", "(https)", "Markdown", "root",
]);
for (const file of files(SRC).filter((f) => f.endsWith(".svelte"))) {
  const markup = readFileSync(file, "utf8")
    .replace(/<script[\s\S]*?<\/script>/g, (m) => m.replace(/[^\n]/g, " "))
    .replace(/<style[\s\S]*?<\/style>/g, (m) => m.replace(/[^\n]/g, " "))
    .replace(/<!--[\s\S]*?-->/g, (m) => m.replace(/[^\n]/g, " "))
    .replace(/<svg[\s\S]*?<\/svg>/g, (m) => m.replace(/[^\n]/g, " "));
  // Blank out {expressions}, innermost first, so nested braces disappear too
  let stripped = markup;
  for (let prev = ""; prev !== stripped; ) {
    prev = stripped;
    stripped = stripped.replace(/\{[^{}]*\}/g, (m) => " ".repeat(m.length));
  }
  const found = [
    ...[...stripped.matchAll(/>([^<>]*[A-Za-zÀ-ÿ]{2,}[^<>]*)</g)].map((m) => m[1]),
    ...[...stripped.matchAll(/\b(?:title|placeholder|aria-label|alt)="([^"]*[A-Za-z]{2,}[^"]*)"/g)].map((m) => m[1]),
  ];
  for (const raw of found) {
    const text = raw.replace(/\s+/g, " ").trim().replace(/^[·:•→↗×+\-(]+\s*|\s*[·:•→↗×)]+$/g, "");
    // Technical examples (URLs, IPs, user@realm, "RAID-Z2, RAID 10...") are the same in every language
    const technical = /:\/\/|@|\d/.test(text) || /^[A-Z0-9][A-Za-z0-9-]*(, [A-Z0-9][A-Za-z0-9 -]*)+\.\.\.$/.test(text);
    if (!text || technical || ALLOWED_LITERALS.has(text)) continue;
    errors++;
    console.error(`hardcoded text in ${file.replace(SRC, "src/")}: "${text}"`);
  }
}

if (errors) process.exit(1);
console.log(`i18n OK: ${used.size} keys used, ${dicts.es.size} defined per locale`);
