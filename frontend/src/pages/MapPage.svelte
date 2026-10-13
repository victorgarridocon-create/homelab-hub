<script>
  import NetworkMap from "../components/map/NetworkMap.svelte";
  import TreeView from "../components/map/TreeView.svelte";
  import MapControls from "../components/map/MapControls.svelte";
  import { t } from "../lib/i18n.js";

  let mapComponent;
  let viewMode = "map"; // "map" or "tree"
</script>

<div class="map-page">
  <div class="map-header">
    <h2>{$t("map.title")}</h2>
    <div class="header-controls">
      <div class="view-toggle">
        <button 
          class:active={viewMode === "map"} 
          on:click={() => viewMode = "map"}
        >
          {$t("map.mapView")}
        </button>
        <button 
          class:active={viewMode === "tree"} 
          on:click={() => viewMode = "tree"}
        >
          {$t("map.treeView")}
        </button>
      </div>
      {#if viewMode === "map"}
        <MapControls 
          on:relayout={() => mapComponent?.relayout()} 
        />
      {/if}
    </div>
  </div>
  <div class="map-container">
    {#if viewMode === "map"}
      <NetworkMap bind:this={mapComponent} />
    {:else}
      <TreeView />
    {/if}
  </div>
</div>

<style>
  .map-page {
    display: flex;
    flex-direction: column;
    height: calc(100vh - 7rem);
    min-height: 420px;
  }
  .map-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 0.5rem 1rem;
    margin-bottom: 0.5rem;
  }
  .map-header h2 {
    margin: 0;
  }
  .header-controls {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 0.5rem 1rem;
  }
  .view-toggle {
    display: flex;
    gap: 0;
    border: 1px solid var(--pico-muted-border-color);
    border-radius: 6px;
    overflow: hidden;
  }
  .view-toggle button {
    margin: 0;
    padding: 0.4rem 1rem;
    font-size: 0.85rem;
    width: auto;
    white-space: nowrap;
    background: var(--hub-surface-2);
    border: none;
    border-right: 1px solid var(--hub-border);
    color: var(--hub-text);
    cursor: pointer;
    border-radius: 0;
  }
  .view-toggle button:last-child {
    border-right: none;
  }
  .view-toggle button.active {
    background: var(--pico-primary-background);
    color: var(--pico-primary-inverse);
  }
  .view-toggle button:hover:not(.active) {
    background: var(--hub-surface-hover);
  }
  .map-container {
    flex: 1;
    border: 1px solid var(--pico-muted-border-color);
    border-radius: 8px;
    overflow: hidden;
    position: relative;
  }
  @media (max-width: 700px) {
    .map-header h2 {
      font-size: 1.4rem;
    }
    .map-page {
      height: calc(100vh - 11rem);
    }
  }
</style>
