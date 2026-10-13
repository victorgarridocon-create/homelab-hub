<script>
  import { t } from "../../lib/i18n.js";
  import TagInput from "../common/TagInput.svelte";
  import IpField from "../common/IpField.svelte";
  import IconPicker from "./IconPicker.svelte";

  export let item = {};
</script>

<div class="grid">
  <label>{$t("fields.name")} *<input type="text" bind:value={item.name} required /></label>
  <label>{$t("fields.hostname")}<input type="text" bind:value={item.hostname} /></label>
</div>
<div class="grid">
  <IpField bind:value={item.ip_address} type="hardware" id={item.id} />
  <label>{$t("fields.mac_address")}<input type="text" bind:value={item.mac_address} placeholder="00:00:00:00:00:00" /></label>
</div>
<div class="grid">
  <label>{$t("fields.os")}<input type="text" bind:value={item.os} /></label>
</div>
<div class="grid">
  <label>{$t("fields.cpu")}<input type="text" bind:value={item.cpu} /></label>
  <label>{$t("fields.cpu_cores")}<input type="number" bind:value={item.cpu_cores} /></label>
  <label>{$t("fields.ram_gb")}<input type="number" step="0.1" bind:value={item.ram_gb} /></label>
</div>
<div class="grid">
  <label>{$t("fields.make")}<input type="text" bind:value={item.make} /></label>
  <label>{$t("fields.model")}<input type="text" bind:value={item.model} /></label>
</div>
<div class="grid">
  <label>{$t("fields.serial_number")}<input type="text" bind:value={item.serial_number} /></label>
  <label>{$t("fields.location")}<input type="text" bind:value={item.location} /></label>
</div>
<IconPicker bind:value={item.icon} />
<div class="grid">
  <label>{$t("fields.purchase_date")}<input type="date" bind:value={item.purchase_date} /></label>
  <label>{$t("fields.warranty_until")}<input type="date" bind:value={item.warranty_until} /></label>
</div>
<TagInput bind:value={item.tags} />
<label>{$t("fields.notes")}<textarea bind:value={item.notes} rows="3"></textarea></label>
