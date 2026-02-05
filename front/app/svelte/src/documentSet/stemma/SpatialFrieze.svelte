<script>
    import { createEventDispatcher } from 'svelte';
    import { derived, writable } from 'svelte/store';
    import { i18n } from "../../utils.js";

    export let selectedNodes;
    export let visiblePairs;
    export let documentNodes;
    export let mode = 'page';

    const dispatch = createEventDispatcher();

    const LINE_WIDTH = 5;
    const AXIS_HEIGHT = 20;

    const baseDocId = writable(null);
    const selectedIndex = writable(null);

    $: if ($selectedNodes.length && !$selectedNodes.find(n => n.id === $baseDocId)) {
        baseDocId.set($selectedNodes[0].id);
        selectedIndex.set(null);
    }

    $: if (mode) selectedIndex.set(null);

    const t = {
        base: { en: 'Pick a base document', fr: 'Sélectionner un document de base' },
    };

    const friezeData = derived(
        [selectedNodes, visiblePairs, documentNodes, baseDocId],
        ([$nodes, $pairs, $docs, $baseId]) => {
            if (!$nodes.length || !$docs.size || !$baseId) return null;

            const baseDoc = $docs.get($baseId);
            if (!baseDoc?.images?.length) return null;

            const images = baseDoc.images;
            const otherDocIds = new Set($nodes.filter(n => n.id !== $baseId).map(n => n.id));

            const imageMatchCount = new Map();
            for (const img of images) imageMatchCount.set(img.id, new Set());

            if (otherDocIds.size) {
                for (const p of $pairs) {
                    const id1InBase = p.regions_id_1 === baseDoc.id;
                    const id2InBase = p.regions_id_2 === baseDoc.id;
                    if (!id1InBase && !id2InBase) continue;

                    const baseImgId = id1InBase ? p.id_1 : p.id_2;
                    const otherRegionId = id1InBase ? p.regions_id_2 : p.regions_id_1;
                    if (!otherDocIds.has(otherRegionId)) continue;

                    imageMatchCount.get(baseImgId)?.add(otherRegionId);
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
                for (const docId of imageMatchCount.get(img.id) || []) {
                    pd.matchedDocs.add(docId);
                }
            }

            const imageItems = images.map(img => ({
                id: img.id,
                page: img.canvas,
                matchCount: imageMatchCount.get(img.id)?.size || 0
            }));

            const pageItems = [];
            for (let p = 1; p <= maxPage; p++) {
                const pd = pageData.get(p);
                pageItems.push({
                    page: p,
                    imageCount: pd?.images.length || 0,
                    matchCount: pd?.matchedDocs.size || 0,
                    images: pd?.images || []
                });
            }

            const maxImageMatches = Math.max(1, ...imageItems.map(i => i.matchCount));
            const maxPageMatches = Math.max(1, ...pageItems.map(p => p.matchCount));
            const maxImagesPerPage = Math.max(1, ...pageItems.map(p => p.imageCount));

            return {
                imageItems,
                pageItems,
                maxImageMatches,
                maxPageMatches,
                maxImagesPerPage,
                totalImages: images.length,
                totalPages: maxPage
            };
        }
    );

    $: items = $friezeData ? (mode === 'image' ? $friezeData.imageItems : $friezeData.pageItems) : [];
    $: maxVal = $friezeData ? (mode === 'image' ? $friezeData.maxImageMatches : $friezeData.maxPageMatches) : 1;
    $: axisMax = $friezeData ? (mode === 'image' ? $friezeData.totalImages : $friezeData.totalPages) : 0;

    function handleClick(index) {
        selectedIndex.set(index);
        if (mode === 'image') {
            const img = $friezeData.imageItems[index];
            dispatch('imageselect', {
                imageId: img.id,
                baseDocId: $baseDocId
            });
        } else {
            const pageItem = $friezeData.pageItems[index];
            dispatch('imageselect', {
                imageId: pageItem.images[0]?.id || null,
                baseDocId: $baseDocId,
                page: pageItem.page,
                images: pageItem.images
            });
        }
    }

    function getAxisTicks(max, targetCount = 10) {
        if (max <= targetCount) return Array.from({ length: max }, (_, i) => i + 1);
        const step = Math.ceil(max / targetCount);
        const ticks = [];
        for (let i = step; i <= max; i += step) ticks.push(i);
        if (ticks[ticks.length - 1] !== max) ticks.push(max);
        return ticks;
    }

    $: axisTicks = getAxisTicks(axisMax);
</script>

<div class="frieze-container">
    {#if $friezeData}
        {@const baseDoc = $documentNodes.get($baseDocId)}
        <div class="frieze-wrapper">
            <div class="frieze" style="--line-width: {LINE_WIDTH}px;">
                {#each items as item, idx}
                    <button
                        class="frieze-line"
                        class:is-selected={idx === $selectedIndex}
                        style="--opacity: {item.matchCount / maxVal}"
                        title="{mode === 'image' ? `Page ${item.page}, ` : ''}{item.matchCount} match(es)"
                        on:click={() => handleClick(idx)}
                    />
                {/each}
            </div>

            {#if mode === 'page'}
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

            <svg class="axis" height={AXIS_HEIGHT} style="width: {items.length * LINE_WIDTH}px;">
                <line x1="0" y1="0" x2="100%" y2="0" stroke="var(--bulma-border)" />
                {#each axisTicks as tick}
                    {@const x = (mode === 'image' ? tick - 0.5 : tick - 0.5) * LINE_WIDTH}
                    <line x1={x} y1="0" x2={x} y2="5" stroke="var(--bulma-border)" />
                    <text x={x} y="16" text-anchor="middle" class="axis-label">{tick}</text>
                {/each}
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

    {#if $selectedNodes.length}
        <h4 class="title is-6 my-2">{i18n('base', t)}</h4>
        <div class="doc-selector">
            {#each $selectedNodes as node (node.id)}
                <button class="tag is-small" class:is-base={node.id === $baseDocId}
                    style="background-color: {node.color}; color: #222;" title={node.title}
                    on:click={() => { baseDocId.set(node.id); selectedIndex.set(null); }}>
                    {node.title.length > 15 ? node.title.slice(0, 13) + '…' : node.title}
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
        width: 2000px; /* wider than real frieze to have background color all the way */
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
        height: 10px;
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
        font-size: 10px;
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
        transition: border-color 0.15s;
    }
    .doc-selector .tag.is-base {
        border-color: var(--bulma-link);
    }
</style>
