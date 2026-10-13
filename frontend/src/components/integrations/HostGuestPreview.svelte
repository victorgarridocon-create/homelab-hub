<script>
  import { createEventDispatcher } from "svelte";
  import { t } from "../../lib/i18n.js";

  // preview: { hosts: [...], guests: [...] } from a Proxmox or ESXi preview endpoint
  export let preview;
  export let selected = new Set();
  export let busy = false;

  const dispatch = createEventDispatcher();

  function toggle(key) {
    selected.has(key) ? selected.delete(key) : selected.add(key);
    selected = selected;
  }

  function toggleAll(items) {
    const all = items.every((i) => selected.has(i.key));
    items.forEach((i) => (all ? selected.delete(i.key) : selected.add(i.key)));
    selected = selected;
  }

  $: all = [...preview.hosts, ...preview.guests];
</script>

  <article>
    <h3>{$t("integrations.preview")}</h3>
    <p class="muted">{$t("integrations.previewHint")}</p>
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>
              <input type="checkbox" aria-label={$t("integrations.selectAll")}
                checked={all.every((i) => selected.has(i.key))}
                on:change={() => toggleAll(all)} />
            </th>
            <th>{$t("fields.name")}</th>
            <th>{$t("fields.type")}</th>
            <th>{$t("fields.ip_address")}</th>
            <th>{$t("fields.os")}</th>
            <th>{$t("fields.cpu_cores")}</th>
            <th>{$t("fields.ram_gb")}</th>
            <th>{$t("integrations.action")}</th>
          </tr>
        </thead>
        <tbody>
          {#each preview.hosts as host (host.key)}
            <tr class="host-row">
              <td><input type="checkbox" aria-label={host.name} checked={selected.has(host.key)}
                on:change={() => toggle(host.key)} /></td>
              <td><strong>{host.name}</strong></td>
              <td>{$t("integrations.node")}</td>
              <td>{host.ip_address || "—"}</td>
              <td>{host.os || ""}</td>
              <td>{host.cpu_cores ?? ""}</td>
              <td>{host.ram_gb ?? ""}</td>
              <td><span class="badge" class:update={host.match_id}>{$t(host.match_id ? "integrations.update" : "integrations.new")}</span></td>
            </tr>
            {#each preview.guests.filter((g) => g.node === host.name) as g (g.key)}
              <tr>
                <td><input type="checkbox" aria-label={g.name} checked={selected.has(g.key)}
                  on:change={() => toggle(g.key)} /></td>
                <td class="indent">{g.name} <span class="muted">#{g.vmid}</span></td>
                <td>{g.kind === "lxc" ? "LXC" : "VM"} <span class="muted">· {g.status}</span></td>
                <td>{g.ip_address || "—"}</td>
                <td>{g.os || ""}</td>
                <td>{g.cpu_cores ?? ""}</td>
                <td>{g.ram_gb ?? ""}</td>
                <td><span class="badge" class:update={g.match_id}>{$t(g.match_id ? "integrations.update" : "integrations.new")}</span></td>
              </tr>
            {/each}
          {/each}
        </tbody>
      </table>
    </div>
    <button on:click={() => dispatch("apply")} aria-busy={busy} disabled={busy || selected.size === 0}>
      {$t("integrations.importSelected", { count: selected.size })}
    </button>
  </article>

<style>
  article {
    margin: 0 0 1rem;
  }
  article > button {
    width: auto;
  }
  .muted {
    color: var(--pico-muted-color);
    font-size: 0.9rem;
  }
  .table-wrap {
    overflow-x: auto;
    margin-bottom: 1rem;
  }
  .host-row td {
    background: var(--hub-surface-2);
  }
  .indent {
    padding-left: 1.75rem;
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
</style>
