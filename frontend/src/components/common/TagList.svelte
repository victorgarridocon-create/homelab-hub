<script>
  import { createEventDispatcher } from "svelte";
  import { parseTags } from "../../lib/links.js";
  import { t } from "../../lib/i18n.js";

  export let tags = "";
  export let clickable = false;

  const dispatch = createEventDispatcher();
  $: list = parseTags(tags);
</script>

{#if list.length}
  <span class="tag-list">
    {#each list as tag}
      {#if clickable}
        <button type="button" class="tag" title={$t("tags.filterBy", { tag })}
          on:click|stopPropagation={() => dispatch("select", tag)}>{tag}</button>
      {:else}
        <span class="tag">{tag}</span>
      {/if}
    {/each}
  </span>
{/if}

<style>
  .tag-list {
    display: inline-flex;
    flex-wrap: wrap;
    gap: 0.25rem;
  }
  .tag {
    display: inline-block;
    padding: 0.05rem 0.5rem;
    margin: 0;
    width: auto;
    border-radius: 999px;
    border: 1px solid var(--hub-border);
    background: var(--hub-surface-2);
    color: var(--hub-text);
    font-size: 0.75rem;
    line-height: 1.5;
    white-space: nowrap;
  }
  button.tag {
    cursor: pointer;
  }
  button.tag:hover {
    border-color: var(--pico-primary);
  }
</style>
