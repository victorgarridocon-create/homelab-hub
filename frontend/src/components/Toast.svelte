<script>
  import { toasts, dismissToast } from "../lib/stores.js";
  import { t } from "../lib/i18n.js";
</script>

<!-- Always rendered so screen readers pick up new messages -->
<div class="toast-container" role="status" aria-live="polite">
  {#each $toasts as toast (toast.id)}
    <div class="toast toast-{toast.type}" role={toast.type === "error" ? "alert" : undefined}>
      <span>{toast.message}</span>
      <button type="button" class="dismiss" aria-label={$t("common.close")} on:click={() => dismissToast(toast.id)}>×</button>
    </div>
  {/each}
</div>

<style>
  .toast-container {
    position: fixed;
    bottom: 1rem;
    right: 1rem;
    left: auto;
    z-index: 9999;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    max-width: min(420px, calc(100vw - 2rem));
  }
  .toast {
    display: flex;
    align-items: flex-start;
    gap: 0.75rem;
    padding: 0.7rem 0.75rem 0.7rem 1rem;
    border-radius: 6px;
    color: #fff;
    font-size: 0.9rem;
    box-shadow: var(--hub-shadow);
    animation: slideIn 0.2s ease-out;
  }
  .toast span {
    flex: 1;
    word-break: break-word;
  }
  .toast-info {
    background: #4f46e5;
  }
  .toast-success {
    background: #15803d;
  }
  .toast-error {
    background: #b91c1c;
  }
  .dismiss {
    all: unset;
    cursor: pointer;
    font-size: 1.2rem;
    line-height: 1;
    opacity: 0.8;
    padding: 0 0.2rem;
  }
  .dismiss:hover,
  .dismiss:focus-visible {
    opacity: 1;
    outline: 1px solid #fff;
    border-radius: 3px;
  }
  @keyframes slideIn {
    from {
      transform: translateY(20%);
      opacity: 0;
    }
    to {
      transform: translateY(0);
      opacity: 1;
    }
  }
  @media (prefers-reduced-motion: reduce) {
    .toast {
      animation: none;
    }
  }
  @media (max-width: 600px) {
    .toast-container {
      left: 1rem;
      max-width: none;
    }
  }
</style>
