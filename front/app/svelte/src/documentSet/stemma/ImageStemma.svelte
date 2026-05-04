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
    import { onMount } from "svelte";
    import { derived } from "svelte/store";
    import {RegionItem} from "../../regions/types.js";
    import RegionModal from "../../regions/modal/RegionModal.svelte";
    import PageView from "../../regions/modal/PageView.svelte";
    import RegionCard from "../../regions/RegionCard.svelte";
    import RightClick from "../../ui/RightClick.svelte";
    import Tabs from "../../ui/Tabs.svelte";
    import {i18n} from "../../utils.js";
    import * as d3 from "d3";

    import { createEventDispatcher } from "svelte";
    const dispatch = createEventDispatcher();

    export let stemmaStore;
    export let visiblePairs;
    export let imageNodes;
    export let documents;
    export let startImageId = null;
    export let baseDocId = null;

    let menu = { open: false, x: 0, y: 0, items: [] };

    function onContextMenu(e, node) {
        e.preventDefault();
        const noImg = !node.img;
        const isAnchor = node.docId === baseDocId && node.imageId === startImageId;
        menu = {
            open: true, x: e.clientX, y: e.clientY,
            items: [
                { label: i18n("openModal", t), icon: "expand", disabled: noImg, action: () => openImg(node) },
                { label: i18n("setAnchor", t), icon: "anchor", disabled: noImg || isAnchor, action: () => dispatch("anchorselect", { imageId: node.imageId, baseDocId: node.docId }) },
            ]
        };
    }

    const { edges, nodePositions } = stemmaStore;
    const { updateNodePosition } = stemmaStore;

    const IMG_SIZE = 150;
    const DRAG_THRESHOLD = 3;

    let svgEl;
    let drag = null; // { node, startX, startY, originX, originY, moved }
    let dragOverride = null; // { docId, x, y } during drag for instant feedback

    let width = 800, height = 600;
    let transform = d3.zoomIdentity;
    let zoomBehavior;

    onMount(() => {
        zoomBehavior = d3.zoom()
            .scaleExtent([0.2, 5])
            .filter(e => !drag && e.type !== "contextmenu" && e.button === 0)
            .on("zoom", e => transform = e.transform);
        d3.select(svgEl).call(zoomBehavior);
    });

    // Fit content once when nodes first appear
    let fitted = false;
    $: if (!fitted && stemmaImages.nodes.length && svgEl && zoomBehavior) {
        fitContent();
        fitted = true;
    }
    $: if (!stemmaImages.nodes.length) fitted = false;

    function fitContent() {
        const xs = stemmaImages.nodes.map(n => n.x);
        const ys = stemmaImages.nodes.map(n => n.y);
        const minX = Math.min(...xs), minY = Math.min(...ys);
        const maxX = Math.max(...xs) + IMG_SIZE, maxY = Math.max(...ys) + IMG_SIZE;
        const w = maxX - minX, h = maxY - minY;
        const k = Math.min(width / (w + 80), height / (h + 80), 1);
        const tx = (width - w * k) / 2 - minX * k;
        const ty = (height - h * k) / 2 - minY * k;
        d3.select(svgEl).call(zoomBehavior.transform, d3.zoomIdentity.translate(tx, ty).scale(k));
    }

    // $: if (!fitted && stemmaImages.nodes.length && svgEl && zoomBehavior && width && height) {
    //     fitContent();
    //     fitted = true;
    // }

    let modalOpen = false;
    let clickedRegionIdx = 0;
    $: visibleRegions = stemmaImages.nodes
        .filter(n => n.img)
        .map(n => new RegionItem(n.img));

    const openImg = (node) => {
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
        { id: "region", label: i18n("mainView") },
        { id: "page", label: i18n("pageView") },
    ];

    const t = {
        select:    { en: "Select an image in the frieze", fr: "Sélectionner une image dans la frise" },
        openModal: { en: "Open detailed view", fr: "Ouvrir la vue détaillé" },
        setAnchor: { en: "Set as anchor", fr: "Définir comme ancre" },
    };

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

    $: stemmaImages = computeStemma($edges, $nodePositions, documents, $pairIndex, $imageNodes, startImageId, baseDocId);

    function computeStemma(edges, positions, docs, pairIdx, imgNodes, startImgId, baseId) {
        if (!startImgId || !baseId) return { nodes: [], edges: [] };
        const docMap = new Map(docs.map(n => [n.id, n]));
        const baseDoc = docMap.get(baseId);
        if (!edges.length) {
            if (!baseDoc) return { nodes: [], edges: [] };
            return {
                nodes: [{
                    docId: baseId,
                    imageId: startImgId,
                    color: baseDoc.color,
                    title: baseDoc.title,
                    x: 0, y: 0,
                    img: imgNodes.get(startImgId)
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
        for (const [docId, { imageId }] of resolved) {
            const doc = docMap.get(docId);
            const pos = positions[docId] || { x: 0, y: 0 };
            if (!doc) continue;
            nodes.push({
                docId, imageId, color: doc.color, title: doc.title,
                x: pos.x, y: pos.y,
                img: imageId ? imgNodes.get(imageId) : null
            });
        }

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
        const regionItem = new RegionItem(img);
        return regionItem.url(null, `,${IMG_SIZE}`);
    }

    function svgPoint(e) {
        const rect = svgEl.getBoundingClientRect();
        const x = (e.clientX - rect.left - transform.x) / transform.k;
        const y = (e.clientY - rect.top  - transform.y) / transform.k;
        return { x, y };
    }

    function onPointerDown(e, node) {
        if (e.button !== 0) return;
        e.stopPropagation();   // prevent d3-zoom from starting a pan
        const p = svgPoint(e);
        drag = { node, startX: p.x, startY: p.y, originX: node.x, originY: node.y, moved: false };
        svgEl.setPointerCapture(e.pointerId);
    }

    function onPointerMove(e) {
        if (!drag) return;
        const p = svgPoint(e);
        const dx = p.x - drag.startX, dy = p.y - drag.startY;
        if (!drag.moved && Math.hypot(dx, dy) < DRAG_THRESHOLD) return;
        drag.moved = true;
        dragOverride = { docId: drag.node.docId, x: drag.originX + dx, y: drag.originY + dy };
    }

    function onPointerUp(e) {
        if (!drag) return;
        if (drag.moved && dragOverride) {
            updateNodePosition(drag.node.docId, dragOverride.x, dragOverride.y);
        }
        svgEl.releasePointerCapture?.(e.pointerId);
        drag = null;
        dragOverride = null;
    }

    function posOf(node, _override) {
        return _override?.docId === node.docId ? _override : node;
    }
</script>

<div class="image-stemma" bind:clientWidth={width} bind:clientHeight={height}>
    {#if stemmaImages.nodes.length}
        <svg bind:this={svgEl} class="stemma-svg"
             viewBox="0 0 {width} {height}"
             on:pointermove={onPointerMove} on:pointerup={onPointerUp}>
            <defs>
                <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
                    <polygon points="0 0, 10 3.5, 0 7" fill="var(--bulma-grey)" />
                </marker>
            </defs>

            <g transform="translate({transform.x},{transform.y}) scale({transform.k})">
                {#each stemmaImages.edges as edge}
                    {@const s = posOf(edge.source, dragOverride)}
                    {@const t2 = posOf(edge.target, dragOverride)}
                    <line x1={s.x + IMG_SIZE/2} y1={s.y + IMG_SIZE}
                          x2={t2.x + IMG_SIZE/2} y2={t2.y}
                          stroke="var(--bulma-grey)" stroke-width="5"
                          marker-end="url(#arrowhead)"/>
                {/each}

                {#each stemmaImages.nodes as node (node.docId)}
                    {@const p = posOf(node, dragOverride)}
                    <g transform="translate({p.x},{p.y})"
                       style="cursor: {drag?.node.docId === node.docId ? 'grabbing' : 'grab'}"
                       on:pointerdown={e => onPointerDown(e, node)}
                       on:contextmenu={e => onContextMenu(e, node)}>
                        <rect width={IMG_SIZE} height={IMG_SIZE} rx="4"
                              fill={node.color} stroke={node.color}
                              stroke-width={node.docId === baseDocId ? 20 : 10}/>
                        <image href={getImageUrl(node.img)}
                               width={IMG_SIZE} height={IMG_SIZE}
                               clip-path="inset(0 round 4px)"
                               preserveAspectRatio="xMidYMid slice"/>
                        <title>{node.title}</title>
                    </g>
                {/each}
            </g>
        </svg>
    {:else}
        <p class="has-text-grey is-size-6 p-3 mb-3">
            {i18n("select", t)}
        </p>
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

<RightClick bind:open={menu.open} x={menu.x} y={menu.y} items={menu.items}/>

<style>
    .image-stemma {
        width: 100%;
        /*min-height: 60vh;*/
        height: 100%;
    }
    .stemma-svg {
        display: block;
        width: 100%;
        height: 100%;
        background-color: var(--bulma-scheme-main-bis);
        border-radius: .5em;
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
