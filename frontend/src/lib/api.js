import { markLoggedOut } from "./auth.js";

const BASE = "/api";

async function request(path, options = {}, base = BASE) {
  const res = await fetch(`${base}${path}`, {
    credentials: "same-origin",
    ...options,
    headers: { "Content-Type": "application/json", ...options.headers },
  });
  if (res.status === 401) markLoggedOut();
  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: res.statusText }));
    throw new Error(err.error || res.statusText);
  }
  return res.json();
}

export function get(path) {
  return request(path);
}

export function post(path, data) {
  return request(path, { method: "POST", body: JSON.stringify(data) });
}

export function put(path, data) {
  return request(path, { method: "PUT", body: JSON.stringify(data) });
}

export function patch(path, data) {
  return request(path, { method: "PATCH", body: JSON.stringify(data) });
}

export function del(path) {
  return request(path, { method: "DELETE" });
}

// Export/import/search live under /inventory instead of /api
export const inventoryApi = {
  get: (path) => request(path, {}, "/inventory"),
  post: (path, data) => request(path, { method: "POST", body: JSON.stringify(data) }, "/inventory"),
};
