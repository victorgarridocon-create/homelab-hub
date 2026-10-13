<script>
  import { push } from "svelte-spa-router";
  import { inventoryApi } from "../lib/api.js";
  import { itemHref, isImageIcon as isImage } from "../lib/links.js";
  import { t } from "../lib/i18n.js";
  import { confirmLeave } from "../lib/unsaved.js";

  let query = "";
  let results = [];
  let open = false;
  let active = -1;
  let loading = false;
  let input;
  let timer;
  let requestId = 0;

  function onInput() {
    clearTimeout(timer);
    active = -1;
    if (!query.trim()) {
      results = [];
      open = false;
      return;
    }
    timer = setTimeout(search, 200);
  }

  async function search() {
    const id = ++requestId;
    loading = true;
    try {
      const res = await inventoryApi.get(`/search?q=${encodeURIComponent(query.trim())}`);
      if (id !== requestId) return; // a newer search is in flight
      results = res.data;
      open = true;
    } catch {
      results = [];
    }
    loading = false;
  }

  async function go(result) {
    open = false;
    input.blur();
    if (!(await confirmLeave())) return;
    push(itemHref(result._type, result.id, result).slice(1));
    query = "";
    results = [];
  }

  function onKeydown(e) {
    if (!open) return;
    if (e.key === "ArrowDown") {
      e.preventDefault();
      active = Math.min(active + 1, results.length - 1);
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      active = Math.max(active - 1, 0);
    } else if (e.key === "Enter" && results.length) {
      e.preventDefault();
      go(results[Math.max(active, 0)]);
    } else if (e.key === "Escape") {
      open = false;
    }
  }

  function onWindowKeydown(e) {
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
      e.preventDefault();
      input.focus();
      input.select();
    }
  }

</script>

<svelte:window on:keydown={onWindowKeydown} />

<div class="global-search">
  <input
    bind:this={input}
    bind:value={query}
    on:input={onInput}
    on:keydown={onKeydown}
    on:focus={() => (open = results.length > 0)}
    on:blur={() => setTimeout(() => (open = false), 150)}
    type="search"
    placeholder={$t("search.placeholder")}
    aria-label={$t("search.label")}
    role="combobox"
    aria-expanded={open}
    aria-controls="global-search-results"
    aria-autocomplete="list"
    aria-activedescendant={active >= 0 ? `search-result-${active}` : undefined}
    autocomplete="off"
  />
  <kbd aria-hidden="true">Ctrl K</kbd>
  {#if open}
    <ul class="results" id="global-search-results" role="listbox">
      {#if results.length === 0}
        <li class="empty">{loading ? $t("common.loading") : $t("search.noResults")}</li>
      {/if}
      {#each results as result, i}
        <li
          id="search-result-{i}"
          role="option"
          aria-selected={i === active}
          class:active={i === active}
          on:mousedown|preventDefault={() => go(result)}
          on:mouseenter={() => (active = i)}
        >
          <span class="icon" aria-hidden="true">
            {#if isImage(result.icon)}<img src={result.icon} alt="" />{:else}{result.icon || ""}{/if}
          </span>
          <span class="main">
            <span class="name">{result.name}</span>
            {#if result.match_field !== "name" && result.match_field !== "title"}
              <span class="match">{$t(`fields.${result.match_field}`)}: {result.match}</span>
            {/if}
          </span>
          <span class="type">{$t(`typeSingular.${result._type}`)}</span>
        </li>
      {/each}
    </ul>
  {/if}
</div>

<style>
  .global-search {
    position: relative;
    flex: 1;
    max-width: 480px;
    min-width: 180px;
  }
  input {
    margin: 0;
    padding: 0.4rem 4rem 0.4rem 2.25rem;
    height: auto;
    font-size: 0.9rem;
    --pico-form-element-spacing-vertical: 0.4rem;
  }
  kbd {
    position: absolute;
    right: 0.6rem;
    top: 50%;
    transform: translateY(-50%);
    font-size: 0.7rem;
    padding: 0.1rem 0.35rem;
    opacity: 0.6;
    pointer-events: none;
  }
  /* No physical keyboard on touch devices: hide the shortcut hint */
  @media (hover: none), (max-width: 600px) {
    kbd {
      display: none;
    }
    input {
      padding-right: 0.75rem;
    }
  }
  .results {
    position: absolute;
    top: calc(100% + 4px);
    left: 0;
    right: 0;
    z-index: 1000;
    list-style: none;
    margin: 0;
    padding: 0.25rem 0;
    max-height: 60vh;
    overflow-y: auto;
    background: var(--hub-surface);
    border: 1px solid var(--hub-border);
    border-radius: 6px;
    box-shadow: var(--hub-shadow);
  }
  li {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    padding: 0.45rem 0.75rem;
    margin: 0;
    cursor: pointer;
    color: var(--pico-color);
    list-style: none;
  }
  li.active {
    background: var(--hub-info-bg);
  }
  li.empty {
    cursor: default;
    color: var(--pico-muted-color);
  }
  .icon {
    width: 1.4rem;
    text-align: center;
    flex-shrink: 0;
  }
  .icon img {
    width: 1.2rem;
    height: 1.2rem;
    object-fit: contain;
  }
  .main {
    flex: 1;
    min-width: 0;
    display: flex;
    flex-direction: column;
  }
  .name {
    font-weight: 500;
  }
  .match {
    font-size: 0.75rem;
    color: var(--pico-muted-color);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .type {
    font-size: 0.7rem;
    color: var(--pico-muted-color);
    border: 1px solid var(--hub-border);
    border-radius: 999px;
    padding: 0 0.45rem;
    white-space: nowrap;
  }
</style>
