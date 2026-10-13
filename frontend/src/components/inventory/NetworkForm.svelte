<script>
  import { t } from "../../lib/i18n.js";
  import TagInput from "../common/TagInput.svelte";
  export let item = {};
</script>

<div class="grid">
  <label>{$t("fields.name")} *<input type="text" bind:value={item.name} required /></label>
  <label>{$t("fields.vlan_id")}<input type="number" bind:value={item.vlan_id} /></label>
</div>
<div class="grid">
  <label>{$t("fields.subnet")}<input type="text" bind:value={item.subnet} placeholder="192.168.1.0/24" /></label>
  <label>{$t("fields.gateway")}<input type="text" bind:value={item.gateway} placeholder="192.168.1.1" /></label>
</div>
<label>{$t("fields.dns_servers")}<input type="text" bind:value={item.dns_servers} placeholder="1.1.1.1, 8.8.8.8" /></label>
<label>{$t("fields.color")}<input type="color" bind:value={item.color} /></label>
<TagInput bind:value={item.tags} />
<label>{$t("fields.notes")}<textarea bind:value={item.notes} rows="3"></textarea></label>
