<script>
  import { t } from "../../lib/i18n.js";
  import TagInput from "../common/TagInput.svelte";
  import IpField from "../common/IpField.svelte";
  import IconPicker from "./IconPicker.svelte";

  export let item = {};
</script>

<div class="grid">
  <label>{$t("fields.name")} *<input type="text" bind:value={item.name} required /></label>
  <label>{$t("fields.category")}<input type="text" bind:value={item.category} /></label>
</div>
<div class="grid">
  <label>{$t("fields.hostname")}<input type="text" bind:value={item.hostname} /></label>
  <IpField bind:value={item.ip_address} type="misc" id={item.id} />
</div>
<label>{$t("fields.description")}<textarea bind:value={item.description} rows="2"></textarea></label>
<IconPicker bind:value={item.icon} />
<label>{$t("fields.renewal_date")}<input type="date" bind:value={item.renewal_date} />
  <small>{$t("inventory.renewalHint")}</small>
</label>
<TagInput bind:value={item.tags} />
<label>{$t("fields.notes")}<textarea bind:value={item.notes} rows="3"></textarea></label>
