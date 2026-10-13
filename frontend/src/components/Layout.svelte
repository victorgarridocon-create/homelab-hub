<script>
  import Sidebar from "./Sidebar.svelte";
  import GlobalSearch from "./GlobalSearch.svelte";
  import { t } from "../lib/i18n.js";

  let menuOpen = false;
</script>

<svelte:window on:keydown={(e) => e.key === "Escape" && menuOpen && (menuOpen = false)} />

<a class="skip-link" href="#main-content">{$t("nav.skipToContent")}</a>

<div class="layout">
  <Sidebar open={menuOpen} on:close={() => (menuOpen = false)} />
  {#if menuOpen}
    <!-- svelte-ignore a11y-click-events-have-key-events -->
    <!-- svelte-ignore a11y-no-static-element-interactions -->
    <div class="drawer-backdrop" on:click={() => (menuOpen = false)}></div>
  {/if}

  <div class="page">
    <header class="header">
      <button
        type="button"
        class="menu-btn"
        aria-label={$t("nav.menu")}
        aria-expanded={menuOpen}
        aria-controls="sidebar"
        on:click={() => (menuOpen = !menuOpen)}
      >
        <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/></svg>
      </button>
      <a class="brand" href="#/">Home Lab Hub</a>
      <GlobalSearch />
    </header>

    <main class="main" id="main-content" tabindex="-1">
      <slot />
    </main>
  </div>
</div>

<style>
  .layout {
    display: flex;
    min-height: 100vh;
  }

  .page {
    flex: 1;
    min-width: 0;
    display: flex;
    flex-direction: column;
  }

  .header {
    position: sticky;
    top: 0;
    z-index: 100;
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 0.6rem 1.5rem;
    background: var(--hub-header-bg);
    color: var(--hub-header-color);
    border-bottom: 1px solid var(--hub-border);
  }

  .brand {
    font-size: 1.25rem;
    font-weight: 700;
    color: inherit;
    text-decoration: none;
    white-space: nowrap;
  }

  .menu-btn {
    display: none;
    background: transparent;
    border: none;
    color: inherit;
    padding: 0.3rem;
    margin: 0;
    width: auto;
    line-height: 0;
  }

  .main {
    flex: 1;
    padding: 1.5rem;
    min-width: 0;
  }
  .main:focus {
    outline: none;
  }

  .skip-link {
    position: absolute;
    left: -9999px;
    top: 0.5rem;
    z-index: 10000;
    padding: 0.5rem 1rem;
    background: var(--pico-primary-background);
    color: var(--pico-primary-inverse);
    border-radius: 4px;
  }
  .skip-link:focus {
    left: 0.5rem;
  }

  .drawer-backdrop {
    display: none;
  }

  @media (max-width: 900px) {
    .menu-btn {
      display: inline-flex;
    }
    .drawer-backdrop {
      display: block;
      position: fixed;
      inset: 0;
      z-index: 7999;
      background: var(--hub-backdrop);
    }
    .header {
      flex-wrap: wrap;
      gap: 0.5rem 0.75rem;
      padding: 0.5rem 1rem;
    }
    .main {
      padding: 1rem;
    }
  }

  @media (max-width: 600px) {
    /* Search gets its own full-width row */
    .header :global(.global-search) {
      order: 3;
      flex-basis: 100%;
      max-width: none;
    }
  }
</style>
