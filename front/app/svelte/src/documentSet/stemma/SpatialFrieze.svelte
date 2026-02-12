<script>
    import { createEventDispatcher } from "svelte";
    import { derived, writable } from "svelte/store";
    import { i18n } from "../../utils.js";

    export let stemmaStore;
    export let documents;
    export let visiblePairs;
    export let documentNodes;
    export let mode = "page";

    const { nodeTitles } = stemmaStore;

    const dispatch = createEventDispatcher();

    const LINE_WIDTH = 5;
    const AXIS_HEIGHT = 20;

    const baseDocId = writable(null);
    const selectedIndex = writable(null);

    $: if (documents.length && !documents.find(n => n.id === $baseDocId)) {
        baseDocId.set(documents[0].id);
        selectedIndex.set(null);
    }

    $: if (mode) selectedIndex.set(null);

    const t = {
        base: { en: "Pick a base document", fr: "Sélectionner un document de base" },
        similarity: { en: "similarities", fr: "similarités" },
    };

    const documentsStore = writable([]);
    $: documentsStore.set(documents);
    const friezeData = derived(
        [documentsStore, visiblePairs, documentNodes, baseDocId],
        ([$nodes, $pairs, $docs, $baseId]) => {
            if (!$nodes.length || !$docs.size || !$baseId) return null;

            const baseDoc = $docs.get($baseId);
            if (!baseDoc?.images?.length) return null;

            const images = baseDoc.images;
            const otherDocIds = new Set($nodes.filter(n => n.id !== $baseId).map(n => n.id));

            const imageMatches = new Map();
            for (const img of images) imageMatches.set(img.id, new Set());

            if (otherDocIds.size) {
                for (const p of $pairs) {
                    const id1InBase = p.regions_id_1 === baseDoc.id;
                    const id2InBase = p.regions_id_2 === baseDoc.id;
                    if (!id1InBase && !id2InBase) continue;

                    const baseImgId = id1InBase ? p.id_1 : p.id_2;
                    const otherRegionId = id1InBase ? p.regions_id_2 : p.regions_id_1;
                    if (!otherDocIds.has(otherRegionId)) continue;

                    imageMatches.get(baseImgId)?.add(otherRegionId);
                }
            }

            const pageData = new Map();
            let maxPage = 0;

            for (const img of images) {
                const page = img.canvas;
                if (page > maxPage) maxPage = page;

                if (!pageData.has(page)) {
                    pageData.set(page, { images: [], matchedDocs: new Set() });
                }
                const pd = pageData.get(page);
                pd.images.push(img);
                for (const docId of imageMatches.get(img.id) || []) {
                    pd.matchedDocs.add(docId);
                }
            }

            const imageItems = images.map(img => ({
                id: img.id,
                page: img.canvas,
                matchedDocs: imageMatches.get(img.id) || new Set()
            }));
            imageItems.forEach(item => item.matchCount = item.matchedDocs.size);

            const pageItems = [];
            for (let p = 1; p <= maxPage; p++) {
                const pd = pageData.get(p);
                pageItems.push({
                    page: p,
                    imageCount: pd?.images.length || 0,
                    matchedDocs: pd?.matchedDocs || new Set(),
                    matchCount: pd?.matchedDocs.size || 0,
                    images: pd?.images || []
                });
            }

            const pageBoundaries = [];
            let currentPage = null, startIdx = 0;
            images.forEach((img, i) => {
                if (img.canvas !== currentPage) {
                    if (currentPage !== null) pageBoundaries.push({ page: currentPage, startIdx, endIdx: i });
                    currentPage = img.canvas;
                    startIdx = i;
                }
            });
            if (currentPage !== null) pageBoundaries.push({ page: currentPage, startIdx, endIdx: images.length });

            const maxImageMatches = Math.max(1, ...imageItems.map(i => i.matchCount));
            const maxPageMatches = Math.max(1, ...pageItems.map(p => p.matchCount));
            const maxImagesPerPage = Math.max(1, ...pageItems.map(p => p.imageCount));

            return {
                imageItems,
                pageItems,
                pageBoundaries,
                maxImageMatches,
                maxPageMatches,
                maxImagesPerPage,
                totalImages: images.length,
                totalPages: maxPage
            };
        }
    );

    $: items = $friezeData ? (mode === "image" ? $friezeData.imageItems : $friezeData.pageItems) : [];
    $: maxVal = $friezeData ? (mode === "image" ? $friezeData.maxImageMatches : $friezeData.maxPageMatches) : 1;

    let hoveredDocs = new Set();

    function handleClick(index) {
        selectedIndex.set(index);
        if (mode === "image") {
            const img = $friezeData.imageItems[index];
            dispatch("imageselect", { imageId: img.id, baseDocId: $baseDocId });
        } else {
            const pageItem = $friezeData.pageItems[index];
            const firstImg = pageItem.images[0];
            dispatch("imageselect", {
                imageId: firstImg?.id || null,
                baseDocId: $baseDocId,
                page: pageItem.page,
                images: pageItem.images
            });
        }
    }

    function handleMouseEnter(item) {
        hoveredDocs = item.matchedDocs;
    }

    function handleMouseLeave() {
        hoveredDocs = new Set();
    }

    function getAxisTicks(maxPage) {
        const ticks = [];
        for (let p = 50; p <= maxPage; p += 50) ticks.push(p);
        if (ticks.length === 0 || ticks[ticks.length - 1] !== maxPage) ticks.push(maxPage);
        return ticks;
    }

    $: axisTicks = $friezeData ? getAxisTicks($friezeData.totalPages) : [];
</script>

<div class="frieze-container">
    {#if $friezeData}
        {@const baseDoc = $documentNodes.get($baseDocId)}
        <h4 class="title is-6 mb-3">
            {baseDoc.title} {i18n("similarity", t)}
        </h4>
        {@const friezeWidth = items.length * LINE_WIDTH}
        <div class="frieze-wrapper">
            <div class="frieze" style="--line-width: {LINE_WIDTH}px;">
                {#each items as item, idx}
                    <button
                        class="frieze-line"
                        class:is-selected={idx === $selectedIndex}
                        style="--opacity: {item.matchCount / maxVal}"
                        title="{mode === "image" ? `Page ${item.page}, ` : `Page ${item.page}, `}{item.matchCount} match(es)"
                        on:click={() => handleClick(idx)}
                        on:mouseenter={() => handleMouseEnter(item)}
                        on:mouseleave={handleMouseLeave}
                    />
                {/each}
            </div>

            {#if mode === "page"}
                <div class="heatmap" style="--line-width: {LINE_WIDTH}px;">
                    {#each $friezeData.pageItems as item}
                        <div
                            class="heatmap-cell"
                            style="--opacity: {item.imageCount / $friezeData.maxImagesPerPage}; background-color: {baseDoc?.color}"
                            title="Page {item.page}: {item.imageCount} image(s)"
                        />
                    {/each}
                </div>
            {/if}

            <svg class="axis" height={AXIS_HEIGHT} style="width: {friezeWidth}px;">
                <line x1="0" y1="0" x2={friezeWidth} y2="0" stroke="var(--bulma-border)" />
                {#if mode === "page"}
                    {#each axisTicks as tick}
                        {@const x = (tick - 0.5) * LINE_WIDTH}
                        <line x1={x} y1="0" x2={x} y2="5" stroke="var(--bulma-border)" />
                        <text x={x} y="16" text-anchor="middle" class="axis-label">{tick}</text>
                    {/each}
                {:else}
                    {#each $friezeData.pageBoundaries as boundary}
                        {@const x = boundary.startIdx * LINE_WIDTH}
                        {#if boundary.page % 50 === 0 || boundary.page === $friezeData.totalPages}
                            <line x1={x} y1="0" x2={x} y2="5" stroke="var(--bulma-border)" />
                            <text x={x} y="16" text-anchor="middle" class="axis-label">{boundary.page}</text>
                        {/if}
                    {/each}
                {/if}
            </svg>
        </div>

        <div class="frieze-legend is-size-7 has-text-grey mt-2">
            <span>{$friezeData.totalImages} images</span>
            <span class="mx-2">·</span>
            <span>{$friezeData.totalPages} pages</span>
            <span class="mx-2">·</span>
            <span>Max {maxVal} matches</span>
        </div>
    {:else}
        <p class="has-text-grey is-size-7">No base document selected</p>
    {/if}

    {#if documents.length}
        <h4 class="title is-6 my-2">{i18n("base", t)}</h4>
        <div class="doc-selector">
            {#each documents as node (node.id)}
                {@const title = $nodeTitles[node.id] || node.title}
                <button class="tag is-small" title={title}
                    class:is-base={node.id === $baseDocId}
                    class:is-inactive={hoveredDocs.size > 0 && !hoveredDocs.has(node.id) && node.id !== $baseDocId}
                    style="background-color: {node.color}; color: #222;"
                    on:click={() => { baseDocId.set(node.id); selectedIndex.set(null); }}>
                    {title.length > 15 ? title.slice(0, 13) + "…" : title}
                </button>
            {/each}
        </div>
    {/if}
</div>

<style>
    .frieze-container {
        padding: 0.5rem;
    }
    .frieze-wrapper {
        overflow-x: auto;
        padding-top: 5px;
    }
    .frieze {
        display: flex;
        height: 60px;
        background: var(--bulma-scheme-main-bis);
        border-radius: 4px 4px 0 0;
    }
    .frieze-line {
        width: var(--line-width);
        flex-shrink: 0;
        border: none;
        padding: 0;
        cursor: pointer;
        background: color-mix(in srgb, var(--bulma-link) calc(var(--opacity) * 100%), transparent);
        transition: margin-top 0.1s, height 0.1s;
    }
    .frieze-line.is-selected {
        margin-top: -5px;
        height: calc(100% + 5px);
        background: var(--bulma-link);
    }
    .heatmap {
        display: flex;
        height: 8px;
    }
    .heatmap-cell {
        width: var(--line-width);
        flex-shrink: 0;
        opacity: var(--opacity);
    }
    .axis {
        display: block;
    }
    .axis-label {
        font-size: 9px;
        fill: var(--bulma-text-weak);
    }
    .frieze-legend {
        display: flex;
        justify-content: center;
    }
    .doc-selector {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
    }
    .doc-selector .tag {
        cursor: pointer;
        border: 2px solid transparent;
        transition: border-color 0.3s, opacity 0.3s, filter 0.3s;
    }
    .doc-selector .tag.is-base {
        border-color: var(--bulma-link);
    }
    .doc-selector .tag.is-inactive {
        opacity: 0.3;
        filter: grayscale(0.8);
    }
</style>
