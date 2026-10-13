<script>
  import Modal from "./Modal.svelte";
  import { dialog, closeDialog } from "../lib/dialog.js";
  import { t } from "../lib/i18n.js";

  let value = "";

  $: if ($dialog?.kind === "prompt") value = $dialog.value || "";

  function cancel() {
    closeDialog($dialog?.kind === "confirm" ? false : $dialog?.kind === "prompt" ? null : undefined);
  }

  function accept() {
    closeDialog($dialog.kind === "prompt" ? value : $dialog.kind === "confirm" ? true : undefined);
  }
</script>

<Modal
  isOpen={!!$dialog}
  title={$dialog?.title || ($dialog?.kind === "confirm" ? $t("dialog.confirmTitle") : $dialog?.kind === "alert" ? $t("dialog.alertTitle") : "")}
  maxWidth="440px"
  on:close={cancel}
>
  {#if $dialog}
    <form on:submit|preventDefault={accept}>
      {#if $dialog.kind === "prompt"}
        <label>
          {$dialog.message}
          <input type="text" bind:value placeholder={$dialog.placeholder} />
        </label>
      {:else}
        <p class="message">{$dialog.message}</p>
      {/if}
      <div class="form-actions">
        {#if $dialog.kind !== "alert"}
          <button type="button" class="secondary outline" on:click={cancel}>{$t("common.cancel")}</button>
        {/if}
        <button type="submit" class:danger={$dialog.danger}>
          {$dialog.confirmLabel || (($dialog.kind === "alert") ? $t("common.ok") : $t("common.accept"))}
        </button>
      </div>
    </form>
  {/if}
</Modal>

<style>
  .message {
    margin: 0;
    white-space: pre-line;
  }
  .form-actions {
    justify-content: flex-end;
  }
</style>
