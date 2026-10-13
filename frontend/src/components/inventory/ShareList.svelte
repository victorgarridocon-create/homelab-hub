<script>
  import { createEventDispatcher } from "svelte";
  import { t } from "../../lib/i18n.js";
  import { confirmDialog } from "../../lib/dialog.js";
  import Modal from "../Modal.svelte";
  import ShareForm from "./ShareForm.svelte";

  export let shares = [];
  export let storageId;
  export let parentIp = "";
  export let parentHostname = "";

  const dispatch = createEventDispatcher();

  let isModalOpen = false;
  let editingShare = null;

  function openForm(share = null) {
    editingShare = share;
    isModalOpen = true;
  }

  function closeForm() {
    isModalOpen = false;
    editingShare = null;
  }

  function handleFormSubmit(event) {
    dispatch("save", event.detail);
    closeForm();
  }

  async function handleDeleteShare(share) {
    const ok = await confirmDialog($t("shares.confirmDelete", { name: share.name }), {
      confirmLabel: $t("common.delete"),
      danger: true,
    });
    if (ok) dispatch("delete", share);
  }
</script>

<section class="shares-section">
  <div class="shares-header">
    <h3>{$t("types.shares")}</h3>
    <button type="button" class="small" on:click={() => openForm()}>+ {$t("shares.add")}</button>
  </div>

  {#if shares.length > 0}
    <ul class="shares-list">
      {#each shares as share (share.id)}
        <li class="share-item">
          <div class="share-info">
            <div class="share-name">{share.name}</div>
            <div class="share-details">
              <span class="badge info">{share.share_type === "Other" ? $t("shares.other") : share.share_type}</span>
              {#if share.hostname}
                <span class="muted">{$t("fields.hostname")}: {share.hostname}</span>
              {/if}
              {#if share.ip}
                <span class="muted">IP: {share.ip}</span>
              {/if}
            </div>
            {#if share.notes}
              <div class="share-notes muted">{share.notes}</div>
            {/if}
          </div>
          <div class="share-actions">
            <button type="button" class="outline secondary small" on:click={() => openForm(share)}>
              {$t("common.edit")}
            </button>
            <button type="button" class="outline danger small" on:click={() => handleDeleteShare(share)}>
              {$t("common.delete")}
            </button>
          </div>
        </li>
      {/each}
    </ul>
  {:else}
    <p class="muted">{$t("shares.empty")}</p>
  {/if}
</section>

<Modal
  isOpen={isModalOpen}
  title={editingShare ? $t("shares.editTitle") : $t("shares.addTitle")}
  on:close={closeForm}
>
  {#key editingShare}
    <ShareForm
      share={editingShare}
      {storageId}
      defaultIp={parentIp}
      defaultHostname={parentHostname}
      on:submit={handleFormSubmit}
      on:cancel={closeForm}
    />
  {/key}
</Modal>

<style>
  .shares-section {
    margin-top: 2rem;
    padding-top: 1.5rem;
    border-top: 1px solid var(--hub-border);
    max-width: 700px;
  }
  .shares-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
  }
  .shares-header h3 {
    margin: 0;
  }
  .shares-list {
    list-style: none;
    padding: 0;
    margin: 0;
    display: flex;
    flex-direction: column;
    gap: 0.6rem;
  }
  .share-item {
    list-style: none;
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 1rem;
    padding: 0.8rem 1rem;
    background: var(--hub-surface-2);
    border: 1px solid var(--hub-border);
    border-radius: 6px;
  }
  .share-info {
    flex: 1;
    min-width: 0;
  }
  .share-name {
    font-weight: 600;
    margin-bottom: 0.3rem;
  }
  .share-details {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 0.4rem 0.8rem;
  }
  .share-notes {
    margin-top: 0.4rem;
    font-style: italic;
  }
  .share-actions {
    display: flex;
    gap: 0.4rem;
    flex-shrink: 0;
  }
  @media (max-width: 600px) {
    .share-item {
      flex-direction: column;
    }
  }
</style>
