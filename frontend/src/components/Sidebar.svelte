<script>
  import { createEventDispatcher } from "svelte";
  import { location } from "svelte-spa-router";
  import { t, locale, LOCALES } from "../lib/i18n.js";
  import { theme, THEMES } from "../lib/theme.js";
  import { session, logout } from "../lib/auth.js";
  import { exportDatabase, importDatabase } from "../lib/backup.js";

  // On narrow screens the sidebar is an off-canvas drawer controlled by the layout
  export let open = false;

  const dispatch = createEventDispatcher();
  const inventoryTypes = ["hardware", "vms", "apps", "storage", "networks", "misc"];

  // Top-level links after the inventory section: [path, i18n key, svg body]
  const links = [
    ["/map", "nav.map", '<circle cx="6" cy="6" r="2"/><circle cx="18" cy="6" r="2"/><circle cx="12" cy="18" r="2"/><line x1="8" y1="6" x2="16" y2="6"/><line x1="7" y1="8" x2="11" y2="16"/><line x1="17" y1="8" x2="13" y2="16"/>'],
    ["/ipam", "nav.ipam", '<rect x="2" y="3" width="20" height="6" rx="1"/><rect x="2" y="15" width="20" height="6" rx="1"/><line x1="6" y1="6" x2="6.01" y2="6"/><line x1="6" y1="18" x2="6.01" y2="18"/>'],
    ["/docs", "nav.docs", '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/>'],
    ["/integrations", "nav.integrations", '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/>'],
  ];

  let inventoryExpanded = true;
  let fileInput;

  function isActive(itemPath, currentPath) {
    if (itemPath === "/") return currentPath === "/";
    return currentPath.startsWith(itemPath);
  }

  // Close the drawer after navigating
  $: $location, dispatch("close");

  async function onFile(event) {
    const file = event.target.files[0];
    event.target.value = "";
    await importDatabase(file);
  }
</script>

<nav class="sidebar" class:open id="sidebar" aria-label={$t("nav.main")}>
  <ul class="nav-list">
    <li>
      <a href="#/" class:active={isActive("/", $location)} aria-current={$location === "/" ? "page" : undefined}>
        <span class="icon" aria-hidden="true"><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg></span>
        {$t("nav.dashboard")}
      </a>
    </li>
    <li class="section">
      <button
        type="button"
        class="section-header"
        class:active={$location.startsWith("/inventory")}
        aria-expanded={inventoryExpanded}
        aria-controls="inventory-links"
        on:click={() => (inventoryExpanded = !inventoryExpanded)}
      >
        <span class="icon" aria-hidden="true"><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/></svg></span>
        <span class="section-title">{$t("nav.inventory")}</span>
        <span class="expand-icon" class:collapsed={!inventoryExpanded} aria-hidden="true">
          <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"/></svg>
        </span>
      </button>
      {#if inventoryExpanded}
        <ul class="subsection" id="inventory-links">
          {#each inventoryTypes as type}
            <li>
              <a
                href={"#/inventory/" + type}
                class:active={$location.startsWith("/inventory/" + type)}
                aria-current={$location.startsWith("/inventory/" + type) ? "page" : undefined}
              >
                {$t(`types.${type}`)}
              </a>
            </li>
          {/each}
        </ul>
      {/if}
    </li>
    {#each links as [path, key, icon]}
      <li>
        <a href={"#" + path} class:active={isActive(path, $location)} aria-current={isActive(path, $location) ? "page" : undefined}>
          <span class="icon" aria-hidden="true"><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{@html icon}</svg></span>
          {$t(key)}
        </a>
      </li>
    {/each}
  </ul>

  <div class="sidebar-footer">
    <div class="footer-row">
      <button type="button" class="outline secondary small" on:click={exportDatabase}>{$t("header.export")}</button>
      <button type="button" class="outline secondary small" on:click={() => fileInput.click()}>{$t("header.import")}</button>
      <input bind:this={fileInput} type="file" accept=".json,application/json" hidden on:change={onFile} />
    </div>
    <label class="setting">
      <span>{$t("header.language")}</span>
      <select bind:value={$locale}>
        {#each LOCALES as option}
          <option value={option.code}>{option.label}</option>
        {/each}
      </select>
    </label>
    <label class="setting">
      <span>{$t("header.theme")}</span>
      <select bind:value={$theme}>
        {#each THEMES as option}
          <option value={option}>{$t(`header.themes.${option}`)}</option>
        {/each}
      </select>
    </label>
    {#if $session.authEnabled}
      <div class="footer-row user-row">
        <span class="user" title={$session.user}>👤 {$session.user}</span>
        <button type="button" class="outline secondary small" on:click={logout}>{$t("header.logout")}</button>
      </div>
    {/if}
  </div>
</nav>

<style>
  .sidebar {
    width: 230px;
    min-width: 230px;
    background: var(--hub-surface);
    border-right: 1px solid var(--hub-border);
    display: flex;
    flex-direction: column;
    flex-shrink: 0;
    position: sticky;
    top: 0;
    height: 100vh;
    overflow-y: auto;
  }

  /* Pico lays out "nav ul/li" as a horizontal bar with negative margins: undo that here */
  .nav-list,
  .subsection {
    list-style: none;
    padding: 0;
    margin: 0;
    display: flex;
    flex-direction: column;
    align-items: stretch;
  }
  .nav-list {
    padding: 0.5rem 0;
    flex: 1;
  }
  .nav-list li {
    list-style: none;
    display: block;
    margin: 0;
    padding: 0;
  }

  a,
  .section-header {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    width: 100%;
    box-sizing: border-box;
    padding: 0.6rem 1rem;
    color: var(--hub-nav-color);
    text-decoration: none;
    border-radius: 0;
  }
  .section-header {
    background: transparent;
    border: none;
    margin: 0;
    font-size: inherit;
    font-weight: 500;
    text-align: left;
    cursor: pointer;
  }
  a:hover,
  .section-header:hover {
    color: var(--hub-text);
    background: var(--hub-surface-hover);
  }
  a.active,
  .section-header.active {
    color: var(--pico-primary);
    font-weight: 600;
  }
  a:focus-visible,
  .section-header:focus-visible {
    outline: 2px solid var(--pico-primary);
    outline-offset: -2px;
  }
  .section-header:focus:not(:focus-visible) {
    box-shadow: none;
  }
  .subsection a {
    padding: 0.45rem 1rem 0.45rem 2.6rem;
    font-size: 0.9rem;
  }

  .icon {
    width: 1.5rem;
    display: inline-flex;
    justify-content: center;
    flex-shrink: 0;
  }
  .section-title {
    flex: 1;
  }
  .expand-icon {
    display: flex;
    transition: transform 0.15s;
  }
  .expand-icon.collapsed {
    transform: rotate(-90deg);
  }

  .sidebar-footer {
    border-top: 1px solid var(--hub-border);
    padding: 0.75rem 1rem 1rem;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    font-size: 0.85rem;
  }
  .footer-row {
    display: flex;
    gap: 0.4rem;
  }
  .footer-row button {
    flex: 1;
  }
  .setting {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 0.5rem;
    margin: 0;
    color: var(--hub-nav-color);
  }
  .setting select {
    width: auto;
    max-width: 60%;
    margin: 0;
    padding: 0.2rem 1.8rem 0.2rem 0.5rem;
    font-size: 0.8rem;
    height: auto;
  }
  .user-row {
    align-items: center;
    justify-content: space-between;
  }
  .user-row button {
    flex: 0 0 auto;
  }
  .user {
    color: var(--hub-nav-color);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  /* Off-canvas drawer on narrow screens */
  @media (max-width: 900px) {
    .sidebar {
      position: fixed;
      top: 0;
      left: 0;
      bottom: 0;
      z-index: 8000;
      height: 100%;
      transform: translateX(-100%);
      transition: transform 0.2s ease;
      box-shadow: var(--hub-shadow);
    }
    .sidebar.open {
      transform: translateX(0);
    }
  }
  @media (prefers-reduced-motion: reduce) {
    .sidebar,
    .expand-icon {
      transition: none;
    }
  }
</style>
