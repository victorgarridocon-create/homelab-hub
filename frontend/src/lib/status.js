import { writable } from "svelte/store";
import { get as apiGet } from "./api.js";

const POLL_MS = 60_000;
// While the server is running checks, ask again soon to show the new results
const CHECKING_POLL_MS = 3_000;

// { "<type>-<id>": { status: "up"|"down", latency_ms, method, target, checked_at } }
export const statusMap = writable({});
export const statusMeta = writable({ checkedAt: null, up: 0, down: 0, loading: false, checking: false });

let timer = null;
let followUp = null;

export async function refreshStatus(force = false) {
  statusMeta.update((m) => ({ ...m, loading: true }));
  try {
    const res = await apiGet(`/status${force ? "?refresh=1" : ""}`);
    statusMap.set(res.data || {});
    statusMeta.set({ checkedAt: res.checked_at, up: res.up, down: res.down, loading: false, checking: res.checking });
    clearTimeout(followUp);
    if (res.checking && timer) followUp = setTimeout(() => refreshStatus(), CHECKING_POLL_MS);
  } catch {
    statusMeta.update((m) => ({ ...m, loading: false }));
  }
}

export function startStatusPolling() {
  if (timer) return;
  refreshStatus();
  timer = setInterval(refreshStatus, POLL_MS);
}

export function stopStatusPolling() {
  clearInterval(timer);
  clearTimeout(followUp);
  timer = null;
}
