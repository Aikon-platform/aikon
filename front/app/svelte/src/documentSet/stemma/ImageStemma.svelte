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
    import { createEventDispatcher } from "svelte";
    import { derived } from "svelte/store";
    import {RegionItem} from "../../regions/types.js";
    import RegionModal from "../../regions/modal/RegionModal.svelte";
    import PageView from "../../regions/modal/PageView.svelte";
    import RegionCard from "../../regions/RegionCard.svelte";
    import RightClick from "../../ui/RightClick.svelte";
    import InputToggle from "../../ui/InputToggle.svelte";
    import StemmaModalEditor from "./StemmaModalEditor.svelte";
    import Tabs from "../../ui/Tabs.svelte";
    import { i18n } from "../../utils.js";
    import { createStemmaInteraction, createStemmaMenu } from "./stemmaInteraction.js";
    import QueryExpansionView from "../../regions/modal/QueryExpansionView.svelte";

    export let stemmaStore;
    export let visiblePairs;
    export let imageNodes;
    export let documents;
    export let startImageId = null;
    export let baseDocId = null;
    let startFromImage = false;

    const dispatch = createEventDispatcher();
    const { edges, nodePositions, nodeTitles, updateNodeTitle, updateEdgeLabel, addEdge } = stemmaStore;

    const interaction = createStemmaInteraction(stemmaStore);
    const { transform, dragOverride, drawingEdge } = interaction;
    interaction.enableEdgeDraw({ getNodeId: n => n.docId, documents });

    const tabs = [
        { id: "region", label: i18n("mainView") },
        { id: "page", label: i18n("pageView") },
        { id: "matches", label: i18n("matchesView") },
    ];

    const t = {
        select:    { en: "Select an image in the frieze", fr: "Sélectionner une image dans la frise" },
        openModal: { en: "Open detailed view", fr: "Ouvrir la vue détaillée" },
        setAnchor: { en: "Set as anchor", fr: "Définir comme ancre" },
        startFromImage: { en: "Suggest images", fr: "Images apparentées" },
        addToStemma: { en: "Add to document stemma", fr: "Ajouter au stemma" },
    };

    const ADD_TO_STEMMA_K = 1;

    const IMG_SIZE = 150;
    let svgEl, containerEl;
    let width = 800, height = 600;

    let editingNode = null;
    let editingEdge = null;

    const stemmaMenu = createStemmaMenu(stemmaStore, {
        onRename: node => editingNode = { id: node.docId, title: $nodeTitles[node.docId] || node.title, color: node.color },
        onEditEdge: edge => editingEdge = edge,
    });
    const { menu } = stemmaMenu;

    function openNodeMenu(e, node) {
        const noImg = !node.img;
        if (node.extra) {
            stemmaMenu.openNodeMenu(e, node, [
                { label: i18n("openModal", t), icon: "expand", disabled: noImg, action: () => openImg(node) },
            ], false);
            return;
        }
        const isAnchor = node.docId === baseDocId && node.imageId === startImageId;
        stemmaMenu.openNodeMenu(e, node, [
            { label: i18n("openModal", t), icon: "expand", disabled: noImg, action: () => openImg(node) },
            { label: i18n("setAnchor", t), icon: "anchor", disabled: noImg || isAnchor, action: () => dispatch("anchorselect", { imageId: node.imageId, baseDocId: node.docId }) },
        ]);
    }

    function openExtraEdgeMenu(e, edge) {
        e.preventDefault();
        const ex = edge.target, stem = edge.source;
        stemmaMenu.openNodeMenu(e, ex, [
            { label: i18n("addToStemma", t), icon: "code-branch", action: () =>
                addEdge(ex.docId, stem.docId, documents.find(d => d.id === ex.docId), documents.find(d => d.id === stem.docId)) },
        ], false);
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

    function orderRank(doc) {
        return [doc?.min_date ?? Infinity, doc?.title ?? "", doc?.id ?? Infinity];
    }
    function isEarlier(a, b) {
        const [da, ta, ia] = orderRank(a), [db, tb, ib] = orderRank(b);
        if (da !== db) return da < db;
        const c = ta.localeCompare(tb);
        return c !== 0 ? c < 0 : ia < ib;
    }

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
    $: stemmaImages = computeStemma($edges, $nodePositions, documents, $pairIndex, $imageNodes, startImageId, baseDocId, $nodeTitles, startFromImage);

    function computeStemma(edges, positions, docs, pairIdx, imgNodes, startImgId, baseId, titles, fromImage) {
        if (!startImgId || !baseId) return {nodes: [], edges: []};
        const docMap = new Map(docs.map(n => [n.id, n]));
        const baseDoc = docMap.get(baseId);
        const titleFor = id => titles[id] || docMap.get(id)?.title;

        const adjacency = new Map();
        for (const docId of docMap.keys()) adjacency.set(docId, []);
        if (!edges.length) {
            if (!baseDoc) return {nodes: [], edges: []};
            const img = imgNodes.get(startImgId);
            const base = {
                docId: baseId, id: baseId, imageId: startImgId,
                color: baseDoc.color, title: titleFor(baseId),
                ...(positions[baseId] || {x: 0, y: 0}), img, ...nodeDims(img)
            };
            const ex = fromImage ? extraImageNodes([base]) : {nodes: [], edges: []};
            return {nodes: [base, ...ex.nodes], edges: ex.edges};
        }
        for (const e of edges) {
            adjacency.get(e.source)?.push(e.target);
            adjacency.get(e.target)?.push(e.source);
        }

        const resolved = new Map([[baseId, {imageId: startImgId, score: Infinity, parent: null}]]);
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
                        const wasDeadEnd = !existing.imageId;
                        resolved.set(neighborDocId, {...match, parent: currentDocId});
                        if (wasDeadEnd) queue.push(neighborDocId);
                    }
                    continue;
                }

                visited.add(neighborDocId);
                resolved.set(neighborDocId, match ? {...match, parent: currentDocId} : {
                    imageId: null,
                    score: -Infinity,
                    parent: null
                });
                queue.push(neighborDocId);
            }
        }

        const nodes = [];
        for (const [docId, {imageId}] of resolved) {
            const doc = docMap.get(docId);
            if (!doc) continue;
            const pos = positions[docId] || {x: 0, y: 0};
            const img = imageId ? imgNodes.get(imageId) : null;
            nodes.push({
                docId, id: docId, imageId, color: doc.color, title: titleFor(docId),
                x: pos.x, y: pos.y, img, ...nodeDims(img)
            });
        }
        const extra = fromImage ? extraImageNodes(nodes) : {nodes: [], edges: []};
        nodes.push(...extra.nodes);

        const nodeMap = new Map(nodes.map(n => [n.docId, n]));
        const renderedEdges = edges.map(e => {
            const src = nodeMap.get(e.source), tgt = nodeMap.get(e.target);
            return src && tgt ? {source: src, target: tgt, label: e.label} : null;
        }).filter(Boolean);

        return {nodes, edges: [...renderedEdges, ...extra.edges]};

        function extraImageNodes(stemmaNodes) {
            const byImg = new Map(stemmaNodes.filter(n => n.imageId).map(n => [n.imageId, n]));
            const inStemma = new Set(stemmaNodes.map(n => n.docId));
            const found = new Map();
            for (const [, pairs] of pairIdx) for (const p of pairs) {
                const a = byImg.get(p.id_1), b = byImg.get(p.id_2);
                if (!a === !b) continue;
                const stem = a || b;
                const imageId = a ? p.id_2 : p.id_1;
                const docId = a ? p.digit_2 : p.digit_1;
                if (byImg.has(imageId) || inStemma.has(docId) || !docMap.has(docId)) continue;
                if (!found.has(imageId)) found.set(imageId, {docId, partners: new Map()});
                const partners = found.get(imageId).partners;
                if (!partners.has(stem.imageId) || partners.get(stem.imageId).score < p.weightedScore)
                    partners.set(stem.imageId, {node: stem, score: p.weightedScore});
            }

            // NOTE: extra images are located at their source-document position;
            //  NOTE: we keep only top-k = 1 to avoid a position collision.
            const bestPerDoc = new Map();
            for (const [imageId, {docId, partners}] of found) {
                const top = Math.max(...[...partners.values()].map(v => v.score));
                if (!bestPerDoc.has(docId) || bestPerDoc.get(docId).top < top)
                    bestPerDoc.set(docId, {imageId, partners, top});
            }

            const out = {nodes: [], edges: []};
            for (const [docId, {imageId, partners: partnerMap}] of bestPerDoc) {
                const partners = [...partnerMap.values()].sort((x, y) => y.score - x.score);
                const img = imgNodes.get(imageId);
                const pos = positions[docId] || {x: 0, y: 0};
                const node = {
                    docId,
                    id: docId,
                    imageId,
                    extra: true,
                    color: docMap.get(docId).color,
                    title: titleFor(docId),
                    x: pos.x,
                    y: pos.y,
                    img, ...nodeDims(img)
                };
                out.nodes.push(node);
                for (const {node: stem} of partners.slice(0, ADD_TO_STEMMA_K)) out.edges.push({
                    source: stem,
                    target: node,
                    extra: true
                });
            }
            return out;
        }
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
        return override?.docId === node.docId ? { ...node, x: override.x, y: override.y } : node;
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
             on:pointermove={interaction.onPointerMove} on:pointerup={interaction.onPointerUp}>
            <defs>
                <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
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
                    <g class="edge-group" on:contextmenu={e => edge.extra ? openExtraEdgeMenu(e, edge) : stemmaMenu.openEdgeMenu(e, edge)}>
                        <line class="edge-hit" {x1} {y1} {x2} {y2} stroke-width={10 / $transform.k}/>
                        <line class="edge" {x1} {y1} {x2} {y2}
                              stroke={edge.extra ? "transparent" : "var(--bulma-body-color)"}
                              stroke-width={2 / $transform.k}
                              marker-end={edge.extra ? null : "url(#arrowhead)"}/>
                    </g>
                    {#if edge.label}
                        <text x={(x1 + x2) / 2} y={(y1 + y2) / 2 - 4 / $transform.k}
                              font-size={10 / $transform.k} text-anchor="middle"
                              fill="var(--bulma-body-color)">{edge.label}</text>
                    {/if}
                {/each}

                {#if $drawingEdge}
                    {@const src = stemmaImages.nodes.find(n => n.docId === $drawingEdge.sourceId)}
                    {#if src}
                        <line x1={src.x + src.w/2} y1={src.y + src.h}
                              x2={$drawingEdge.x} y2={$drawingEdge.y}
                              stroke="var(--bulma-body-color)" stroke-width={2 / $transform.k}
                              stroke-dasharray="5,5"/>
                    {/if}
                {/if}

                {#each stemmaImages.nodes as node (node.id)}
                    {@const p = posOf(node, $dragOverride)}
                    <g data-node-id={node.docId}
                       transform="translate({p.x},{p.y})"
                       style="cursor: grab"
                       on:pointerdown={e => interaction.onPointerDown(e, node)}
                       on:contextmenu={e => openNodeMenu(e, node)}>
                        <rect width={node.w} height={node.h} rx="4"
                              fill={node.color} stroke={node.color}
                              stroke-width={node.imageId === startImageId && node.docId === baseDocId ? 20 : 10}/>
                        <image href={getImageUrl(node.img)}
                               width={node.w} height={node.h}
                               clip-path="inset(0 round 4px)"
                               preserveAspectRatio="xMidYMid meet"/>
                        <title>{node.title}</title>
                    </g>
                {/each}
            </g>
        </svg>
        <div class="toggle-btn">
            <InputToggle toggleLabel={i18n("startFromImage", t)} start={startFromImage} on:updateChecked={e => startFromImage = e.detail}/>
        </div>
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
            {:else if activeTab === "matches"}
                {#key currentItem.img}
                    <QueryExpansionView item={currentItem}/>
                {/key}
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
    .toggle-btn {
        position: absolute;
        top: 0.5rem;
        left: 0.5rem;
        cursor: pointer;
    }
</style>
