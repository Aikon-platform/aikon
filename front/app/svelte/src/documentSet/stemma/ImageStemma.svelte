<!--
Propagation logic:
1. The startImageId (clicked line in the in the spatial frieze) determines the starting image placed at the base document node
2. We use Breadth-first search algorithm to browse the stemma, following all edges from the base node to build the complete graph structure
3. For each edge, look for the best matching pair between the current image and the neighbor document:
   - If multiple pairs exist, pick the one with the highest weightedScore
   - If no visible pair exists, it's a dead end for image propagation (node is displayed with a placeholder)
4. Continue to next generation: each resolved node becomes the new base for its unvisited neighbors
5. Repeat until all reachable nodes are visited

Special cases:
- Circular graphs: if multiple paths reach the same node, keep the pair with the highest score
-->

<script>
    import { derived } from "svelte/store";
    import {RegionItem} from "../../regions/types.js";
    import RegionModal from "../../regions/modal/RegionModal.svelte";
    import PageView from "../../regions/modal/PageView.svelte";
    import RegionCard from "../../regions/RegionCard.svelte";
    import Tabs from "../../ui/Tabs.svelte";
    import {appLang} from "../../constants.js";

    export let stemmaStore;
    export let visiblePairs;
    export let imageNodes;
    export let documents;
    export let startImageId;
    export let baseDocId;

    const { edges, nodePositions } = stemmaStore;

    const IMG_SIZE = 150;
    let modalOpen = false;
    let clickedRegionIdx = 0;
    $: visibleRegions = stemmaImages.nodes
      .filter(n => n.img)
      .map(n => new RegionItem(n.img));

    const clickOnImg = (node) => {
      if (!node.img){
        return
      }
      clickedRegionIdx = visibleRegions.findIndex(r => r.id === node.imageId);
      modalOpen = true;
    };

    const handleNavigate = (e) => {
      clickedRegionIdx = e.detail.index ?? 0;
    };

    const tabs = [
      { id: "region", label: appLang === "en" ? "Main view" : "Vue principale" },
      { id: "page", label: appLang === "en" ? "Page View" : "Vue de la page" },
    ];

    const pairIndex = derived(visiblePairs, $pairs => {
      const idx = new Map();
      for (const p of $pairs) {
        const key1 = `${p.regions_id_1}-${p.regions_id_2}`;
        const key2 = `${p.regions_id_2}-${p.regions_id_1}`;
        if (!idx.has(key1)) idx.set(key1, []);
        if (!idx.has(key2)) idx.set(key2, []);
        idx.get(key1).push(p);
        idx.get(key2).push(p);
      }
      return idx;
    });

    let stemmaImages = { nodes: [], edges: [] };

    $: stemmaImages = computeStemma($edges, $nodePositions, documents, $pairIndex, $imageNodes, startImageId, baseDocId);

    function computeStemma(edges, positions, docs, pairIdx, imgNodes, startImgId, baseId) {
      if (!startImgId || !baseId) return { nodes: [], edges: [] };

      const docMap = new Map(docs.map(n => [n.id, n]));
      const baseDoc = docMap.get(baseId);

      if (!edges.length) {
        if (!baseDoc) return { nodes: [], edges: [] };
        const img = imgNodes.get(startImgId);
        return {
          nodes: [{
            docId: baseId,
            imageId: startImgId,
            color: baseDoc.color,
            title: baseDoc.title,
            x: 20,
            y: 20,
            img
          }],
          edges: []
        };
      }

      const adjacency = new Map();
      for (const docId of docMap.keys()) adjacency.set(docId, []);
      for (const e of edges) {
        adjacency.get(e.source)?.push(e.target);
        adjacency.get(e.target)?.push(e.source);
      }

      // Propagate images via BFS until dead ends
      const resolved = new Map([[baseId, { imageId: startImgId, score: Infinity }]]);
      const queue = [baseId];
      const visited = new Set([baseId]);

      while (queue.length) {
        const currentDocId = queue.shift();
        const currentImgId = resolved.get(currentDocId).imageId;
        if (!currentImgId || !imgNodes.get(currentImgId)) continue;

        for (const neighborDocId of adjacency.get(currentDocId) || []) {
          const match = findBestMatch(currentImgId, currentDocId, neighborDocId, pairIdx);

          if (visited.has(neighborDocId)) {
            const existing = resolved.get(neighborDocId);
            if (match && (!existing.imageId || match.score > existing.score)) {
              resolved.set(neighborDocId, match);
            }
            continue;
          }

          visited.add(neighborDocId);
          resolved.set(neighborDocId, match || { imageId: null, score: -Infinity });
          if (match) queue.push(neighborDocId);
        }
      }

      // Add missing nodes from stemma graph
      for (const docId of docMap.keys()) {
        if (!resolved.has(docId)) {
          resolved.set(docId, { imageId: null, score: -Infinity });
        }
      }

      const nodes = [];
      let minX = Infinity, minY = Infinity;

      for (const [docId, { imageId }] of resolved) {
        const doc = docMap.get(docId);
        const pos = positions[docId] || { x: 0, y: 0 };
        if (!doc) continue;

        if (pos.x < minX) minX = pos.x;
        if (pos.y < minY) minY = pos.y;

        nodes.push({
          docId, imageId, color: doc.color, title: doc.title,
          x: pos.x, y: pos.y,
          img: imageId ? imgNodes.get(imageId) : null
        });
      }

      const padding = 20;
      for (const n of nodes) {
        n.x = n.x - minX + padding;
        n.y = n.y - minY + padding;
      }

      // All edges from stemma graph
      const nodeMap = new Map(nodes.map(n => [n.docId, n]));
      const renderedEdges = edges
        .map(e => {
          const src = nodeMap.get(e.source);
          const tgt = nodeMap.get(e.target);
          return src && tgt ? { source: src, target: tgt } : null;
        })
        .filter(Boolean);

      return { nodes, edges: renderedEdges };
    }

    function findBestMatch(imgId, fromDocId, toDocId, pairIdx) {
      const key = `${fromDocId}-${toDocId}`;
      const pairs = pairIdx.get(key) || [];

      let best = null;
      for (const p of pairs) {
        const isFrom1 = p.regions_id_1 === fromDocId && p.id_1 === imgId;
        const isFrom2 = p.regions_id_2 === fromDocId && p.id_2 === imgId;
        if (!isFrom1 && !isFrom2) continue;

        const matchedImgId = isFrom1 ? p.id_2 : p.id_1;
        if (!best || p.weightedScore > best.score) {
          best = { imageId: matchedImgId, score: p.weightedScore };
        }
      }
      return best;
    }

    function getImageUrl(img) {
      if (!img) return `https://placehold.co/${IMG_SIZE}x${IMG_SIZE}/png?text=No+image`;
      const regionItem = new RegionItem(img);
      return regionItem.url(null, `,${IMG_SIZE}`);
    }
</script>

<div class="image-stemma">
    {#if stemmaImages.nodes.length}
        <svg class="stemma-svg" viewBox="0 0 {Math.max(...stemmaImages.nodes.map(n => n.x)) + IMG_SIZE + 40} {Math.max(...stemmaImages.nodes.map(n => n.y)) + IMG_SIZE + 40}">
            <defs>
                <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
                    <polygon points="0 0, 10 3.5, 0 7" fill="var(--bulma-grey)" />
                </marker>
            </defs>

            {#each stemmaImages.edges as edge}
                <line
                    x1={edge.source.x + IMG_SIZE / 2}
                    y1={edge.source.y + IMG_SIZE}
                    x2={edge.target.x + IMG_SIZE / 2}
                    y2={edge.target.y}
                    stroke="var(--bulma-grey)"
                    stroke-width="5"
                    marker-end="url(#arrowhead)"
                />
            {/each}

            {#each stemmaImages.nodes as node (node.docId)}
                <g transform="translate({node.x}, {node.y})"
                    style="cursor: {node.img ? "pointer" : "default"}"
                    on:click={() => clickOnImg(node)}
                    on:keyup>
                    <rect
                        width={IMG_SIZE}
                        height={IMG_SIZE}
                        rx="4"
                        fill={node.color}
                        stroke="{node.color}"
                        stroke-width={node.docId === baseDocId ? 20 : 10}
                    />
                    <image href={getImageUrl(node.img)}
                        width={IMG_SIZE}
                        height={IMG_SIZE}
                        clip-path="inset(0 round 4px)"
                        preserveAspectRatio="xMidYMid slice"
                    />
                    <title>{node.title}</title>
                </g>
            {/each}
        </svg>
    {:else}
        <p class="has-text-grey is-size-7 p-3">Select an image in the frieze above</p>
    {/if}
</div>

<RegionModal items={visibleRegions} bind:currentIndex={clickedRegionIdx} bind:open={modalOpen} on:navigate={handleNavigate}>
    <svelte:fragment let:item={currentItem}>
        <Tabs {tabs} let:activeTab>
            {#if activeTab === "region"}
                <div class="modal-region">
                    <RegionCard item={currentItem} height="full" isInModal={true} selectable={false}/>
                </div>
            {:else if activeTab === "page"}
                <PageView item={currentItem}/>
            {/if}
        </Tabs>
    </svelte:fragment>
</RegionModal>

<style>
    .image-stemma {
        width: 100%;
        height: 100%;
        overflow: auto;
    }
    .stemma-svg {
        display: block;
        min-width: 100%;
        min-height: 200px;
    }
    .modal-region {
        height: 100%;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .modal-region :global(.region) {
        height: 100%;
    }
</style>
