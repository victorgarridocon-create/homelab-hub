/** Browser URL for an app: its external hostname when set, otherwise host/IP + port. */
export function appUrl(app) {
  if (!app) return null;
  const scheme = app.https ? "https" : "http";
  if (app.external_hostname) {
    const host = app.external_hostname.replace(/^https?:\/\//, "").replace(/\/+$/, "");
    return /^https?:\/\//.test(app.external_hostname) ? app.external_hostname : `${scheme}://${host}`;
  }
  const host = app.hostname || app.ip_address;
  if (!host) return null;
  const defaultPort = (app.https && app.port === 443) || (!app.https && app.port === 80);
  return `${scheme}://${host}${app.port && !defaultPort ? `:${app.port}` : ""}`;
}

/** Hash route for a search/IPAM result. */
export function itemHref(type, id, extra = {}) {
  if (type === "documents") return `#/docs/${id}`;
  if (type === "shares") return `#/inventory/storage/${extra.storage_id}`;
  return `#/inventory/${type}/${id}`;
}

export function parseTags(tags) {
  return (tags || "")
    .split(",")
    .map((tag) => tag.trim())
    .filter(Boolean);
}

/** Days until an ISO date (negative when past). */
export function daysUntil(isoDate) {
  if (!isoDate) return null;
  const target = new Date(`${isoDate}T00:00:00`);
  if (Number.isNaN(target.getTime())) return null;
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  return Math.round((target - today) / 86_400_000);
}

/** Image icons are data URLs (forms/detail) or /api/icons/... URLs (lists); anything else is emoji/text. */
export function isImageIcon(icon) {
  return typeof icon === "string" && (icon.startsWith("data:image/") || icon.startsWith("/api/icons/") || icon.startsWith("http"));
}
