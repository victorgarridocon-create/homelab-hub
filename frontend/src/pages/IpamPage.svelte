<script>
  import { onMount } from "svelte";
  import { get } from "../lib/api.js";
  import { addToast } from "../lib/stores.js";
  import { itemHref } from "../lib/links.js";
  import { t } from "../lib/i18n.js";

  let data = null;
  let loading = true;
  let showFree = {};

  async function load() {
    loading = true;
    try {
      data = (await get("/ipam")).data;
    } catch (e) {
      addToast(e.message, "error");
    }
    loading = false;
  }

  onMount(load);

  async function copy(ip) {
    try {
      await navigator.clipboard.writeText(ip);
      addToast($t("ipam.copied", { ip }), "success");
    } catch {
      // Clipboard not available (http): nothing to do
    }
  }

  function level(pct) {
    return pct >= 90 ? "high" : pct >= 70 ? "medium" : "low";
  }
</script>

<div class="ipam">
  <div class="page-header">
    <h2>{$t("nav.ipam")}</h2>
    <button class="outline secondary" on:click={load} aria-busy={loading}>{$t("status.refresh")}</button>
  </div>

  {#if loading && !data}
    <p aria-busy="true">{$t("common.loading")}</p>
  {:else if data}
    {#if data.duplicates.length}
      <article class="alert" role="alert">
        <h3>⚠ {$t("ipam.duplicatesCount", { count: data.duplicates.length })}</h3>
        <p class="muted">{$t("ipam.duplicatesHint")}</p>
        <ul>
          {#each data.duplicates as dup}
            <li>
              <code>{dup.ip}</code>:
              {#each dup.owners.filter((o) => o.host) as owner, i}
                {#if i > 0}, {/if}<a href={itemHref(owner.type, owner.id, owner)}>{owner.name}</a>
                <span class="muted">({$t(`typeSingular.${owner.type}`)})</span>
              {/each}
            </li>
          {/each}
        </ul>
      </article>
    {/if}

    {#if data.networks.length === 0}
      <p>{$t("ipam.noNetworks")} <a href="#/inventory/networks">{$t("ipam.addNetwork")}</a></p>
    {/if}

    {#each data.networks as net (net.id)}
      <article class="network">
        <header class="net-header">
          <div>
            <h3>
              <span class="swatch" style="background: {net.color || 'var(--hub-neutral)'}"></span>
              {net.name}
            </h3>
            <span class="muted">
              {net.subnet}
              {#if net.vlan_id} · VLAN {net.vlan_id}{/if}
              {#if net.gateway} · {$t("fields.gateway")} {net.gateway}{/if}
            </span>
          </div>
          <div class="stats">
            <strong>{net.utilization}%</strong>
            <span class="muted">{$t("ipam.usedOf", { used: net.used_count, total: net.size })}</span>
          </div>
        </header>
        <div class="bar level-{level(net.utilization)}" role="progressbar" aria-valuenow={net.utilization}
          aria-valuemin="0" aria-valuemax="100" aria-label={$t("ipam.utilizationOf", { name: net.name })}>
          <span style="width: {Math.min(100, net.utilization)}%"></span>
        </div>

        <p class="next-free">
          {#if net.next_free}
            {$t("ipam.nextFree")}: <code>{net.next_free}</code>
            <button class="outline secondary small" on:click={() => copy(net.next_free)}>{$t("ipam.copy")}</button>
            · {$t("ipam.freeCount", { count: net.free_count })}
          {:else}
            {$t("ipam.full")}
          {/if}
        </p>

        {#if net.addresses.length}
          <div class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>{$t("fields.ip_address")}</th>
                  <th>{$t("ipam.assignedTo")}</th>
                </tr>
              </thead>
              <tbody>
                {#each net.addresses as row}
                  <tr class:conflict={row.owners.filter((o) => o.host).length > 1}>
                    <td><code>{row.ip}</code></td>
                    <td>
                      {#if row.owners.length === 0}
                        <span class="muted">{$t("fields.gateway")}</span>
                      {/if}
                      {#each row.owners as owner, i}
                        {#if i > 0}, {/if}<a href={itemHref(owner.type, owner.id, owner)}>{owner.name}</a>
                        <span class="muted">({$t(`typeSingular.${owner.type}`)})</span>
                      {/each}
                      {#if row.ip === net.gateway && row.owners.length}
                        <span class="muted">· {$t("fields.gateway")}</span>
                      {/if}
                    </td>
                  </tr>
                {/each}
              </tbody>
            </table>
          </div>
        {/if}

        {#if net.free_sample.length}
          <details bind:open={showFree[net.id]}>
            <summary>{$t("ipam.showFree", { count: net.free_sample.length })}</summary>
            <div class="free-list">
              {#each net.free_sample as ip}
                <button class="free-ip" title={$t("ipam.copy")} on:click={() => copy(ip)}>{ip}</button>
              {/each}
            </div>
          </details>
        {/if}
      </article>
    {/each}

    {#if data.unassigned.length}
      <article>
        <h3>{$t("ipam.unassigned")}</h3>
        <p class="muted">{$t("ipam.unassignedHint")}</p>
        <ul>
          {#each data.unassigned as row}
            <li>
              <code>{row.ip}</code>:
              {#each row.owners as owner, i}
                {#if i > 0}, {/if}<a href={itemHref(owner.type, owner.id, owner)}>{owner.name}</a>
              {/each}
            </li>
          {/each}
        </ul>
      </article>
    {/if}

    {#if data.invalid.length || data.invalid_subnets.length}
      <article>
        <h3>{$t("ipam.invalid")}</h3>
        <ul>
          {#each data.invalid as row}
            <li><code>{row.value}</code> — <a href={itemHref(row.owner.type, row.owner.id, row.owner)}>{row.owner.name}</a></li>
          {/each}
          {#each data.invalid_subnets as net}
            <li><code>{net.subnet}</code> — <a href={itemHref("networks", net.id)}>{net.name}</a></li>
          {/each}
        </ul>
      </article>
    {/if}
  {/if}
</div>

<style>
  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
  }
  .page-header h2 {
    margin: 0;
  }
  .page-header button {
    width: auto;
    margin: 0;
  }
  article {
    margin: 0 0 1rem;
  }
  .alert {
    border-left: 4px solid var(--hub-danger);
  }
  .alert h3 {
    color: var(--hub-danger);
    font-size: 1.1rem;
  }
  .net-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 1rem;
    flex-wrap: wrap;
  }
  .net-header h3 {
    margin: 0;
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }
  .swatch {
    width: 14px;
    height: 14px;
    border-radius: 3px;
    display: inline-block;
  }
  .stats {
    text-align: right;
    display: flex;
    flex-direction: column;
  }
  .stats strong {
    font-size: 1.4rem;
  }
  .bar {
    height: 8px;
    border-radius: 4px;
    background: var(--hub-surface-2);
    overflow: hidden;
    margin: 0.75rem 0;
  }
  .bar span {
    display: block;
    height: 100%;
    background: var(--hub-success);
  }
  .bar.level-medium span {
    background: var(--hub-warning);
  }
  .bar.level-high span {
    background: var(--hub-danger);
  }
  .next-free {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    flex-wrap: wrap;
  }
  .table-wrap {
    overflow-x: auto;
  }
  tr.conflict td {
    background: var(--hub-danger-bg);
  }
  .muted {
    color: var(--pico-muted-color);
    font-size: 0.85rem;
  }
  .free-list {
    display: flex;
    flex-wrap: wrap;
    gap: 0.3rem;
    margin-top: 0.5rem;
  }
  .free-ip {
    all: unset;
    cursor: pointer;
    font-family: var(--pico-font-family-monospace);
    font-size: 0.8rem;
    padding: 0.1rem 0.4rem;
    border-radius: 4px;
    border: 1px solid var(--pico-muted-border-color);
  }
  .free-ip:hover,
  .free-ip:focus-visible {
    border-color: var(--pico-primary);
  }
</style>
