<script>
  import StatusDot from "../common/StatusDot.svelte";
  import TagList from "../common/TagList.svelte";
  import { appUrl, itemHref } from "../../lib/links.js";
  import { t, formatDate } from "../../lib/i18n.js";

  // node: { type, entity_id, networkName, networkColor }
  export let node;
  export let details = null;
  export let loading = false;

  const MONITORED = ["hardware", "vms", "apps", "misc"];

  // [field, suffix] rendered in order when present
  const FIELDS = [
    ["hostname"], ["ip_address"], ["mac_address"], ["os"], ["cpu"], ["cpu_cores"], ["ram_gb", " GB"],
    ["disk_gb", " GB"], ["port"], ["external_hostname"], ["storage_type"], ["raid_type"],
    ["raw_space_tb", " TB"], ["usable_space_tb", " TB"], ["filesystem"], ["category"], ["description"],
    ["share_type"],
  ];
  const DATE_FIELDS = ["purchase_date", "warranty_until", "renewal_date"];

  $: link = node.type === "apps" ? appUrl(details) : null;
  $: ip = details?.ip_address || details?.ip;
  $: inventoryHref = node.type === "shares" && !details?.storage_id
    ? "#/inventory/storage"
    : itemHref(node.type, node.entity_id, details || {});
</script>

<div class="info-content">
  <div class="info-item">
    <span class="info-label">{$t("fields.type")}:</span>
    <span class="info-value">{$t(`typeSingular.${node.type}`)}</span>
  </div>
  {#if MONITORED.includes(node.type)}
    <div class="info-item">
      <span class="info-label">{$t("fields.status")}:</span>
      <span class="info-value"><StatusDot key="{node.type}-{node.entity_id}" showLabel /></span>
    </div>
  {/if}
  {#if loading}
    <div class="info-item">
      <span class="info-label">{$t("common.loading")}</span>
    </div>
  {:else if details}
    {#each FIELDS as [field, suffix]}
      {#if field === "ip_address" ? ip : details[field]}
        <div class="info-item">
          <span class="info-label">{$t(`fields.${field}`)}:</span>
          <span class="info-value">{field === "ip_address" ? ip : details[field]}{suffix || ""}</span>
        </div>
      {/if}
    {/each}
    {#if link}
      <div class="info-item">
        <span class="info-label">{$t("fields.link")}:</span>
        <span class="info-value">
          <a href={link} target="_blank" rel="noopener noreferrer">{link.replace(/^https?:\/\//, "")}</a>
        </span>
      </div>
    {/if}
    {#each DATE_FIELDS as field}
      {#if details[field]}
        <div class="info-item">
          <span class="info-label">{$t(`fields.${field}`)}:</span>
          <span class="info-value">{formatDate(details[field])}</span>
        </div>
      {/if}
    {/each}
    {#if details.tags}
      <div class="info-item">
        <span class="info-label">{$t("fields.tags")}:</span>
        <span class="info-value"><TagList tags={details.tags} /></span>
      </div>
    {/if}
  {/if}
  {#if node.networkName}
    <div class="info-item">
      <span class="info-label">{$t("fields.network")}:</span>
      <span class="info-value">
        <span class="network-indicator" style="background-color: {node.networkColor}"></span>
        {node.networkName}
      </span>
    </div>
  {/if}
  {#if details?.notes}
    <div class="info-item notes">
      <span class="info-label">{$t("fields.notes")}:</span>
      <span class="info-value">{details.notes}</span>
    </div>
  {/if}
</div>
<div class="info-footer">
  <a href={inventoryHref} class="view-link">{$t("map.viewInInventory")}</a>
  {#if link}
    <a href={link} target="_blank" rel="noopener noreferrer" class="view-link">{$t("common.open")} ↗</a>
  {/if}
</div>

<style>
  .info-content {
    padding: 1rem;
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    max-height: 60vh;
    overflow-y: auto;
  }
  .info-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 1rem;
    font-size: 0.9rem;
  }
  .info-item.notes {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.3rem;
  }
  .info-item.notes .info-value {
    font-size: 0.85rem;
    color: var(--hub-overlay-muted);
    font-style: italic;
  }
  .info-label {
    color: var(--hub-overlay-muted);
    font-weight: 500;
    white-space: nowrap;
  }
  .info-value {
    color: var(--hub-overlay-color);
    display: flex;
    align-items: center;
    gap: 0.5rem;
    text-align: right;
    word-break: break-word;
  }
  .network-indicator {
    width: 12px;
    height: 12px;
    border-radius: 2px;
    display: inline-block;
    border: 1px solid var(--hub-border);
  }
  .info-footer {
    padding: 0.75rem 1rem;
    border-top: 1px solid var(--hub-border);
    display: flex;
    justify-content: space-between;
  }
  .view-link {
    color: var(--pico-primary);
    text-decoration: none;
    font-size: 0.9rem;
    font-weight: 500;
    transition: color 0.2s;
  }
  .view-link:hover {
    color: var(--pico-primary-hover);
  }
</style>
