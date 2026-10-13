<script>
  import { onMount, onDestroy } from "svelte";
  import cytoscape from "cytoscape";
  import dagre from "cytoscape-dagre";
  import { get, put } from "../../lib/api.js";
  import { addToast } from "../../lib/stores.js";
  import { statusMap } from "../../lib/status.js";
  import { t } from "../../lib/i18n.js";
  import NodeDetails from "./NodeDetails.svelte";

  cytoscape.use(dagre);

  let container;
  let cy;
  let saveTimeout;
  let networks = [];
  let selectedNode = null;
  let selectedNodeDetails = null;
  let loadingDetails = false;
  let tooltip = { visible: false, text: "", x: 0, y: 0 };
  
  // On phones the networks/filters panel would cover the map: it opens on demand
  let panelOpen = false;

  // Visibility toggles for each node type
  let showHardware = true;
  let showVms = true;
  let showApps = true;
  let showStorage = true;
  let showShares = true;
  let showMisc = true;

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

  $: if (selectedNode) {
    loadNodeDetails(selectedNode);
  } else {
    selectedNodeDetails = null;
    loadingDetails = false;
  }

  const EDGE_LABELS = ["hosts", "runs", "storage", "share"];

  const NODE_STYLES = {
    hardware:  { shape: "hexagon",          color: "#C5E1F5" },  // Pastel blue
    vms:       { shape: "ellipse",          color: "#C8E6C9" },  // Pastel green
    apps:      { shape: "round-rectangle", color: "#FFE0B2" },  // Pastel orange
    storage:   { shape: "barrel",           color: "#E1BEE7" },  // Pastel purple
    shares:    { shape: "round-tag",        color: "#FFF9C4" },  // Pastel yellow
    misc:      { shape: "diamond",          color: "#E0E0E0" },  // Light gray
  };

  onMount(async () => {
    try {
      const [graphRes, layoutRes, networksRes] = await Promise.all([
        get("/map/graph"),
        get("/map/layout"),
        get("/map/networks"),
      ]);

      const savedPositions = layoutRes.data || {};
      networks = networksRes.networks || [];

      // Apply saved positions to nodes
      const nodes = graphRes.nodes.map((n) => {
        const saved = savedPositions[n.data.id];
        if (saved) {
          n.position = { x: saved.x, y: saved.y };
          // Don't lock nodes - they should always be draggable
        }
        return n;
      });

      cy = cytoscape({
        container,
        elements: {
          nodes,
          // Relationship labels come from the backend in English ("hosts", "runs"...): translate the known ones
          edges: graphRes.edges.map((e) =>
            EDGE_LABELS.includes(e.data.label) ? { ...e, data: { ...e.data, label: $t(`map.edges.${e.data.label}`) } } : e
          ),
        },
        style: [
          {
            selector: "node",
            style: {
              label: "data(label)",
              "text-valign": "center",
              "text-halign": "center",
              "font-size": "7px",
              "font-weight": "400",
              "font-family": "system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif",
              "font-style": "italic",
              color: "#333",
              "text-outline-width": 0,
              width: 48,
              height: 48,
              "text-wrap": "wrap",
              "text-max-width": "65px",
              "background-color": "#FFFFFF",
              "border-width": 2,
              "border-color": "#999",
              "border-style": "solid",
            },
          },
          // Nodes with emoji icons - larger emoji only, no text, no italic
          {
            selector: "node[icon]:not([imageIcon])",
            style: {
              "font-size": "20px",
              "font-style": "normal",
              width: 52,
              height: 52,
            },
          },
          // Nodes with image icons - use background image
          {
            selector: "node[imageIcon]",
            style: {
              "background-image": "data(imageIcon)",
              "background-fit": "contain",
              "background-clip": "none",
              "background-width": "70%",
              "background-height": "70%",
              width: 48,
              height: 48,
              label: "",  // Hide label for image nodes
            },
          },
          // Per-type styles
          ...Object.entries(NODE_STYLES).map(([type, s]) => ({
            selector: `node[type="${type}"]`,
            style: {
              shape: s.shape,
              "background-color": s.color,
            },
          })),
          // Override color for nodes with network color
          {
            selector: "node[networkColor]",
            style: {
              "border-width": 3,
              "border-color": "data(networkColor)",
              "border-style": "solid",
            },
          },
          // Reachability overrides the network colour on the border
          {
            selector: 'node[status="up"]',
            style: { "border-width": 3, "border-color": "#22c55e" },
          },
          {
            selector: 'node[status="down"]',
            style: { "border-width": 4, "border-color": "#ef4444", "border-style": "double" },
          },
          {
            selector: "edge",
            style: {
              width: 2,
              "line-color": "#666",
              "target-arrow-color": "#666",
              "target-arrow-shape": "triangle",
              "curve-style": "bezier",
              label: "data(label)",
              "font-size": "9px",
              color: "#999",
              "text-rotation": "autorotate",
            },
          },
          {
            selector: "edge[?manual]",
            style: {
              "line-style": "dashed",
              "line-color": "#888",
            },
          },
          {
            selector: ".constraint-edge",
            style: {
              opacity: 0,  // Make invisible
              "z-index": -1,
            },
          },
        ],
        layout: { name: "preset" }, // Use saved positions first
        minZoom: 0.2,
        maxZoom: 3,
      });

      // If no saved positions, run dagre layout
      const hasSavedPositions = Object.keys(savedPositions).length > 0;
      if (!hasSavedPositions && nodes.length > 0) {
        runDagreLayout();
      }

      // Persist positions on drag end
      cy.on("dragfree", "node", () => {
        debounceSaveLayout();
      });

      // Show details on tap
      cy.on("tap", "node", (evt) => {
        const node = evt.target;
        selectedNode = node.data();
      });

      // Deselect when clicking background
      cy.on("tap", (evt) => {
        if (evt.target === cy) {
          selectedNode = null;
        }
      });

      // Show tooltip on hover
      cy.on("mouseover", "node", (evt) => {
        const node = evt.target;
        const renderedPosition = node.renderedPosition();
        tooltip = {
          visible: true,
          text: node.data("rawName") || node.data("label"),
          x: renderedPosition.x + 45,
          y: renderedPosition.y
        };
      });

      cy.on("mouseout", "node", () => {
        tooltip.visible = false;
      });
    } catch (e) {
      addToast($t("map.loadFailed", { error: e.message }), "error");
    }
  });

  // Push reachability into node data so the status styles apply
  $: if (cy) {
    cy.nodes().forEach((node) => {
      const info = $statusMap[node.id()];
      if (info) node.data("status", info.status);
      else node.removeData("status");
    });
  }

  // Reactive statement to hide/show nodes by type
  $: if (cy) {
    const nodeTypes = [
      { type: 'hardware', show: showHardware },
      { type: 'vms', show: showVms },
      { type: 'apps', show: showApps },
      { type: 'storage', show: showStorage },
      { type: 'shares', show: showShares },
      { type: 'misc', show: showMisc }
    ];
    
    nodeTypes.forEach(({ type, show }) => {
      const nodes = cy.nodes(`[type="${type}"]`);
      if (show) {
        nodes.show();
      } else {
        nodes.hide();
      }
    });
  }

  onDestroy(() => {
    if (cy) cy.destroy();
    clearTimeout(saveTimeout);
  });

  function runDagreLayout() {
    if (!cy) return;
    
    // Run initial dagre layout to establish vertical positioning (hierarchy)
    cy.layout({
      name: "dagre",
      rankDir: "TB",
      nodeSep: 20,
      rankSep: 100,
      ranker: "network-simplex",
      fit: false,
      padding: 30,
      animate: false,
    }).run();
    
    // Separate misc nodes from the main tree structure
    const miscNodes = cy.nodes().filter(node => node.data('type') === 'misc');
    const mainNodes = cy.nodes().filter(node => node.data('type') !== 'misc');
    
    // Find root nodes in main tree (nodes with no incoming edges, excluding misc)
    const roots = mainNodes
      .filter(node => node.indegree(false) === 0)
      .sort((a, b) => a.position().x - b.position().x);
    
    let nextX = 0;
    const nodeSpacing = 70; // Horizontal space between leaf nodes
    const subtreeGap = 50; // Gap between separate tree hierarchies
    
    // Depth-first layout: children are evenly spaced, parents centered above
    function layoutSubtree(node) {
      // Get direct children, sorted by their original position (excluding misc)
      const children = node.outgoers('node')
        .filter(n => n.data('type') !== 'misc')
        .sort((a, b) => a.position().x - b.position().x);
      
      if (children.length === 0) {
        // Leaf node - assign next available X position
        const x = nextX;
        nextX += nodeSpacing;
        node.position({ x, y: node.position().y });
        return x;
      }
      
      // Recursively layout all children depth-first
      const childXPositions = children.map(child => layoutSubtree(child));
      
      // Center this node over its children
      const avgX = childXPositions.reduce((sum, x) => sum + x, 0) / childXPositions.length;
      node.position({ x: avgX, y: node.position().y });
      
      return avgX;
    }
    
    // Layout each root tree
    roots.forEach((root, idx) => {
      if (idx > 0) {
        nextX += subtreeGap; // Add gap between separate trees
      }
      layoutSubtree(root);
    });
    
    // Center the main tree in viewport
    const mainX = mainNodes.map(n => n.position().x);
    const minMainX = Math.min(...mainX);
    const maxMainX = Math.max(...mainX);
    const mainWidth = maxMainX - minMainX;
    const centerShift = -(minMainX + maxMainX) / 2;
    
    mainNodes.forEach(node => {
      const pos = node.position();
      node.position({ x: pos.x + centerShift, y: pos.y });
    });
    
    // Layout misc nodes on the right in a compact grid
    if (miscNodes.length > 0) {
      const miscGap = 100; // Gap between main tree and misc section
      const miscStartX = maxMainX + centerShift + miscGap;
      const miscSpacingX = 80;
      const miscSpacingY = 80;
      const miscColumns = 2; // Number of columns for misc nodes
      
      // Sort misc nodes by their original Y position to maintain some order
      const sortedMisc = miscNodes.toArray().sort((a, b) => a.position().y - b.position().y);
      
      sortedMisc.forEach((node, idx) => {
        const col = idx % miscColumns;
        const row = Math.floor(idx / miscColumns);
        const x = miscStartX + col * miscSpacingX;
        const y = 100 + row * miscSpacingY; // Start from top
        node.position({ x, y });
      });
    }
    
    cy.fit(50);
  }

  function debounceSaveLayout() {
    clearTimeout(saveTimeout);
    saveTimeout = setTimeout(saveLayout, 500);
  }

  async function saveLayout() {
    if (!cy) return;
    const positions = {};
    cy.nodes().forEach((node) => {
      const pos = node.position();
      positions[node.id()] = { x: pos.x, y: pos.y, pinned: true };
    });
    try {
      await put("/map/layout", { positions });
    } catch (e) {
      // silent fail on layout save
    }
  }

  export function relayout() {
    runDagreLayout();
    setTimeout(saveLayout, 500);
  }
</script>

<div class="cy-container" bind:this={container}></div>

{#if tooltip.visible}
  <div class="node-tooltip" style="left: {tooltip.x}px; top: {tooltip.y}px;">
    {tooltip.text}
  </div>
{/if}

{#if selectedNode}
  <div class="info-panel">
    <div class="info-header">
      <h3>
        {#if selectedNode.icon}
          <span class="node-icon">{selectedNode.icon}</span>
        {/if}
        {selectedNode.rawName || selectedNode.label}
      </h3>
      <button class="close-btn" on:click={() => selectedNode = null} aria-label={$t("common.close")}>×</button>
    </div>
    <NodeDetails node={selectedNode} details={selectedNodeDetails} loading={loadingDetails} />
  </div>
{/if}

<button type="button" class="panel-toggle" aria-expanded={panelOpen} aria-controls="map-panel"
  on:click={() => (panelOpen = !panelOpen)}>{$t("map.filters")}</button>

<div class="networks-panel" id="map-panel" class:open={panelOpen}>
  <h3>{$t("types.networks")}</h3>
  {#if networks.length > 0}
    <div class="network-list">
      {#each networks as network}
        <div class="network-item">
          <span class="network-color" style="background-color: {network.color}"></span>
          <span class="network-name">{network.name}</span>
          {#if network.vlan_id}
            <span class="network-vlan">VLAN {network.vlan_id}</span>
          {/if}
        </div>
      {/each}
    </div>
  {:else}
    <p class="empty-state">{$t("map.noNetworks")}</p>
  {/if}
  
  <div class="panel-divider"></div>
  
  <h3>{$t("map.showInventory")}</h3>
  <div class="toggle-list">
    <label class="toggle-option">
      <input type="checkbox" bind:checked={showHardware} />
      <span>{$t("types.hardware")}</span>
    </label>
    <label class="toggle-option">
      <input type="checkbox" bind:checked={showVms} />
      <span>{$t("types.vms")}</span>
    </label>
    <label class="toggle-option">
      <input type="checkbox" bind:checked={showApps} />
      <span>{$t("types.apps")}</span>
    </label>
    <label class="toggle-option">
      <input type="checkbox" bind:checked={showStorage} />
      <span>{$t("types.storage")}</span>
    </label>
    <label class="toggle-option">
      <input type="checkbox" bind:checked={showShares} />
      <span>{$t("types.shares")}</span>
    </label>
    <label class="toggle-option">
      <input type="checkbox" bind:checked={showMisc} />
      <span>{$t("types.misc")}</span>
    </label>
  </div>
</div>

<div class="legend">
  <div class="legend-item">
    <svg width="24" height="24" viewBox="0 0 16 16">
      <polygon points="8,1 15,5 15,11 8,15 1,11 1,5" fill="#C5E1F5" stroke="#999" stroke-width="1"/>
    </svg>
    <span>{$t("types.hardware")}</span>
  </div>
  <div class="legend-item">
    <svg width="24" height="24" viewBox="0 0 16 16">
      <circle cx="8" cy="8" r="7" fill="#C8E6C9" stroke="#999" stroke-width="1"/>
    </svg>
    <span>{$t("types.vms")}</span>
  </div>
  <div class="legend-item">
    <svg width="24" height="24" viewBox="0 0 16 16">
      <rect x="2" y="2" width="12" height="12" rx="2" fill="#FFE0B2" stroke="#999" stroke-width="1"/>
    </svg>
    <span>{$t("types.apps")}</span>
  </div>
  <div class="legend-item">
    <svg width="24" height="24" viewBox="0 0 16 16">
      <ellipse cx="8" cy="3" rx="6" ry="2" fill="#E1BEE7" stroke="#999" stroke-width="1"/>
      <rect x="2" y="3" width="12" height="10" fill="#E1BEE7" stroke="none"/>
      <ellipse cx="8" cy="13" rx="6" ry="2" fill="#E1BEE7" stroke="#999" stroke-width="1"/>
      <line x1="2" y1="3" x2="2" y2="13" stroke="#999" stroke-width="1"/>
      <line x1="14" y1="3" x2="14" y2="13" stroke="#999" stroke-width="1"/>
    </svg>
    <span>{$t("types.storage")}</span>
  </div>
  <div class="legend-item">
    <svg width="24" height="24" viewBox="0 0 16 16">
      <polygon points="8,1 15,8 8,15 1,8" fill="#E0E0E0" stroke="#999" stroke-width="1"/>
    </svg>
    <span>{$t("types.misc")}</span>
  </div>
</div>

<style>
  .cy-container {
    width: 100%;
    height: 100%;
    min-height: 400px;
  }
  .info-panel {
    position: absolute;
    top: 0.75rem;
    left: 0.75rem;
    background: var(--hub-overlay-bg);
    padding: 0;
    border-radius: 6px;
    min-width: 280px;
    max-width: 350px;
    color: var(--hub-overlay-color);
    border: 1px solid var(--hub-border);
    box-shadow: var(--hub-shadow);
  }
  .info-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.75rem 1rem;
    border-bottom: 1px solid var(--hub-border);
  }
  .info-header h3 {
    margin: 0;
    font-size: 1rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }
  .node-icon {
    font-size: 1.5rem;
  }
  .close-btn {
    background: transparent;
    border: none;
    color: var(--hub-overlay-muted);
    font-size: 1.5rem;
    cursor: pointer;
    padding: 0;
    width: 24px;
    height: 24px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 3px;
    transition: all 0.2s;
  }
  .close-btn:hover {
    background: var(--hub-border);
    color: var(--hub-overlay-color);
  }
  .networks-panel {
    position: absolute;
    top: 0.75rem;
    right: 0.75rem;
    background: var(--hub-overlay-bg);
    padding: 0.75rem;
    border-radius: 6px;
    min-width: 200px;
    max-width: 300px;
    color: var(--hub-overlay-color);
  }
  .networks-panel h3 {
    margin: 0 0 0.75rem 0;
    font-size: 0.9rem;
    color: var(--hub-overlay-muted);
    border-bottom: 1px solid var(--hub-border);
    padding-bottom: 0.5rem;
  }
  .network-list {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }
  .network-item {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.85rem;
  }
  .network-color {
    width: 16px;
    height: 16px;
    border-radius: 3px;
    flex-shrink: 0;
    border: 1px solid var(--hub-border);
  }
  .network-name {
    flex: 1;
    font-weight: 500;
  }
  .network-vlan {
    font-size: 0.75rem;
    color: var(--hub-overlay-muted);
  }
  .empty-state {
    font-size: 0.8rem;
    color: var(--hub-overlay-muted);
    margin: 0;
    font-style: italic;
  }
  .panel-divider {
    height: 1px;
    background: var(--hub-border);
    margin: 0.75rem 0;
  }
  .toggle-list {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    margin-top: 0.5rem;
  }
  .toggle-option {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.85rem;
    cursor: pointer;
    color: var(--hub-overlay-muted);
    margin: 0;
  }
  .toggle-option input[type="checkbox"] {
    cursor: pointer;
    margin: 0;
  }
  .toggle-option:hover {
    color: var(--hub-overlay-color);
  }
  .legend {
    position: absolute;
    bottom: 0.75rem;
    left: 0.75rem;
    display: flex;
    gap: 1rem;
    background: var(--hub-overlay-bg);
    padding: 0.6rem 1rem;
    border-radius: 8px;
    font-size: 0.9rem;
    color: var(--hub-overlay-color);
  }
  .legend-item {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }
  .legend-item svg {
    flex-shrink: 0;
  }
  .node-tooltip {
    position: absolute;
    background: var(--hub-overlay-bg);
    color: var(--hub-overlay-color);
    padding: 0.4rem 0.7rem;
    border-radius: 4px;
    font-size: 0.85rem;
    pointer-events: none;
    z-index: 1000;
    white-space: nowrap;
    box-shadow: var(--hub-shadow);
    transform: translate(0, -50%);
  }
  .panel-toggle {
    display: none;
  }
  @media (max-width: 700px) {
    .panel-toggle {
      display: block;
      position: absolute;
      top: 0.5rem;
      right: 0.5rem;
      z-index: 5;
      width: auto;
      margin: 0;
      padding: 0.3rem 0.8rem;
      font-size: 0.85rem;
    }
    .networks-panel {
      display: none;
      top: 3rem;
      right: 0.5rem;
      left: 0.5rem;
      max-width: none;
      z-index: 5;
    }
    .networks-panel.open {
      display: block;
    }
    .info-panel {
      left: 0.5rem;
      right: 0.5rem;
      top: 0.5rem;
      min-width: 0;
      max-width: none;
      z-index: 6;
    }
    .legend {
      left: 0.5rem;
      right: 0.5rem;
      bottom: 0.5rem;
      flex-wrap: wrap;
      gap: 0.3rem 0.8rem;
      font-size: 0.75rem;
      padding: 0.4rem 0.6rem;
    }
  }
</style>
