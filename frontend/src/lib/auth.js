import { writable } from "svelte/store";

// { checked, authenticated, authEnabled, user }
export const session = writable({ checked: false, authenticated: false, authEnabled: true, user: null });

async function call(path, options = {}) {
  const res = await fetch(`/api/auth${path}`, {
    headers: { "Content-Type": "application/json" },
    credentials: "same-origin",
    ...options,
  });
  const body = await res.json().catch(() => ({}));
  if (!res.ok) {
    const err = new Error(body.error || res.statusText);
    err.status = res.status;
    throw err;
  }
  return body;
}

function apply(body) {
  session.set({
    checked: true,
    authenticated: body.authenticated,
    authEnabled: body.auth_enabled,
    user: body.user,
  });
}

export async function checkSession() {
  try {
    apply(await call("/me"));
  } catch {
    session.set({ checked: true, authenticated: false, authEnabled: true, user: null });
  }
}

export async function login(username, password) {
  apply(await call("/login", { method: "POST", body: JSON.stringify({ username, password }) }));
}

export async function logout() {
  apply(await call("/logout", { method: "POST" }));
}

/** Called by the API client when the server answers 401 (session expired). */
export function markLoggedOut() {
  session.update((s) => ({ ...s, authenticated: false }));
}
