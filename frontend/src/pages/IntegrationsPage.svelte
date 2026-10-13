<script>
  import { onMount } from "svelte";
  import { get, post } from "../lib/api.js";
  import { addToast } from "../lib/stores.js";
  import { t } from "../lib/i18n.js";
  import HostGuestPreview from "../components/integrations/HostGuestPreview.svelte";

  const STORAGE_KEY = "homelab-hub.integrations";

  let tab = "proxmox";

  // Non-secret connection settings are remembered in this browser; secrets and passwords never are.
  let pve = { url: "", token_id: "", token_secret: "", verify_ssl: false };
  let vmw = { host: "", username: "", password: "", verify_ssl: false };
  let dock = { connection: "socket", socket_path: "/var/run/docker.sock", url: "", parent_type: "hardware", parent_id: "" };

  let hardware = [];
  let vms = [];

  let pvePreview = null;
  let pveSelected = new Set();
  let esxiPreview = null;
  let esxiSelected = new Set();
  let dockPreview = null;
  let dockSelected = new Set();
  let busy = false;
  let result = null;

  onMount(async () => {
    try {
      const saved = JSON.parse(localStorage.getItem(STORAGE_KEY) || "{}");
      pve = { ...pve, ...saved.pve, token_secret: "" };
      vmw = { ...vmw, ...saved.vmw, password: "" };
      dock = { ...dock, ...saved.dock };
    } catch {
      // ignore
    }
    try {
      [hardware, vms] = (await Promise.all([get("/hardware"), get("/vms")])).map((r) => r.data);
    } catch {
      // Parent dropdown stays empty
    }
  });

  function remember() {
    try {
      const { token_secret, ...pveSafe } = pve;
      const { password, ...vmwSafe } = vmw;
      localStorage.setItem(STORAGE_KEY, JSON.stringify({ pve: pveSafe, vmw: vmwSafe, dock }));
    } catch {
      // ignore
    }
  }

  async function run(fn) {
    busy = true;
    result = null;
    try {
      await fn();
    } catch (e) {
      addToast(e.message, "error");
    }
    busy = false;
  }

  // ---- Proxmox
  const previewProxmox = () =>
    run(async () => {
      remember();
      pvePreview = (await post("/integrations/proxmox/preview", pve)).data;
      pveSelected = new Set([...pvePreview.hosts, ...pvePreview.guests].map((i) => i.key));
    });

  const applyProxmox = () =>
    run(async () => {
      const body = {
        hosts: pvePreview.hosts.filter((h) => pveSelected.has(h.key)),
        guests: pvePreview.guests.filter((g) => pveSelected.has(g.key)),
      };
      result = (await post("/integrations/proxmox/apply", body)).data;
      addToast($t("integrations.done", result), "success");
      pvePreview = null;
    });

  // ---- VMware ESXi / vCenter
  const previewEsxi = () =>
    run(async () => {
      remember();
      esxiPreview = (await post("/integrations/esxi/preview", vmw)).data;
      esxiSelected = new Set([...esxiPreview.hosts, ...esxiPreview.guests].map((i) => i.key));
    });

  const applyEsxi = () =>
    run(async () => {
      const body = {
        hosts: esxiPreview.hosts.filter((h) => esxiSelected.has(h.key)),
        guests: esxiPreview.guests.filter((g) => esxiSelected.has(g.key)),
      };
      result = (await post("/integrations/esxi/apply", body)).data;
      addToast($t("integrations.done", result), "success");
      esxiPreview = null;
    });

  // ---- Docker
  $: parentOptions = dock.parent_type === "vm" ? vms : hardware;

  const previewDocker = () =>
    run(async () => {
      remember();
      dockPreview = (await post("/integrations/docker/preview", dock)).data;
      dockSelected = new Set(dockPreview.containers.map((c) => c.key));
    });

  const applyDocker = () =>
    run(async () => {
      const body = { ...dock, containers: dockPreview.containers.filter((c) => dockSelected.has(c.key)) };
      result = (await post("/integrations/docker/apply", body)).data;
      addToast($t("integrations.done", result), "success");
      dockPreview = null;
    });

  function toggle(set, key) {
    set.has(key) ? set.delete(key) : set.add(key);
    return new Set(set);
  }

  function toggleAll(set, items) {
    const all = items.every((i) => set.has(i.key));
    items.forEach((i) => (all ? set.delete(i.key) : set.add(i.key)));
    return new Set(set);
  }
</script>

<div class="integrations">
  <h2>{$t("nav.integrations")}</h2>
  <p class="muted">{$t("integrations.intro")}</p>

  <div class="tabs" role="tablist">
    <button role="tab" aria-selected={tab === "proxmox"} class:active={tab === "proxmox"} on:click={() => (tab = "proxmox")}>Proxmox VE</button>
    <button role="tab" aria-selected={tab === "esxi"} class:active={tab === "esxi"} on:click={() => (tab = "esxi")}>VMware ESXi</button>
    <button role="tab" aria-selected={tab === "docker"} class:active={tab === "docker"} on:click={() => (tab = "docker")}>Docker</button>
  </div>

  {#if result}
    <article class="result" role="status">
      {$t("integrations.done", result)}
      {#if result.skipped.length}
        <ul>
          {#each result.skipped as s}
            <li>{s.name}: {s.reason}</li>
          {/each}
        </ul>
      {/if}
    </article>
  {/if}

  {#if tab === "proxmox"}
    <article>
      <form on:submit|preventDefault={previewProxmox}>
        <div class="grid">
          <label>
            {$t("integrations.pveUrl")}
            <input type="text" bind:value={pve.url} placeholder="https://192.168.1.10:8006" required />
          </label>
          <label>
            {$t("integrations.tokenId")}
            <input type="text" bind:value={pve.token_id} placeholder="root@pam!homelab-hub" required />
          </label>
          <label>
            {$t("integrations.tokenSecret")}
            <input type="password" bind:value={pve.token_secret} autocomplete="off" required />
          </label>
        </div>
        <label class="checkbox">
          <input type="checkbox" bind:checked={pve.verify_ssl} />
          {$t("integrations.verifySsl")}
        </label>
        <details>
          <summary>{$t("integrations.pveHowTo")}</summary>
          <ol class="muted">
            <li>{$t("integrations.pveStep1")}</li>
            <li>{$t("integrations.pveStep2")}</li>
            <li>{$t("integrations.pveStep3")}</li>
          </ol>
        </details>
        <button type="submit" aria-busy={busy} disabled={busy}>{$t("integrations.search")}</button>
      </form>
    </article>

    {#if pvePreview}
      <HostGuestPreview preview={pvePreview} bind:selected={pveSelected} {busy} on:apply={applyProxmox} />
    {/if}
  {:else if tab === "esxi"}
    <article>
      <form on:submit|preventDefault={previewEsxi}>
        <div class="grid">
          <label>
            {$t("integrations.esxiHost")}
            <input type="text" bind:value={vmw.host} placeholder="192.168.1.30" required />
          </label>
          <label>
            {$t("auth.username")}
            <input type="text" bind:value={vmw.username} placeholder="root" autocomplete="off" required />
          </label>
          <label>
            {$t("auth.password")}
            <input type="password" bind:value={vmw.password} autocomplete="off" required />
          </label>
        </div>
        <label class="checkbox">
          <input type="checkbox" bind:checked={vmw.verify_ssl} />
          {$t("integrations.verifySsl")}
        </label>
        <details>
          <summary>{$t("integrations.esxiHowTo")}</summary>
          <ol class="muted">
            <li>{$t("integrations.esxiStep1")}</li>
            <li>{$t("integrations.esxiStep2")}</li>
            <li>{$t("integrations.esxiStep3")}</li>
          </ol>
        </details>
        <button type="submit" aria-busy={busy} disabled={busy}>{$t("integrations.search")}</button>
      </form>
    </article>

    {#if esxiPreview}
      <HostGuestPreview preview={esxiPreview} bind:selected={esxiSelected} {busy} on:apply={applyEsxi} />
    {/if}
  {:else}
    <article>
      <form on:submit|preventDefault={previewDocker}>
        <fieldset>
          <legend>{$t("integrations.connection")}</legend>
          <label class="checkbox">
            <input type="radio" bind:group={dock.connection} value="socket" />
            {$t("integrations.socket")}
          </label>
          <label class="checkbox">
            <input type="radio" bind:group={dock.connection} value="tcp" />
            {$t("integrations.tcp")}
          </label>
        </fieldset>
        {#if dock.connection === "socket"}
          <label>
            {$t("integrations.socketPath")}
            <input type="text" bind:value={dock.socket_path} />
            <small>{$t("integrations.socketHint")}</small>
          </label>
        {:else}
          <label>
            {$t("integrations.dockerUrl")}
            <input type="text" bind:value={dock.url} placeholder="http://192.168.1.20:2375" required />
            <small>{$t("integrations.tcpHint")}</small>
          </label>
        {/if}
        <div class="grid">
          <label>
            {$t("integrations.runsOnType")}
            <select bind:value={dock.parent_type} on:change={() => (dock.parent_id = "")}>
              <option value="hardware">{$t("typeSingular.hardware")}</option>
              <option value="vm">{$t("typeSingular.vms")}</option>
            </select>
          </label>
          <label>
            {$t("integrations.runsOn")}
            <select bind:value={dock.parent_id} required>
              <option value="">{$t("common.select")}</option>
              {#each parentOptions as p}
                <option value={p.id}>{p.name}</option>
              {/each}
            </select>
          </label>
        </div>
        <button type="submit" aria-busy={busy} disabled={busy}>{$t("integrations.search")}</button>
      </form>
    </article>

    {#if dockPreview}
      <article>
        <h3>{$t("integrations.preview")}</h3>
        <p class="muted">{$t("integrations.previewHint")}</p>
        {#if dockPreview.containers.length === 0}
          <p>{$t("integrations.noContainers")}</p>
        {:else}
          <div class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>
                    <input type="checkbox" aria-label={$t("integrations.selectAll")}
                      checked={dockPreview.containers.every((c) => dockSelected.has(c.key))}
                      on:change={() => (dockSelected = toggleAll(dockSelected, dockPreview.containers))} />
                  </th>
                  <th>{$t("fields.name")}</th>
                  <th>{$t("integrations.image")}</th>
                  <th>{$t("fields.port")}</th>
                  <th>{$t("fields.status")}</th>
                  <th>{$t("integrations.project")}</th>
                  <th>{$t("integrations.action")}</th>
                </tr>
              </thead>
              <tbody>
                {#each dockPreview.containers as c (c.key)}
                  <tr>
                    <td><input type="checkbox" aria-label={c.name} checked={dockSelected.has(c.key)}
                      on:change={() => (dockSelected = toggle(dockSelected, c.key))} /></td>
                    <td>{c.name}</td>
                    <td class="muted">{c.description}</td>
                    <td>{c.port ?? "—"}{c.https ? " (https)" : ""}</td>
                    <td>{c.status}</td>
                    <td>{c.compose_project || ""}</td>
                    <td><span class="badge" class:update={c.match_id}>{$t(c.match_id ? "integrations.update" : "integrations.new")}</span></td>
                  </tr>
                {/each}
              </tbody>
            </table>
          </div>
          <button on:click={applyDocker} aria-busy={busy} disabled={busy || dockSelected.size === 0}>
            {$t("integrations.importSelected", { count: dockSelected.size })}
          </button>
        {/if}
      </article>
    {/if}
  {/if}
</div>

<style>
  .muted {
    color: var(--pico-muted-color);
    font-size: 0.9rem;
  }
  .tabs {
    display: flex;
    gap: 0.5rem;
    margin-bottom: 1rem;
  }
  .tabs button {
    width: auto;
    margin: 0;
    background: transparent;
    color: var(--pico-muted-color);
    border: 1px solid var(--pico-muted-border-color);
  }
  .tabs button.active {
    color: var(--pico-primary-inverse);
    background: var(--pico-primary-background);
    border-color: var(--pico-primary-background);
  }
  article {
    margin: 0 0 1rem;
  }
  .checkbox {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }
  button[type="submit"],
  article > button {
    width: auto;
  }
  .table-wrap {
    overflow-x: auto;
    margin-bottom: 1rem;
  }
  .badge {
    font-size: 0.75rem;
    padding: 0.05rem 0.5rem;
    border-radius: 999px;
    background: var(--hub-success-bg);
    color: var(--hub-success);
    white-space: nowrap;
  }
  .badge.update {
    background: var(--hub-info-bg);
    color: var(--hub-info);
  }
  .result {
    border-left: 4px solid var(--hub-success);
  }
</style>
