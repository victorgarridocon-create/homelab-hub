<script>
  import { t } from "../../lib/i18n.js";
  import TagInput from "../common/TagInput.svelte";
  import { onMount } from "svelte";
  import { get } from "../../lib/api.js";
  import IconPicker from "./IconPicker.svelte";

  export let item = {};

  let hardwareOptions = [];
  let vmOptions = [];
  let parentType = item.vm_id ? "vm" : item.hardware_id ? "hardware" : "none";
  let previousHardwareId = item.hardware_id;
  let previousVmId = item.vm_id;

  onMount(async () => {
    try {
      const [hwRes, vmRes] = await Promise.all([get("/hardware"), get("/vms")]);
      hardwareOptions = hwRes.data;
      vmOptions = vmRes.data;
    } catch (e) {
      // ignore
    }
    if (item.vm_id) parentType = "vm";
    else if (item.hardware_id) parentType = "hardware";
  });

  $: {
    if (parentType === "none") {
      item.hardware_id = null;
      item.vm_id = null;
    } else if (parentType === "hardware") {
      item.vm_id = null;
    } else if (parentType === "vm") {
      item.hardware_id = null;
    }
  }

  // Auto-populate hostname and IP from parent only when creating a new app
  $: if (!item.id && item.hardware_id && hardwareOptions.length > 0 && item.hardware_id !== previousHardwareId) {
    const hardware = hardwareOptions.find(h => h.id === item.hardware_id);
    if (hardware) {
      if (hardware.hostname && !item.hostname) {
        item.hostname = hardware.hostname;
      }
      if (hardware.ip_address && !item.ip_address) {
        item.ip_address = hardware.ip_address;
      }
    }
    previousHardwareId = item.hardware_id;
  }

  $: if (!item.id && item.vm_id && vmOptions.length > 0 && item.vm_id !== previousVmId) {
    const vm = vmOptions.find(v => v.id === item.vm_id);
    if (vm) {
      if (vm.hostname && !item.hostname) {
        item.hostname = vm.hostname;
      }
      if (vm.ip_address && !item.ip_address) {
        item.ip_address = vm.ip_address;
      }
    }
    previousVmId = item.vm_id;
  }
</script>

<div class="grid">
  <label>{$t("fields.name")} *<input type="text" bind:value={item.name} required /></label>
  <label>
    {$t("inventory.runsOn")}
    <select bind:value={parentType}>
      <option value="none">{$t("inventory.standalone")}</option>
      <option value="hardware">{$t("inventory.bareMetal")}</option>
      <option value="vm">{$t("typeSingular.vms")}</option>
    </select>
  </label>
</div>

{#if parentType === "hardware"}
  <label>
    {$t("typeSingular.hardware")}
    <select bind:value={item.hardware_id}>
      <option value="">{$t("common.select")}</option>
      {#each hardwareOptions as hw}
        <option value={hw.id}>{hw.name}</option>
      {/each}
    </select>
  </label>
{:else if parentType === "vm"}
  <label>
    {$t("typeSingular.vms")}
    <select bind:value={item.vm_id}>
      <option value="">{$t("common.select")}</option>
      {#each vmOptions as vm}
        <option value={vm.id}>{vm.name}</option>
      {/each}
    </select>
  </label>
{/if}

<label>{$t("fields.description")}<input type="text" bind:value={item.description} /></label>
<div class="grid">
  <label>{$t("fields.hostname")}<input type="text" bind:value={item.hostname} placeholder={$t("inventory.defaultsParentHost")} /></label>
  <label>{$t("fields.ip_address")}<input type="text" bind:value={item.ip_address} placeholder={$t("inventory.defaultsParentIp")} /></label>
</div>
<div class="grid">
  <label>{$t("fields.external_hostname")}<input type="text" bind:value={item.external_hostname} /></label>
  <label>{$t("fields.port")}<input type="number" bind:value={item.port} /></label>
</div>
<label>
  <input type="checkbox" bind:checked={item.https} />
  {$t("inventory.useHttps")}
</label>
<IconPicker bind:value={item.icon} />
<label>{$t("fields.renewal_date")}<input type="date" bind:value={item.renewal_date} />
  <small>{$t("inventory.renewalHint")}</small>
</label>
<TagInput bind:value={item.tags} />
<label>{$t("fields.notes")}<textarea bind:value={item.notes} rows="3"></textarea></label>
