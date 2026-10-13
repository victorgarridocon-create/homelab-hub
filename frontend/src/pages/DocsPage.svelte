<script>
  import { params } from "svelte-spa-router";
  import { onMount } from "svelte";
  import { get, post, put, del } from "../lib/api.js";
  import { addToast } from "../lib/stores.js";
  import { confirmDialog } from "../lib/dialog.js";
  import { t } from "../lib/i18n.js";
  import DocEditor from "../components/docs/DocEditor.svelte";

  let docs = [];
  let activeDoc = null;
  let loading = true;
  let saveTimeout;

  $: docId = $params?.id ? parseInt($params.id) : null;

  async function loadDocs() {
    try {
      const res = await get("/docs");
      docs = res.data;
    } catch (e) {
      addToast(e.message, "error");
    }
    loading = false;
  }

  async function loadDoc(id) {
    if (!id) {
      activeDoc = null;
      return;
    }
    try {
      const res = await get(`/docs/${id}`);
      activeDoc = res.data;
    } catch (e) {
      addToast(e.message, "error");
    }
  }

  $: loadDoc(docId);
  onMount(loadDocs);

  async function createDoc() {
    try {
      const res = await post("/docs", { title: $t("docs.untitled") });
      docs = [...docs, res.data];
      window.location.hash = `/docs/${res.data.id}`;
    } catch (e) {
      addToast(e.message, "error");
    }
  }

  async function deleteDoc(id) {
    if (!(await confirmDialog($t("docs.confirmDelete"), { confirmLabel: $t("common.delete"), danger: true }))) return;
    try {
      await del(`/docs/${id}`);
      addToast($t("toast.deleted"), "success");
      if (activeDoc?.id === id) {
        activeDoc = null;
        window.location.hash = "/docs";
      }
      loadDocs();
    } catch (e) {
      addToast(e.message, "error");
    }
  }

  function handleContentChange(content) {
    if (!activeDoc) return;
    activeDoc.content = content;
    clearTimeout(saveTimeout);
    saveTimeout = setTimeout(async () => {
      try {
        await put(`/docs/${activeDoc.id}`, {
          title: activeDoc.title,
          content: activeDoc.content,
        });
      } catch (e) {
        addToast($t("docs.autoSaveFailed", { error: e.message }), "error");
      }
    }, 1000);
  }

  async function handleTitleChange() {
    if (!activeDoc) return;
    try {
      await put(`/docs/${activeDoc.id}`, { title: activeDoc.title });
      const idx = docs.findIndex((d) => d.id === activeDoc.id);
      if (idx !== -1) docs[idx].title = activeDoc.title;
      docs = docs;
    } catch (e) {
      addToast(e.message, "error");
    }
  }
</script>

<div class="docs-page">
  <aside class="doc-list">
    <div class="doc-list-header">
      <h3>{$t("nav.docs")}</h3>
      <button class="outline small" on:click={createDoc}>+ {$t("common.new")}</button>
    </div>
    {#if loading}
      <p aria-busy="true">{$t("common.loading")}</p>
    {:else}
      <ul>
        {#each docs as doc (doc.id)}
          <li class:active={activeDoc?.id === doc.id}>
            <a href={"#/docs/" + doc.id}>{doc.title}</a>
            <button class="delete-btn" aria-label="{$t('common.delete')} {doc.title}" title={$t("common.delete")}
              on:click|stopPropagation={() => deleteDoc(doc.id)}>×</button>
          </li>
        {/each}
      </ul>
    {/if}
  </aside>

  <div class="doc-content">
    {#if activeDoc}
      <input
        class="doc-title"
        type="text"
        aria-label={$t("fields.title")}
        bind:value={activeDoc.title}
        on:blur={handleTitleChange}
      />
      <DocEditor content={activeDoc.content} onChange={handleContentChange} />
    {:else}
      <p class="placeholder">{$t("docs.selectOrCreate")}</p>
    {/if}
  </div>
</div>

<style>
  .docs-page {
    display: flex;
    gap: 0;
    min-height: calc(100vh - 7rem);
  }
  .doc-list {
    width: 240px;
    border-right: 1px solid var(--pico-muted-border-color);
    padding: 1rem;
    overflow-y: auto;
    flex-shrink: 0;
  }
  .doc-list-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.5rem;
  }
  .doc-list-header h3 {
    margin: 0;
    font-size: 1rem;
  }
  .doc-list-header button {
    white-space: nowrap;
  }
  ul {
    list-style: none;
    padding: 0;
    margin: 0;
  }
  li {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.4rem 0.5rem;
    border-radius: 4px;
  }
  li:hover {
    background: var(--hub-surface-hover);
  }
  li.active {
    background: var(--hub-info-bg);
  }
  li.active a {
    color: var(--pico-primary);
    font-weight: 600;
  }
  li a {
    text-decoration: none;
    flex: 1;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .delete-btn {
    background: none;
    border: none;
    color: var(--pico-muted-color);
    cursor: pointer;
    padding: 0 0.4rem;
    font-size: 1.1rem;
    line-height: 1;
    width: auto;
    margin: 0;
  }
  .delete-btn:hover,
  .delete-btn:focus-visible {
    color: var(--hub-danger);
  }
  .doc-content {
    flex: 1;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }
  .doc-title {
    font-size: 1.4rem;
    font-weight: 600;
    border: none;
    border-bottom: 1px solid var(--pico-muted-border-color);
    border-radius: 0;
    margin-bottom: 0;
    padding: 0.5rem;
  }
  .doc-content {
    padding-left: 1rem;
    min-width: 0;
  }
  .placeholder {
    padding: 2rem;
    color: var(--pico-muted-color);
  }
  @media (max-width: 900px) {
    .docs-page {
      flex-direction: column;
    }
    .doc-list {
      width: auto;
      max-height: 30vh;
      border-right: none;
      border-bottom: 1px solid var(--hub-border);
      padding: 0 0 0.75rem;
    }
    .doc-content {
      padding: 0.75rem 0 0;
    }
  }
</style>
