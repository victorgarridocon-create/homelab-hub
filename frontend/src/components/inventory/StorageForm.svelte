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
</script>

<div class="grid">
  <label>{$t("fields.name")} *<input type="text" bind:value={item.name} required /></label>
  <label>
    {$t("inventory.runsOn")}
    <select bind:value={parentType}>
      <option value="none">{$t("inventory.standalone")}</option>
      <option value="hardware">{$t("typeSingular.hardware")}</option>
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

<div class="grid">
  <label>{$t("fields.storage_type")}<input type="text" bind:value={item.storage_type} placeholder="HDD, SSD, NVMe..." /></label>
  <label>{$t("fields.raid_type")}<input type="text" bind:value={item.raid_type} placeholder="RAID-Z2, RAID 10..." /></label>
</div>
<div class="grid">
  <label>{$t("fields.drive_count")}<input type="number" bind:value={item.drive_count} /></label>
  <label>{$t("fields.raw_space_tb")}<input type="number" step="0.01" bind:value={item.raw_space_tb} /></label>
  <label>{$t("fields.usable_space_tb")}<input type="number" step="0.01" bind:value={item.usable_space_tb} /></label>
</div>
<label>{$t("fields.filesystem")}<input type="text" bind:value={item.filesystem} placeholder="ZFS, EXT4, BTRFS..." /></label>
<IconPicker bind:value={item.icon} />
<TagInput bind:value={item.tags} />
<label>{$t("fields.notes")}<textarea bind:value={item.notes} rows="3"></textarea></label>
