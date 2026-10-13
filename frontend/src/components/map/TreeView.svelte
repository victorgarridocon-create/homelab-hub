<script>
  import { onMount } from "svelte";
  import { get } from "../../lib/api.js";
  import TreeNode from "./TreeNode.svelte";
  import NodeDetails from "./NodeDetails.svelte";
  import { t } from "../../lib/i18n.js";

  let treeData = [];
  let loading = true;
  let expandedNodes = new Set();
  let selectedNode = null;
  let selectedNodeDetails = null;
  let loadingDetails = false;

  onMount(async () => {
    await loadTreeData();
  });

  async function loadTreeData() {
    loading = true;
    try {
      const graphRes = await get("/map/graph");
      const nodes = graphRes.nodes || [];
      const edges = graphRes.edges || [];
      
      // Build adjacency map
      const childrenMap = new Map();
      edges.forEach(edge => {
        const parentId = edge.data.source;
        const childId = edge.data.target;
        if (!childrenMap.has(parentId)) {
          childrenMap.set(parentId, []);
        }
        childrenMap.get(parentId).push(childId);
      });

      // Find root nodes (rank 0)
      const rootNodes = nodes.filter(n => n.data.rank === 0);
      
      // Build tree structure
      function buildTreeNode(nodeData) {
        const node = nodes.find(n => n.data.id === nodeData.data.id);
        const childIds = childrenMap.get(node.data.id) || [];
        const children = childIds.map(childId => {
          const childNode = nodes.find(n => n.data.id === childId);
          return buildTreeNode(childNode);
        });
        
        return {
          id: node.data.id,
          label: node.data.rawName || node.data.label,
          type: node.data.type,
          icon: node.data.icon,
          imageIcon: node.data.imageIcon,
          networkColor: node.data.networkColor,
          networkName: node.data.networkName,
          entity_id: node.data.entity_id,
          children
        };
      }

      treeData = rootNodes.map(buildTreeNode);
    } catch (e) {
      console.error('Failed to load tree data:', e);
    }
    loading = false;
  }

  function toggleNode(nodeId) {
    if (expandedNodes.has(nodeId)) {
      expandedNodes.delete(nodeId);
    } else {
      expandedNodes.add(nodeId);
    }
    expandedNodes = expandedNodes; // Trigger reactivity
  }

  function expandAll() {
    function collectIds(nodes) {
      const ids = [];
      nodes.forEach(node => {
        ids.push(node.id);
        if (node.children && node.children.length > 0) {
          ids.push(...collectIds(node.children));
        }
      });
      return ids;
    }
    expandedNodes = new Set(collectIds(treeData));
  }

  function collapseAll() {
    expandedNodes = new Set();
  }
  
  async function loadNodeDetails(node) {
    if (!node) return;
    loadingDetails = true;
    try {
      const response = await get(`/${node.type}/${node.entity_id}`);
      selectedNodeDetails = response.data;
    } catch (e) {
      console.error('Failed to load node details:', e);
      selectedNodeDetails = null;
    }
    loadingDetails = false;
  }
  
  function handleNodeClick(event) {
    selectedNode = event.detail;
    loadNodeDetails(selectedNode);
  }
  
  $: if (!selectedNode) {
    selectedNodeDetails = null;
    loadingDetails = false;
  }
</script>

<div class="tree-view">
  {#if loading}
    <div class="loading">{$t("map.loadingTree")}</div>
  {:else}
    <div class="tree-controls">
      <button class="outline secondary small" on:click={expandAll}>{$t("map.expandAll")}</button>
      <button class="outline secondary small" on:click={collapseAll}>{$t("map.collapseAll")}</button>
    </div>
    
    <div class="tree-container">
      {#each treeData as rootNode}
        <TreeNode 
          node={rootNode} 
          bind:expandedNodes 
          {selectedNode}
          on:toggle={(e) => toggleNode(e.detail)} 
          on:nodeclick={handleNodeClick}
          level={0} 
        />
      {/each}
    </div>
    
    {#if selectedNode}
      <div class="info-panel">
        <div class="info-header">
          <h3>
            {#if selectedNode.icon}
              <span class="node-icon">{selectedNode.icon}</span>
            {/if}
            {selectedNode.label}
          </h3>
          <button class="close-btn" on:click={() => selectedNode = null} aria-label={$t("common.close")}>×</button>
        </div>
        <NodeDetails node={selectedNode} details={selectedNodeDetails} loading={loadingDetails} />
      </div>
    {/if}
  {/if}
</div>

<style>
  .tree-view {
    height: 100%;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    background: var(--pico-background-color);
  }
  
  .loading {
    display: flex;
    align-items: center;
    justify-content: center;
    height: 100%;
    color: var(--pico-muted-color);
  }
  
  .tree-controls {
    display: flex;
    gap: 0.5rem;
    padding: 0.75rem;
    border-bottom: 1px solid var(--pico-muted-border-color);
  }
  
  .tree-controls button {
    margin: 0;
    padding: 0.25rem 0.75rem;
    font-size: 0.8rem;
  }
  
  .tree-container {
    flex: 1;
    overflow-y: auto;
    padding: 1rem;
  }
  
  .info-panel {
    position: fixed;
    top: 200px;
    right: 20px;
    width: 320px;
    background: var(--pico-card-background-color);
    border: 1px solid var(--pico-muted-border-color);
    border-radius: 8px;
    box-shadow: var(--hub-shadow);
    z-index: 1000;
    max-height: calc(100vh - 240px);
    display: flex;
    flex-direction: column;
  }
  
  .info-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem;
    border-bottom: 1px solid var(--pico-muted-border-color);
  }
  
  .info-header h3 {
    margin: 0;
    font-size: 1.1rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }
  
  .node-icon {
    font-size: 1.3rem;
  }
  
  .close-btn {
    background: none;
    border: none;
    color: var(--pico-muted-color);
    font-size: 1.5rem;
    cursor: pointer;
    padding: 0;
    width: 2rem;
    height: 2rem;
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 0;
  }
  
  .close-btn:hover {
    color: var(--pico-primary);
  }
  
</style>
