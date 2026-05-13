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
    import { onMount, createEventDispatcher } from "svelte";
    import { derived } from "svelte/store";
    import {RegionItem} from "../../regions/types.js";
    import RegionModal from "../../regions/modal/RegionModal.svelte";
    import PageView from "../../regions/modal/PageView.svelte";
    import RegionCard from "../../regions/RegionCard.svelte";
    import RightClick from "../../ui/RightClick.svelte";
    import StemmaModalEditor from "./StemmaModalEditor.svelte";
    import Tabs from "../../ui/Tabs.svelte";
    import { i18n } from "../../utils.js";
    import { createStemmaInteraction, createStemmaMenu } from "./stemmaInteraction.js";

    export let stemmaStore;
    export let visiblePairs;
    export let imageNodes;
    export let documents;
    export let startImageId = null;
    export let baseDocId = null;

    const dispatch = createEventDispatcher();
    const { edges, nodePositions, nodeTitles, updateNodeTitle, updateEdgeLabel } = stemmaStore;

    const interaction = createStemmaInteraction(stemmaStore);
    const { transform, dragOverride } = interaction;

    const tabs = [
        { id: "region", label: i18n("mainView") },
        { id: "page", label: i18n("pageView") },
    ];

    const t = {
        select:    { en: "Select an image in the frieze", fr: "Sélectionner une image dans la frise" },
        openModal: { en: "Open detailed view", fr: "Ouvrir la vue détaillée" },
        setAnchor: { en: "Set as anchor", fr: "Définir comme ancre" },
    };

    const IMG_SIZE = 150;
    let svgEl, containerEl;
    let width = 800, height = 600;

    let editingNode = null;
    let editingEdge = null;
    let editLabel = "";

    const stemmaMenu = createStemmaMenu(stemmaStore, {
        onRename: node => editingNode = { id: node.docId, title: $nodeTitles[node.docId] || node.title, color: node.color },
        onEditEdge: edge => editingEdge = edge,
    });
    const { menu } = stemmaMenu;

    function openNodeMenu(e, node) {
        const noImg = !node.img;
        const isAnchor = node.docId === baseDocId && node.imageId === startImageId;
        stemmaMenu.openNodeMenu(e, node, [
            { label: i18n("openModal", t), icon: "expand", disabled: noImg, action: () => openImg(node) },
            { label: i18n("setAnchor", t), icon: "anchor", disabled: noImg || isAnchor, action: () => dispatch("anchorselect", { imageId: node.imageId, baseDocId: node.docId }) },
        ]);
    }

    let attached = false;
    $: if (svgEl && !attached) {
        interaction.attach(svgEl);
        attached = true;
    }
    $: if (!stemmaImages.nodes.length) attached = false;

    let lastAnchorKey = null;
    $: {
        const key = `${startImageId}-${baseDocId}`;
        if (key !== lastAnchorKey && stemmaImages.nodes.length && svgEl) {
            interaction.positionCenter(stemmaImages.nodes, { nodeWidth: IMG_SIZE, nodeHeight: IMG_SIZE });
            lastAnchorKey = key;
        }
    }

    function onPointerDown(e, node) {
        if (interaction.startDrag(e, node)) {
            e.stopPropagation();
            svgEl.setPointerCapture(e.pointerId);
        }
    }
    function onPointerMove(e) { interaction.moveDrag(e); }
    function onPointerUp(e)   { interaction.endDrag(); svgEl.releasePointerCapture?.(e.pointerId); }

    let modalOpen = false;
    let clickedRegionIdx = 0;
    $: visibleRegions = stemmaImages.nodes.filter(n => n.img).map(n => new RegionItem(n.img));

    const openImg = (node) => {
        if (!node.img) return;
        clickedRegionIdx = visibleRegions.findIndex(r => r.id === node.imageId);
        modalOpen = true;
    };

    const handleNavigate = (e) => clickedRegionIdx = e.detail.index ?? 0;

    const pairIndex = derived(visiblePairs, $pairs => {
        const idx = new Map();
        for (const p of $pairs) {
            const key1 = `${p.digit_1}-${p.digit_2}`;
            const key2 = `${p.digit_2}-${p.digit_1}`;
            if (!idx.has(key1)) idx.set(key1, []);
            if (!idx.has(key2)) idx.set(key2, []);
            idx.get(key1).push(p);
            idx.get(key2).push(p);
        }
        return idx;
    });

    let stemmaImages = { nodes: [], edges: [] };
    $: stemmaImages = computeStemma($edges, $nodePositions, documents, $pairIndex, $imageNodes, startImageId, baseDocId, $nodeTitles);

    function computeStemma(edges, positions, docs, pairIdx, imgNodes, startImgId, baseId, titles) {
        if (!startImgId || !baseId) return { nodes: [], edges: [] };
        const docMap = new Map(docs.map(n => [n.id, n]));
        const baseDoc = docMap.get(baseId);
        const titleFor = id => titles[id] || docMap.get(id)?.title;

        if (!edges.length) {
            if (!baseDoc) return { nodes: [], edges: [] };
            const img = imgNodes.get(startImgId);
            return {
                nodes: [{
                    docId: baseId, imageId: startImgId,
                    color: baseDoc.color, title: titleFor(baseId),
                    x: 0, y: 0, img: img, ...nodeDims(img)
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

        for (const docId of docMap.keys()) {
            if (!resolved.has(docId)) resolved.set(docId, { imageId: null, score: -Infinity });
        }

        const nodes = [];
        for (const [docId, { imageId }] of resolved) {
            const doc = docMap.get(docId);
            const pos = positions[docId] || { x: 0, y: 0 };
            if (!doc) continue;
            const img = imageId ? imgNodes.get(imageId) : null
            nodes.push({
                docId, imageId, color: doc.color, title: titleFor(docId),
                x: pos.x, y: pos.y,
                img: img,
                ...nodeDims(img)
            });
        }

        const nodeMap = new Map(nodes.map(n => [n.docId, n]));
        const renderedEdges = edges
            .map(e => {
                const src = nodeMap.get(e.source);
                const tgt = nodeMap.get(e.target);
                return src && tgt ? { source: src, target: tgt, label: e.label } : null;
            })
            .filter(Boolean);

        return { nodes, edges: renderedEdges };
    }

    function findBestMatch(imgId, fromDocId, toDocId, pairIdx) {
        const key = `${fromDocId}-${toDocId}`;
        const pairs = pairIdx.get(key) || [];
        let best = null;
        for (const p of pairs) {
            const isFrom1 = p.digit_1 === fromDocId && p.id_1 === imgId;
            const isFrom2 = p.digit_2 === fromDocId && p.id_2 === imgId;
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
        return new RegionItem(img).url(null, `,${IMG_SIZE}`);
    }

    function posOf(node, override) {
        return override?.docId === node.docId ? override : node;
    }

    function saveTitle({ detail }) {
        if (detail.value) updateNodeTitle(editingNode.id, detail.value);
        editingNode = null;
    }

    function saveEdge({ detail }) {
        updateEdgeLabel(editingEdge.source.docId, editingEdge.target.docId, detail.value);
        editingEdge = null;
    }

    function nodeDims(img) {
        if (!img?.xywh) return { w: IMG_SIZE, h: IMG_SIZE };
        const [, , w, h] = img.xywh.map(Number);
        if (!w || !h) return { w: IMG_SIZE, h: IMG_SIZE };
        return w >= h
            ? { w: IMG_SIZE, h: IMG_SIZE * h / w }
            : { w: IMG_SIZE * w / h, h: IMG_SIZE };
    }
</script>

<div id="img-stemma" class="stemma-container" bind:this={containerEl} bind:clientWidth={width} bind:clientHeight={height} style={`height: ${stemmaImages.nodes.length ? "60vh" : "50px"}`}>
    {#if stemmaImages.nodes.length}
        <svg bind:this={svgEl} class="stemma-svg" viewBox="0 0 {width} {height}"
             on:pointermove={onPointerMove} on:pointerup={onPointerUp}>
            <defs>
                <marker id="img-arrow" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
                    <polygon points="0 0, 10 3.5, 0 7" fill="var(--bulma-body-color)"/>
                </marker>
            </defs>

            <g transform="translate({$transform.x},{$transform.y}) scale({$transform.k})">
                {#each stemmaImages.edges as edge}
                    {@const s = posOf(edge.source, $dragOverride)}
                    {@const t2 = posOf(edge.target, $dragOverride)}
                    {@const x1 = s.x + edge.source.w/2}
                    {@const y1 = s.y + edge.source.h}
                    {@const x2 = t2.x + edge.target.w/2}
                    {@const y2 = t2.y}
                    <g class="edge-group" on:contextmenu={e => stemmaMenu.openEdgeMenu(e, edge)}>
                        <line class="edge-hit" {x1} {y1} {x2} {y2} stroke-width={10 / $transform.k}/>
                        <line class="edge" {x1} {y1} {x2} {y2}
                              stroke="var(--bulma-body-color)" stroke-width={2 / $transform.k}
                              marker-end="url(#img-arrow)"/>
                    </g>
                    {#if edge.label}
                        <text x={(x1 + x2) / 2} y={(y1 + y2) / 2 - 4 / $transform.k}
                              font-size={10 / $transform.k} text-anchor="middle"
                              fill="var(--bulma-body-color)">{edge.label}</text>
                    {/if}
                {/each}

                {#each stemmaImages.nodes as node (node.docId)}
                    {@const p = posOf(node, $dragOverride)}
                    <g transform="translate({p.x},{p.y})"
                       style="cursor: grab"
                       on:pointerdown={e => onPointerDown(e, node)}
                       on:contextmenu={e => openNodeMenu(e, node)}>
                        <rect width={node.w} height={node.h} rx="4"
                              fill={node.color} stroke={node.color}
                              stroke-width={node.docId === baseDocId ? 20 : 10}/>
                        <image href={getImageUrl(node.img)}
                               width={node.w} height={node.h}
                               clip-path="inset(0 round 4px)"
                               preserveAspectRatio="xMidYMid meet"/>
                        <title>{node.title}</title>
                    </g>
                {/each}
            </g>
        </svg>
    {:else}
        <p class="has-text-grey is-size-6 p-3 mb-3">{i18n("select", t)}</p>
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

<RightClick bind:open={$menu.open} x={$menu.x} y={$menu.y} items={$menu.items}/>

{#key editingNode}
    <StemmaModalEditor type="node" target={editingNode} on:save={saveTitle} on:close={() => editingNode = null}/>
{/key}

{#key editingEdge}
    <StemmaModalEditor type="edge" target={editingEdge} on:save={saveEdge} on:close={() => editingEdge = null}/>
{/key}

<style>
    .stemma-container {
        position: relative;
        width: 100%;
    }
    .stemma-svg {
        width: 100%;
        height: 100%;
        position: absolute;
        inset: 0;
        background-color: var(--bulma-scheme-main-bis);
        border-radius: .5em;
        overflow: hidden;
    }
    .edge-group:hover .edge {
        stroke-width: 3;
    }
    .edge-hit {
        stroke: transparent;
        fill: none;
        cursor: pointer;
        pointer-events: stroke;
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
