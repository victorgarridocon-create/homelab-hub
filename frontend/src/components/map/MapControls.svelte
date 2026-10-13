<script>
  import { createEventDispatcher } from "svelte";
  import { t } from "../../lib/i18n.js";

  const dispatch = createEventDispatcher();
</script>

<div class="map-controls">
  <button class="outline small" on:click={() => dispatch("relayout")}>
    {$t("map.autoLayout")}
  </button>
</div>

<style>
  .map-controls {
    display: flex;
    gap: 0.5rem;
  }
</style>
