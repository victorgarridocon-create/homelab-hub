<script>
  import { onMount } from "svelte";
  import { get, inventoryApi } from "../lib/api.js";
  import { statusMap, statusMeta, refreshStatus } from "../lib/status.js";
  import { daysUntil, itemHref } from "../lib/links.js";
  import { t, formatDate } from "../lib/i18n.js";
  import StatusDot from "../components/common/StatusDot.svelte";

  const TYPES = ["hardware", "vms", "apps", "storage", "networks", "misc"];
  const EXPIRY_FIELDS = [
    ["hardware", "warranty_until"],
    ["apps", "renewal_date"],
    ["misc", "renewal_date"],
  ];
  const EXPIRY_WINDOW_DAYS = 60;

  let inventory = null;
  let ipam = null;
  let loading = true;

  onMount(async () => {
    try {
      const [inv, ip] = await Promise.all([inventoryApi.get(""), get("/ipam")]);
      inventory = inv.data;
      ipam = ip.data;
    } catch {
      // Cards show their empty state
    }
    loading = false;
  });

  $: byKey = inventory
    ? Object.fromEntries(TYPES.flatMap((type) => (inventory[type] || []).map((item) => [`${type}-${item.id}`, { ...item, type }])))
    : {};

  $: down = Object.entries($statusMap)
    .filter(([, info]) => info.status === "down")
    .map(([key]) => byKey[key])
    .filter(Boolean);

  $: expirations = inventory
    ? EXPIRY_FIELDS.flatMap(([type, field]) =>
        (inventory[type] || [])
          .filter((item) => item[field])
          .map((item) => ({ ...item, type, field, date: item[field], days: daysUntil(item[field]) }))
      )
        .filter((e) => e.days !== null && e.days <= EXPIRY_WINDOW_DAYS)
        .sort((a, b) => a.days - b.days)
    : [];

  function relative(days) {
    if (days < 0) return $t("dashboard.expiredAgo", { days: -days });
    if (days === 0) return $t("dashboard.today");
    return $t("dashboard.inDays", { days });
  }
</script>

<div class="dashboard">
  <h2>{$t("dashboard.title")}</h2>

  {#if loading}
    <p aria-busy="true">{$t("common.loading")}</p>
  {:else}
    <section class="counts" aria-label={$t("dashboard.inventory")}>
      {#each TYPES as type}
        <a class="count-card" href="#/inventory/{type}">
          <span class="count">{inventory?.[type]?.length ?? 0}</span>
          <span class="label">{$t(`types.${type}`)}</span>
        </a>
      {/each}
    </section>

    <div class="cards">
      <article>
        <header class="card-header">
          <h3>{$t("dashboard.status")}</h3>
          <button class="outline secondary small" on:click={() => refreshStatus(true)} aria-busy={$statusMeta.loading}>
            {$t("status.refresh")}
          </button>
        </header>
        <p class="summary">
          <span class="up">{$t("dashboard.upCount", { count: $statusMeta.up })}</span>
          · <span class:down={$statusMeta.down > 0}>{$t("dashboard.downCount", { count: $statusMeta.down })}</span>
        </p>
        {#if $statusMeta.checking}
          <p class="muted" aria-busy="true">{$t("status.checking")}</p>
        {:else if $statusMeta.checkedAt}
          <p class="muted">{$t("status.lastCheck", { time: new Date($statusMeta.checkedAt).toLocaleTimeString() })}</p>
        {/if}
        {#if down.length}
          <ul class="item-list">
            {#each down as item}
              <li>
                <StatusDot key="{item.type}-{item.id}" />
                <a href={itemHref(item.type, item.id)}>{item.name}</a>
                <span class="muted">{$t(`typeSingular.${item.type}`)} · {item.ip_address || item.hostname}</span>
              </li>
            {/each}
          </ul>
        {:else if $statusMeta.up}
          <p>{$t("dashboard.allUp")}</p>
        {:else if $statusMeta.checking}
          <p class="muted">{$t("status.checkingHint")}</p>
        {:else}
          <p class="muted">{$t("dashboard.noMonitored")}</p>
        {/if}
      </article>

      <article>
        <header class="card-header">
          <h3>{$t("dashboard.expirations")}</h3>
        </header>
        <p class="muted">{$t("dashboard.expirationsHint", { days: EXPIRY_WINDOW_DAYS })}</p>
        {#if expirations.length}
          <ul class="item-list">
            {#each expirations as e}
              <li>
                <span class="badge" class:expired={e.days < 0} class:soon={e.days >= 0 && e.days <= 14}>{relative(e.days)}</span>
                <a href={itemHref(e.type, e.id)}>{e.name}</a>
                <span class="muted">{$t(`fields.${e.field}`)} · {formatDate(e.date)}</span>
              </li>
            {/each}
          </ul>
        {:else}
          <p>{$t("dashboard.noExpirations")}</p>
        {/if}
      </article>

      <article>
        <header class="card-header">
          <h3>{$t("nav.ipam")}</h3>
          <a href="#/ipam">{$t("dashboard.viewAll")} →</a>
        </header>
        {#if ipam}
          {#if ipam.duplicates.length}
            <p class="down">{$t("ipam.duplicatesCount", { count: ipam.duplicates.length })}</p>
          {:else}
            <p>{$t("ipam.noDuplicates")}</p>
          {/if}
          {#each ipam.networks as net}
            <div class="net">
              <span>{net.name} <span class="muted">{net.subnet}</span></span>
              <progress value={net.used_count} max={net.size} aria-label={$t("ipam.utilizationOf", { name: net.name })}></progress>
              <span class="muted">{$t("ipam.usedOf", { used: net.used_count, total: net.size })}</span>
            </div>
          {:else}
            <p class="muted">{$t("ipam.noNetworks")}</p>
          {/each}
        {/if}
      </article>
    </div>
  {/if}
</div>

<style>
  .dashboard h2 {
    margin-bottom: 1rem;
  }
  .counts {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
    gap: 0.75rem;
    margin-bottom: 1.5rem;
  }
  .count-card {
    display: flex;
    flex-direction: column;
    padding: 0.9rem 1rem;
    border-radius: 8px;
    border: 1px solid var(--pico-muted-border-color);
    background: var(--pico-card-background-color);
    text-decoration: none;
    color: inherit;
  }
  .count-card:hover {
    border-color: var(--pico-primary);
  }
  .count {
    font-size: 1.8rem;
    font-weight: 700;
    line-height: 1.1;
  }
  .label {
    color: var(--pico-muted-color);
    font-size: 0.85rem;
    hyphens: auto;
  }
  .cards {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 1rem;
    align-items: start;
  }
  article {
    margin: 0;
  }
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 0.5rem;
  }
  .card-header h3 {
    margin: 0;
    font-size: 1.1rem;
  }
  .summary {
    font-size: 1.05rem;
    margin-bottom: 0.25rem;
  }
  .up {
    color: var(--hub-success);
  }
  .down {
    color: var(--hub-danger);
  }
  .muted {
    color: var(--pico-muted-color);
    font-size: 0.85rem;
  }
  .item-list {
    list-style: none;
    padding: 0;
    margin: 0.5rem 0 0;
  }
  .item-list li {
    list-style: none;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    flex-wrap: wrap;
    padding: 0.35rem 0;
    border-bottom: 1px solid var(--pico-muted-border-color);
  }
  .badge {
    font-size: 0.75rem;
    padding: 0.05rem 0.5rem;
    border-radius: 999px;
    background: var(--hub-surface-2);
    white-space: nowrap;
  }
  .badge.soon {
    background: var(--hub-warning-bg);
    color: var(--hub-warning);
  }
  .badge.expired {
    background: var(--hub-danger-bg);
    color: var(--hub-danger);
  }
  .net {
    display: grid;
    grid-template-columns: 1fr;
    gap: 0.1rem;
    margin-top: 0.75rem;
  }
  .net progress {
    margin: 0;
  }
</style>
