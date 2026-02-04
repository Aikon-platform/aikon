<script>
    import { createEventDispatcher } from 'svelte';
    import { derived, writable } from 'svelte/store';
    import { i18n } from "../../utils.js";

    export let selectedNodes;
    export let visiblePairs;
    export let documentNodes;

    const dispatch = createEventDispatcher();

    const LINE_WIDTH = 5;
    const baseDocId = writable(null);
    const selectedImageId = writable(null);

    $: if ($selectedNodes.length && !$selectedNodes.find(n => n.id === $baseDocId)) {
        baseDocId.set($selectedNodes[0].id);
        selectedImageId.set(null);
    }

    const t = {
        base: { en: 'Pick a base document', fr: 'Sélectionner un document de base' },
    };

    const friezeData = derived(
        [selectedNodes, visiblePairs, documentNodes, baseDocId],
        ([$nodes, $pairs, $docs, $baseId]) => {
            if (!$nodes.length || !$docs.size || !$baseId) return { images: [], maxMatches: 0 };

            const baseDoc = $docs.get($baseId);
            if (!baseDoc?.images?.length) return { images: [], maxMatches: 0 };

            const otherDocIds = new Set($nodes.filter(n => n.id !== $baseId).map(n => n.id));
            if (!otherDocIds.size) {
                return {
                    images: baseDoc.images.map(img => ({ id: img.id, matchCount: 0 })),
                    maxMatches: 0
                };
            }

            const matchIndex = new Map();
            for (const p of $pairs) {
                const id1InBase = p.regions_id_1 === baseDoc.id;
                const id2InBase = p.regions_id_2 === baseDoc.id;
                if (!id1InBase && !id2InBase) continue;

                const baseImgId = id1InBase ? p.id_1 : p.id_2;
                const otherRegionId = id1InBase ? p.regions_id_2 : p.regions_id_1;

                if (!otherDocIds.has(otherRegionId)) continue;

                let entry = matchIndex.get(baseImgId);
                if (!entry) {
                    entry = new Map();
                    matchIndex.set(baseImgId, entry);
                }

                const existing = entry.get(otherRegionId);
                if (!existing || p.weightedScore > existing.score) {
                    entry.set(otherRegionId, { score: p.weightedScore });
                }
            }

            let maxMatches = 0;
            const images = baseDoc.images.map(img => {
                const matches = matchIndex.get(img.id);
                const matchCount = matches?.size || 0;
                if (matchCount > maxMatches) maxMatches = matchCount;
                return { id: img.id, matchCount };
            });

            return { images, maxMatches };
        }
    );

    function handleLineClick(imgId) {
        selectedImageId.set(imgId);
        dispatch('imageselect', { imageId: imgId, baseDocId: $baseDocId });
    }
</script>

<div class="frieze-container">
    {#if $friezeData.images.length}
        <div class="frieze" style="--line-width: {LINE_WIDTH}px;">
            {#each $friezeData.images as img (img.id)}
                <button
                    class="frieze-line"
                    class:is-selected={img.id === $selectedImageId}
                    style="--opacity: {$friezeData.maxMatches ? img.matchCount / $friezeData.maxMatches : 0}"
                    title="{img.matchCount} match(es)"
                    on:click={() => handleLineClick(img.id)}
                />
            {/each}
        </div>
        <div class="frieze-legend is-size-7 has-text-grey mt-2">
            <span>{$friezeData.images.length} images</span>
            <span class="mx-2">·</span>
            <span>Max {$friezeData.maxMatches} matches</span>
        </div>
    {:else}
        <p class="has-text-grey is-size-7">No base document selected</p>
    {/if}

    {#if $selectedNodes.length}
        <h4 class="title is-6 my-2">{i18n('base', t)}</h4>
        <div class="doc-selector mt-3">
            {#each $selectedNodes as node (node.id)}
                <button class="tag is-small" class:is-base={node.id === $baseDocId}
                    style="background-color: {node.color}; color: #222;" title={node.title}
                    on:click={() => { baseDocId.set(node.id); selectedImageId.set(null); }}>
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
    .frieze {
        display: flex;
        height: 60px;
        margin-top: 5px;
        background: var(--bulma-scheme-main-bis);
        border-radius: 4px;
        overflow: hidden;
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
