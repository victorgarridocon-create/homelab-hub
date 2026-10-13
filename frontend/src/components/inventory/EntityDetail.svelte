<script>
  import { onMount, onDestroy, createEventDispatcher, tick } from "svelte";
  import { get, post, put, del } from "../../lib/api.js";
  import { addToast } from "../../lib/stores.js";
  import { t } from "../../lib/i18n.js";
  import { appUrl } from "../../lib/links.js";
  import { setDirty, confirmLeave } from "../../lib/unsaved.js";
  import { refreshStatus } from "../../lib/status.js";
  import StatusDot from "../common/StatusDot.svelte";
  import HardwareForm from "./HardwareForm.svelte";
  import VmForm from "./VmForm.svelte";
  import AppForm from "./AppForm.svelte";
  import StorageForm from "./StorageForm.svelte";
  import NetworkForm from "./NetworkForm.svelte";
  import MiscForm from "./MiscForm.svelte";
  import ShareList from "./ShareList.svelte";

  export let type;
  export let id = null;

  const dispatch = createEventDispatcher();

  let item = {};
  let loading = !!id;
  let shares = [];
  let parentIp = '';
  let parentHostname = '';

  const FORMS = {
    hardware: HardwareForm,
    vms: VmForm,
    apps: AppForm,
    storage: StorageForm,
    networks: NetworkForm,
    misc: MiscForm,
  };

  $: FormComponent = FORMS[type];

  // ---- Unsaved changes: compare the form against a snapshot taken once it has rendered.
  // Empty values (null/undefined/"") are treated alike because forms normalise them on load.
  const IGNORED = new Set(["shares", "vms", "apps", "storage_pools", "created_at", "updated_at"]);
  let baseline = null;

  function snapshot(value) {
    return JSON.stringify(
      Object.keys(value)
        .filter((k) => !IGNORED.has(k) && value[k] !== null && value[k] !== undefined && value[k] !== "")
        .sort()
        .map((k) => [k, value[k]])
    );
  }

  async function resetBaseline() {
    await tick();
    // Forms fill in defaults after loading their dropdown options
    setTimeout(() => (baseline = snapshot(item)), 300);
  }

  $: if (baseline !== null) setDirty(snapshot(item) !== baseline);

  onDestroy(() => setDirty(false));

  async function cancel() {
    if (!(await confirmLeave())) return;
    dispatch("cancel");
    history.back();
  }

  onMount(async () => {
    if (id) {
      try {
        const res = await get(`/${type}/${id}`);
        item = res.data;
        if (type === 'storage' && item.shares) {
          shares = item.shares;
          
          if (item.hardware_id) {
            const hwRes = await get(`/hardware/${item.hardware_id}`);
            parentIp = hwRes.data.ip_address || '';
            parentHostname = hwRes.data.hostname || '';
          } else if (item.vm_id) {
            const vmRes = await get(`/vms/${item.vm_id}`);
            parentIp = vmRes.data.ip_address || '';
            parentHostname = vmRes.data.hostname || '';
          }
        }
      } catch (e) {
        addToast(e.message, "error");
      }
      loading = false;
    }
    resetBaseline();
  });

  async function handleSubmit() {
    try {
      if (id) {
        await put(`/${type}/${id}`, item);
        addToast($t("toast.updated"), "success");
      } else {
        await post(`/${type}`, item);
        addToast($t("toast.created"), "success");
      }
      baseline = snapshot(item);
      setDirty(false);
      refreshStatus();
      dispatch("saved");
    } catch (e) {
      addToast(e.message, "error");
    }
  }

  async function handleShareSave(event) {
    try {
      const shareData = event.detail;
      
      if (shareData.id) {
        await put(`/shares/${shareData.id}`, shareData);
        addToast($t("shares.updated"), "success");
      } else {
        await post('/shares', shareData);
        addToast($t("shares.created"), "success");
      }
      
      const res = await get(`/${type}/${id}`);
      item = res.data;
      shares = item.shares || [];
      baseline = snapshot(item);
    } catch (e) {
      addToast(e.message, "error");
    }
  }

  async function handleShareDelete(event) {
    try {
      const share = event.detail;
      await del(`/shares/${share.id}`);
      addToast($t("shares.deleted"), "success");
      
      const res = await get(`/${type}/${id}`);
      item = res.data;
      shares = item.shares || [];
      baseline = snapshot(item);
    } catch (e) {
      addToast(e.message, "error");
    }
  }
</script>

{#if loading}
  <p aria-busy="true">{$t("common.loading")}</p>
{:else}
  <form on:submit|preventDefault={handleSubmit}>
    <div class="detail-header">
      <h3>{$t(id ? "inventory.editTitle" : "inventory.newTitle", { type: $t(`typeSingular.${type}`) })}</h3>
      {#if id && ["hardware", "vms", "apps", "misc"].includes(type)}
        <StatusDot key="{type}-{id}" showLabel />
      {/if}
      {#if type === "apps" && appUrl(item)}
        <a class="outline" role="button" href={appUrl(item)} target="_blank" rel="noopener noreferrer">{$t("common.open")} ↗</a>
      {/if}
    </div>

    <svelte:component this={FormComponent} bind:item />

    <div class="form-actions">
      <button type="submit">{id ? $t("common.save") : $t("common.create")}</button>
      <button type="button" class="outline secondary" on:click={cancel}>
        {$t("common.cancel")}
      </button>
    </div>
  </form>
  
  {#if type === 'storage' && id}
    <ShareList 
      {shares}
      storageId={id}
      {parentIp}
      {parentHostname}
      on:save={handleShareSave}
      on:delete={handleShareDelete}
    />
  {/if}
{/if}

<style>
  .form-actions {
    display: flex;
    gap: 0.5rem;
    margin-top: 1rem;
  }
  form {
    max-width: 700px;
  }
  .detail-header {
    display: flex;
    align-items: center;
    gap: 1rem;
    flex-wrap: wrap;
    margin-bottom: 1rem;
  }
  .detail-header h3 {
    margin: 0;
  }
  .detail-header [role="button"] {
    padding: 0.3rem 0.8rem;
    font-size: 0.85rem;
  }
</style>
