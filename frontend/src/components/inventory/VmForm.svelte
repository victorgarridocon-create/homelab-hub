<script>
  import { t } from "../../lib/i18n.js";
  import TagInput from "../common/TagInput.svelte";
  import IpField from "../common/IpField.svelte";
  import { onMount } from "svelte";
  import { get } from "../../lib/api.js";
  import IconPicker from "./IconPicker.svelte";

  export let item = {};

  let hardwareOptions = [];

  onMount(async () => {
    try {
      const res = await get("/hardware");
      hardwareOptions = res.data;
    } catch (e) {
      // ignore — dropdown will be empty
    }
  });
</script>

<div class="grid">
  <label>{$t("fields.name")} *<input type="text" bind:value={item.name} required /></label>
  <label>
    {$t("typeSingular.hardware")} *
    <select bind:value={item.hardware_id} required>
      <option value="">{$t("inventory.selectHardware")}</option>
      {#each hardwareOptions as hw}
        <option value={hw.id}>{hw.name}</option>
      {/each}
    </select>
  </label>
</div>
<div class="grid">
  <label>{$t("fields.hostname")}<input type="text" bind:value={item.hostname} /></label>
  <IpField bind:value={item.ip_address} type="vms" id={item.id} />
</div>
<div class="grid">
  <label>{$t("fields.mac_address")}<input type="text" bind:value={item.mac_address} placeholder="00:00:00:00:00:00" /></label>
  <label>{$t("fields.os")}<input type="text" bind:value={item.os} /></label>
</div>
<div class="grid">
  <label>{$t("fields.cpu_cores")}<input type="number" bind:value={item.cpu_cores} /></label>
  <label>{$t("fields.ram_gb")}<input type="number" step="0.1" bind:value={item.ram_gb} /></label>
  <label>{$t("fields.disk_gb")}<input type="number" step="0.1" bind:value={item.disk_gb} /></label>
</div>
<IconPicker bind:value={item.icon} />
<TagInput bind:value={item.tags} />
<label>{$t("fields.notes")}<textarea bind:value={item.notes} rows="3"></textarea></label>
