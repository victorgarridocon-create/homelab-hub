<script>
  import { get } from "../../lib/api.js";
  import { t } from "../../lib/i18n.js";

  export let value = "";
  export let type;
  export let id = null;
  export let placeholder = "";

  let conflicts = [];
  let invalid = false;

  async function check() {
    conflicts = [];
    invalid = false;
    const ip = (value || "").trim();
    if (!ip) return;
    try {
      const exclude = id ? `&exclude=${type}-${id}` : "";
      const res = await get(`/ipam/check?ip=${encodeURIComponent(ip)}${exclude}`);
      invalid = !res.data.valid;
      conflicts = res.data.conflicts;
    } catch {
      // The warning is advisory: ignore network errors
    }
  }
</script>

<label>
  {$t("fields.ip_address")}
  <input type="text" bind:value {placeholder} on:blur={check}
    aria-invalid={invalid ? "true" : undefined} />
  {#if invalid}
    <small class="warn">{$t("ipam.invalidIp")}</small>
  {:else if conflicts.length}
    <small class="warn">
      {$t("ipam.inUseBy", { names: conflicts.map((c) => `${c.name} (${$t(`typeSingular.${c.type}`)})`).join(", ") })}
    </small>
  {/if}
</label>

<style>
  .warn {
    color: var(--hub-warning);
  }
</style>
