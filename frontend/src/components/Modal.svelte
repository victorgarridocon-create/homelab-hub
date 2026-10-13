<script>
  import { createEventDispatcher, tick } from "svelte";
  import { t } from "../lib/i18n.js";

  export let isOpen = false;
  export let title = "";
  export let maxWidth = "600px";

  const dispatch = createEventDispatcher();
  const titleId = `modal-title-${Math.random().toString(36).slice(2, 8)}`;
  let container;
  let previouslyFocused = null;

  const FOCUSABLE = 'a[href], button:not([disabled]), input:not([disabled]):not([type="hidden"]), select, textarea, [tabindex]:not([tabindex="-1"])';

  function handleClose() {
    dispatch("close");
  }

  function handleBackdropClick(event) {
    if (event.target === event.currentTarget) handleClose();
  }

  // Keep Tab inside the dialog and close on Escape
  function handleKeydown(event) {
    if (!isOpen) return;
    if (event.key === "Escape") {
      event.stopPropagation();
      handleClose();
      return;
    }
    if (event.key !== "Tab" || !container) return;
    const items = [...container.querySelectorAll(FOCUSABLE)];
    if (!items.length) return;
    const first = items[0];
    const last = items[items.length - 1];
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first.focus();
    }
  }

  async function onOpenChange(open) {
    if (open) {
      previouslyFocused = document.activeElement;
      await tick();
      // Focus the first field (skipping the close button), else the dialog itself
      const target = container?.querySelector(".modal-body " + FOCUSABLE.split(", ").join(", .modal-body "));
      (target || container)?.focus();
    } else if (previouslyFocused?.focus) {
      previouslyFocused.focus();
      previouslyFocused = null;
    }
  }

  $: onOpenChange(isOpen);
</script>

<svelte:window on:keydown={handleKeydown} />

{#if isOpen}
  <!-- svelte-ignore a11y-click-events-have-key-events -->
  <!-- svelte-ignore a11y-no-static-element-interactions -->
  <div class="modal-backdrop" on:click={handleBackdropClick}>
    <div
      class="modal-container"
      style="max-width: {maxWidth}"
      role="dialog"
      aria-modal="true"
      aria-labelledby={title ? titleId : undefined}
      tabindex="-1"
      bind:this={container}
    >
      <div class="modal-header">
        {#if title}
          <h2 id={titleId}>{title}</h2>
        {/if}
        <button type="button" class="close-btn" on:click={handleClose} aria-label={$t("common.close")}>×</button>
      </div>
      <div class="modal-body">
        <slot />
      </div>
    </div>
  </div>
{/if}

<style>
  .modal-backdrop {
    position: fixed;
    inset: 0;
    background: var(--hub-backdrop);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 9000;
    padding: 1rem;
    overflow-y: auto;
  }

  .modal-container {
    background: var(--pico-background-color);
    color: var(--pico-color);
    border: 1px solid var(--hub-border);
    border-radius: 8px;
    box-shadow: var(--hub-shadow);
    width: 100%;
    max-height: 90vh;
    display: flex;
    flex-direction: column;
    margin: auto;
  }

  .modal-container:focus {
    outline: none;
  }

  .modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 1rem;
    padding: 1rem 1.5rem;
    border-bottom: 1px solid var(--hub-border);
  }

  .modal-header h2 {
    margin: 0;
    font-size: 1.2rem;
  }

  .close-btn {
    background: transparent;
    border: none;
    color: var(--pico-muted-color);
    font-size: 1.8rem;
    cursor: pointer;
    padding: 0;
    margin: 0 0 0 auto;
    width: 36px;
    height: 36px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 4px;
    line-height: 1;
  }

  .close-btn:hover {
    background: var(--hub-surface-hover);
    color: var(--hub-text);
  }

  .modal-body {
    padding: 1.25rem 1.5rem;
    overflow-y: auto;
    flex: 1;
  }

  @media (max-width: 768px) {
    .modal-backdrop {
      padding: 0;
      align-items: stretch;
    }

    .modal-container {
      max-height: none;
      min-height: 100%;
      border-radius: 0;
      border: none;
    }

    .modal-body {
      padding: 1rem;
    }
  }
</style>
