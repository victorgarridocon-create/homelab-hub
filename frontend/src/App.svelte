<script>
  import { onMount } from "svelte";
  import Router from "svelte-spa-router";
  import { wrap } from "svelte-spa-router/wrap";
  import Layout from "./components/Layout.svelte";
  import InventoryPage from "./pages/InventoryPage.svelte";
  import LoginPage from "./pages/LoginPage.svelte";
  import Toast from "./components/Toast.svelte";
  import DialogHost from "./components/DialogHost.svelte";
  import { session, checkSession } from "./lib/auth.js";
  import { startStatusPolling, stopStatusPolling } from "./lib/status.js";
  import { t } from "./lib/i18n.js";

  // Heavy pages (map: cytoscape, docs: editor...) load on first visit
  const lazy = (loader) => wrap({ asyncComponent: loader });

  const routes = {
    "/": lazy(() => import("./pages/DashboardPage.svelte")),
    "/inventory": InventoryPage,
    "/inventory/:type": InventoryPage,
    "/inventory/:type/:id": InventoryPage,
    "/map": lazy(() => import("./pages/MapPage.svelte")),
    "/ipam": lazy(() => import("./pages/IpamPage.svelte")),
    "/integrations": lazy(() => import("./pages/IntegrationsPage.svelte")),
    "/docs": lazy(() => import("./pages/DocsPage.svelte")),
    "/docs/:id": lazy(() => import("./pages/DocsPage.svelte")),
  };

  onMount(checkSession);

  $: if ($session.authenticated) startStatusPolling();
  else stopStatusPolling();
</script>

{#if !$session.checked}
  <p class="booting" aria-busy="true">{$t("common.loading")}</p>
{:else if !$session.authenticated}
  <LoginPage />
{:else}
  <Layout>
    <Router {routes} />
  </Layout>
{/if}
<Toast />
<DialogHost />

<style>
  .booting {
    padding: 2rem;
  }
</style>
