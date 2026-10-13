<script>
  import { push } from "svelte-spa-router";
  import { get, post, del } from "../../lib/api.js";
  import { addToast } from "../../lib/stores.js";
  import { confirmDialog } from "../../lib/dialog.js";
  import { refreshStatus } from "../../lib/status.js";
  import { t } from "../../lib/i18n.js";
  import { appUrl, parseTags, isImageIcon as isImage } from "../../lib/links.js";
  import Modal from "../Modal.svelte";
  import StatusDot from "../common/StatusDot.svelte";
  import TagList from "../common/TagList.svelte";
  import HardwareForm from "./HardwareForm.svelte";
  import VmForm from "./VmForm.svelte";
  import AppForm from "./AppForm.svelte";
  import StorageForm from "./StorageForm.svelte";
  import NetworkForm from "./NetworkForm.svelte";
  import MiscForm from "./MiscForm.svelte";

  export let type = "hardware";

  let items = [];
  let loading = true;
  let search = "";
  let showCreateModal = false;
  let newItem = {};
  let sortColumn = null;
  let sortDirection = "asc";

  const FORMS = {
    hardware: HardwareForm,
    vms: VmForm,
    apps: AppForm,
    storage: StorageForm,
    networks: NetworkForm,
    misc: MiscForm,
  };

  const COLUMNS = {
    hardware: ["name", "hostname", "ip_address", "os", "cpu", "ram_gb", "tags"],
    vms: ["name", "hostname", "ip_address", "os", "cpu_cores", "ram_gb", "tags"],
    apps: ["name", "hostname", "ip_address", "external_hostname", "port", "tags"],
    storage: ["name", "storage_type", "raid_type", "raw_space_tb", "usable_space_tb", "tags"],
    networks: ["name", "vlan_id", "subnet", "gateway", "tags"],
    misc: ["name", "category", "hostname", "ip_address", "tags"],
  };

  // Types with a reachability check (see backend/app/utils/monitor.py)
  const MONITORED = ["hardware", "vms", "apps", "misc"];

  // Narrow screens show rows as cards (see styles); the status dot then gets a text label
  let narrow = false;
  const narrowQuery = typeof window !== "undefined" ? window.matchMedia("(max-width: 700px)") : null;
  if (narrowQuery) {
    narrow = narrowQuery.matches;
    narrowQuery.addEventListener("change", (e) => (narrow = e.matches));
  }


  $: columns = COLUMNS[type] || ["name"];
  $: monitored = MONITORED.includes(type);
  $: FormComponent = FORMS[type];
  $: modalTitle = $t("inventory.addTitle", { type: $t(`typeSingular.${type}`) });

  async function loadItems() {
    loading = true;
    items = [];
    try {
      const res = await get(`/${type}`);
      items = res.data;
    } catch (e) {
      addToast(e.message, "error");
    }
    loading = false;
  }

  $: type, loadItems();
  $: type, (search = "");

  // "#tag" matches that tag exactly; anything else matches any field
  $: filtered = search.startsWith("#")
    ? items.filter((item) => parseTags(item.tags).some((tag) => tag.toLowerCase() === search.slice(1).toLowerCase()))
    : search
      ? items.filter((item) =>
          Object.entries(item).some(
            ([key, v]) => key !== "icon" && v && String(v).toLowerCase().includes(search.toLowerCase())
          )
        )
      : items;

  function sortBy(column) {
    if (sortColumn === column) {
      sortDirection = sortDirection === "asc" ? "desc" : "asc";
    } else {
      sortColumn = column;
      sortDirection = "asc";
    }
  }

  $: sorted = sortColumn
    ? [...filtered].sort((a, b) => {
        let aVal = a[sortColumn];
        let bVal = b[sortColumn];

        if (aVal == null) aVal = "";
        if (bVal == null) bVal = "";

        if (typeof aVal === "string") aVal = aVal.toLowerCase();
        if (typeof bVal === "string") bVal = bVal.toLowerCase();

        if (aVal < bVal) return sortDirection === "asc" ? -1 : 1;
        if (aVal > bVal) return sortDirection === "asc" ? 1 : -1;
        return 0;
      })
    : filtered;

  async function deleteItem(id) {
    let message = $t("inventory.confirmDelete");
    if (type === "hardware") {
      // Deleting a host also deletes its VMs: say so before it happens
      try {
        const { data } = await get(`/hardware/${id}`);
        const vms = data.vms?.length || 0;
        const linked = (data.apps?.length || 0) + (data.storage_pools?.length || 0);
        if (vms) message += "\n\n" + $t("inventory.deleteHardwareVms", { count: vms, names: data.vms.map((v) => v.name).join(", ") });
        if (linked) message += "\n\n" + $t("inventory.deleteHardwareLinked", { count: linked });
      } catch {
        // Fall back to the generic confirmation
      }
    }
    const ok = await confirmDialog(message, { confirmLabel: $t("common.delete"), danger: true });
    if (!ok) return;
    try {
      await del(`/${type}/${id}`);
      addToast($t("toast.deleted"), "success");
      loadItems();
    } catch (e) {
      addToast(e.message, "error");
    }
  }

  async function duplicateItem(item) {
    try {
      // Lists carry icon URLs, not the image itself: copy from the full record
      const duplicate = { ...(await get(`/${type}/${item.id}`)).data };
      delete duplicate.id;
      duplicate.name = $t("inventory.copyOf", { name: item.name });

      await post(`/${type}`, duplicate);
      addToast($t("toast.duplicated"), "success");
      loadItems();
    } catch (e) {
      addToast(e.message, "error");
    }
  }

  function handleAddClick() {
    newItem = {};
    showCreateModal = true;
  }

  function handleModalClose() {
    showCreateModal = false;
    newItem = {};
  }

  async function handleCreate() {
    try {
      await post(`/${type}`, newItem);
      addToast($t("toast.created"), "success");
      showCreateModal = false;
      newItem = {};
      loadItems();
      refreshStatus();
    } catch (e) {
      addToast(e.message, "error");
    }
  }
</script>

<div class="entity-list">
  <div class="list-header">
    <h2>{$t(`types.${type}`)}</h2>
    <div class="actions">
      <input type="search" placeholder={$t("inventory.filterPlaceholder")} aria-label={$t("common.filter")} bind:value={search} />
      <button on:click={handleAddClick}>+ {$t("common.add")}</button>
    </div>
  </div>

  {#if search.startsWith("#")}
    <p class="active-filter">
      {$t("tags.filtering", { tag: search.slice(1) })}
      <button class="outline secondary small" on:click={() => (search = "")}>{$t("common.clear")}</button>
    </p>
  {/if}

  {#if loading}
    <p aria-busy="true">{$t("common.loading")}</p>
  {:else if filtered.length === 0}
    <p>{$t("inventory.empty")}</p>
  {:else}
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            {#if monitored}
              <th class="status-col"><span class="visually-hidden">{$t("fields.status")}</span></th>
            {/if}
            {#each columns as col}
              <th aria-sort={sortColumn === col ? (sortDirection === "asc" ? "ascending" : "descending") : undefined}>
                <button type="button" class="sort-btn" on:click={() => sortBy(col)}>
                  {$t(`fields.${col}`)}
                  {#if sortColumn === col}
                    <span class="sort-indicator" aria-hidden="true">{sortDirection === "asc" ? "▲" : "▼"}</span>
                  {/if}
                </button>
              </th>
            {/each}
            <th><span class="visually-hidden">{$t("common.actions")}</span></th>
          </tr>
        </thead>
        <tbody>
          {#each sorted as item (item.id)}
            <tr on:click={() => push(`/inventory/${type}/${item.id}`)} class="clickable">
              {#if monitored}
                <td class="status-col" data-label={$t("fields.status")}><StatusDot key="{type}-{item.id}" showLabel={narrow} /></td>
              {/if}
              {#each columns as col}
                <td data-label={$t(`fields.${col}`)} class:name-cell={col === "name"} class:empty-cell={item[col] == null || item[col] === ""}>
                  {#if col === "name"}
                    <a class="name-link" href="#/inventory/{type}/{item.id}" on:click|stopPropagation>
                      {#if item.icon}
                        <span class="row-icon" aria-hidden="true">
                          {#if isImage(item.icon)}<img src={item.icon} alt="" />{:else}{item.icon}{/if}
                        </span>
                      {/if}{item.name}
                    </a>
                  {:else if col === "tags"}
                    <TagList tags={item.tags} clickable on:select={(e) => (search = "#" + e.detail)} />
                  {:else}
                    {item[col] ?? ""}
                  {/if}
                </td>
              {/each}
              <td class="actions-cell">
                <div class="button-group">
                  {#if type === "apps" && appUrl(item)}
                    <a class="outline small" role="button" href={appUrl(item)} target="_blank" rel="noopener noreferrer"
                      on:click|stopPropagation>{$t("common.open")} ↗</a>
                  {/if}
                  <button class="outline secondary small icon-btn" title={$t("common.duplicate")} aria-label="{$t('common.duplicate')} {item.name}"
                    on:click|stopPropagation={() => duplicateItem(item)}>
                    <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
                    <span class="btn-text">{$t("common.duplicate")}</span>
                  </button>
                  <button class="outline danger small icon-btn" title={$t("common.delete")} aria-label="{$t('common.delete')} {item.name}"
                    on:click|stopPropagation={() => deleteItem(item.id)}>
                    <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/><path d="M10 11v6M14 11v6"/><path d="M9 6V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2"/></svg>
                    <span class="btn-text">{$t("common.delete")}</span>
                  </button>
                </div>
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  {/if}
</div>

<Modal
  isOpen={showCreateModal}
  title={modalTitle}
  maxWidth="700px"
  on:close={handleModalClose}
>
  <form on:submit|preventDefault={handleCreate}>
    <svelte:component this={FormComponent} bind:item={newItem} />

    <div class="form-actions">
      <button type="submit">{$t("common.create")}</button>
      <button type="button" class="secondary outline" on:click={handleModalClose}>{$t("common.cancel")}</button>
    </div>
  </form>
</Modal>

<style>
  .list-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 1rem;
    margin-bottom: 1rem;
  }
  .list-header h2 {
    margin: 0;
  }
  .actions {
    display: flex;
    gap: 0.5rem;
    align-items: center;
  }
  .actions input {
    margin: 0;
    max-width: 200px;
  }
  .actions button {
    margin: 0;
    white-space: nowrap;
  }
  .table-wrap {
    overflow-x: auto;
  }
  .sort-btn {
    all: unset;
    cursor: pointer;
    user-select: none;
    position: relative;
    display: block;
    width: 100%;
    padding-right: 1.1rem;
    font-weight: 600;
    white-space: normal;
    line-height: 1.25;
  }
  .sort-btn:focus-visible {
    outline: 2px solid var(--pico-primary);
  }
  .status-col {
    width: 1%;
  }
  .name-link {
    color: inherit;
    text-decoration: none;
    font-weight: 500;
  }
  .name-link:hover {
    text-decoration: underline;
  }
  .row-icon {
    margin-right: 0.35rem;
  }
  .row-icon img {
    width: 1.1rem;
    height: 1.1rem;
    object-fit: contain;
    vertical-align: text-bottom;
  }
  .active-filter {
    font-size: 0.85rem;
    color: var(--pico-muted-color);
  }
  .sort-indicator {
    position: absolute;
    right: 0;
    font-size: 0.7rem;
    opacity: 0.7;
  }
  tr.clickable {
    cursor: pointer;
  }
  tr.clickable:hover td {
    background: var(--hub-surface-hover);
  }
  .button-group {
    display: flex;
    gap: 0.4rem;
    justify-content: flex-end;
    align-items: center;
  }
  table {
    font-size: 0.92rem;
  }
  th,
  td {
    padding: 0.55rem 0.6rem;
  }
  .actions-cell {
    white-space: nowrap;
    width: 1%;
  }
  .icon-btn {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    padding: 0.35rem 0.45rem;
    line-height: 1;
  }
  /* Text labels only on the mobile cards, where there is room */
  .btn-text {
    display: none;
  }
  form {
    display: flex;
    flex-direction: column;
  }

  /* Cards instead of a table on narrow screens */
  @media (max-width: 700px) {
    .list-header {
      flex-direction: column;
      align-items: stretch;
    }
    .actions input {
      max-width: none;
      flex: 1;
    }
    table,
    thead,
    tbody,
    tr,
    td {
      display: block;
    }
    thead {
      position: absolute;
      width: 1px;
      height: 1px;
      overflow: hidden;
      clip: rect(0 0 0 0);
    }
    tr.clickable {
      border: 1px solid var(--hub-border);
      border-radius: 8px;
      margin-bottom: 0.75rem;
      padding: 0.5rem 0.75rem;
      background: var(--hub-surface);
    }
    td {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 1rem;
      padding: 0.3rem 0;
      border: none;
      background: transparent;
      text-align: right;
    }
    td::before {
      content: attr(data-label);
      color: var(--pico-muted-color);
      font-size: 0.8rem;
      text-align: left;
    }
    td.name-cell {
      font-size: 1.05rem;
    }
    td.name-cell::before,
    td.actions-cell::before {
      content: none;
    }
    td.empty-cell {
      display: none;
    }
    .status-col {
      width: auto;
    }
    .actions-cell .button-group {
      width: 100%;
      justify-content: stretch;
      padding-top: 0.4rem;
    }
    .actions-cell .button-group > * {
      flex: 1;
      justify-content: center;
      text-align: center;
    }
    .btn-text {
      display: inline;
    }
    .actions-cell {
      width: auto;
    }
  }
</style>
