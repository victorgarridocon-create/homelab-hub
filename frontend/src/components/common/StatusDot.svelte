<script>
  import { statusMap } from "../../lib/status.js";
  import { t } from "../../lib/i18n.js";

  export let key;
  export let showLabel = false;

  $: info = $statusMap[key];
  $: state = info?.status || "unknown";
  $: title = info
    ? `${$t(`status.${state}`)} · ${info.target}${info.latency_ms != null ? ` · ${info.latency_ms} ms` : ""} (${info.method})`
    : $t("status.unknownHint");
</script>

<span class="status status-{state}" {title} role="img" aria-label={title}>
  <span class="dot"></span>
  {#if showLabel}<span class="label">{$t(`status.${state}`)}</span>{/if}
</span>

<style>
  .status {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    font-size: 0.8rem;
    white-space: nowrap;
  }
  .dot {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    background: var(--hub-neutral);
    flex-shrink: 0;
  }
  .status-up .dot {
    background: var(--hub-success);
    box-shadow: 0 0 0 3px var(--hub-success-bg);
  }
  .status-down .dot {
    background: var(--hub-danger);
    box-shadow: 0 0 0 3px var(--hub-danger-bg);
  }
  .status-down .label {
    color: var(--hub-danger);
  }
</style>
