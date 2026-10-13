<script>
  import { createEventDispatcher } from "svelte";
  import { t } from "../../lib/i18n.js";

  export let share = null;
  export let storageId = null;
  export let defaultIp = "";
  export let defaultHostname = "";

  const dispatch = createEventDispatcher();

  let formData = {
    id: share?.id,
    storage_id: share?.storage_id || storageId,
    name: share?.name || "",
    hostname: share?.hostname || (share ? "" : defaultHostname),
    ip: share?.ip || (share ? "" : defaultIp),
    share_type: share?.share_type || "NFS",
    notes: share?.notes || "",
  };

  const shareTypes = ["NFS", "SMB", "iSCSI", "FTP", "SFTP", "WebDAV", "Other"];
</script>

<form on:submit|preventDefault={() => dispatch("submit", formData)}>
  <div class="grid">
    <label>
      {$t("fields.name")} *
      <input type="text" bind:value={formData.name} required placeholder={$t("shares.namePlaceholder")} />
    </label>
    <label>
      {$t("fields.share_type")} *
      <select bind:value={formData.share_type} required>
        {#each shareTypes as type}
          <option value={type}>{type === "Other" ? $t("shares.other") : type}</option>
        {/each}
      </select>
    </label>
  </div>
  <div class="grid">
    <label>
      {$t("fields.hostname")}
      <input type="text" bind:value={formData.hostname} placeholder={$t("shares.hostnamePlaceholder")} />
    </label>
    <label>
      {$t("fields.ip_address")}
      <input type="text" bind:value={formData.ip} placeholder={$t("shares.ipPlaceholder")} />
    </label>
  </div>
  <label>
    {$t("fields.notes")}
    <textarea bind:value={formData.notes} rows="3" placeholder={$t("shares.notesPlaceholder")}></textarea>
  </label>

  <div class="form-actions">
    <button type="submit">{share ? $t("common.save") : $t("shares.add")}</button>
    <button type="button" class="secondary outline" on:click={() => dispatch("cancel")}>{$t("common.cancel")}</button>
  </div>
</form>
