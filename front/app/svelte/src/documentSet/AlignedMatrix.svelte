<script>
    import LegendItem from "./LegendItem.svelte";
    import RegionCard from "../regions/RegionCard.svelte";
    import RegionModal from "../regions/modal/RegionModal.svelte";
    import PageView from "../regions/modal/PageView.svelte";
    import Tabs from "../ui/Tabs.svelte";
    import {appLang} from "../constants.js";
    import { activeTab } from '../ui/tabStore.js';

    export let selectedDocuments = [];
    export let documentSetStore;
    const {
        buildAlignedImageMatrix,
        documentNodes,
        imageNodes,
    } = documentSetStore;

    function generateDistinctColor(str) {
        let hash = 0;
        for (let i = 0; i < str.length; i++) {
            hash = str.charCodeAt(i) + ((hash << 5) - hash);
            hash = hash & hash;
        }

        const goldenRatio = 0.618033988749895;
        const hue = ((hash * goldenRatio) % 1) * 360;
        const saturation = 65 + (hash % 20);
        const lightness = 80 + (hash % 10);

        return `hsl(${Math.floor(hue)}, ${saturation}%, ${lightness}%)`;
    }

    let matrixData = null;

    $: if (selectedDocuments.length > 0 && $imageNodes && $documentNodes) {
        const selectionOrder = selectedDocuments.map(n => n.id);
        matrixData = buildAlignedImageMatrix(selectionOrder);
    } else {
        matrixData = null;
    }

    function getImageColor(regionData, imageOccurrences) {
        if (!regionData) return undefined;
        const imgId = regionData.id;

        if (imageOccurrences.get(imgId) === 1) return undefined;
        if (!imageColorMap.has(imgId)) {
            imageColorMap.set(imgId, generateDistinctColor(imgId));
        }
        return imageColorMap.get(imgId);
    }

    const imageColorMap = new Map();

    $: imageOccurrences = matrixData ? (() => {
        const map = new Map();
        matrixData.rows.forEach(rowData => {
            Object.values(rowData).forEach(imgData => {
                map.set(imgData.id, (map.get(imgData.id) || 0) + 1);
            });
        });
        return map;
    })() : new Map();

    let modalOpen = false;
    let modalIndex = 0;
    $: modalItems = matrixData ? matrixData.rows.flatMap(rowData =>
        matrixData.regions.map(regionId => rowData[regionId])
            .filter(imgData => imgData)
            .map(imgData => $imageNodes.get(imgData.id))
    ) : [];
    const handleOpenModal = (e) => {
        modalIndex = e.detail.index ?? 0;
        modalOpen = true;
    };

    $: tabs = [
        { id: "region", label: appLang === "en" ? "Main view" : "Vue principale" },
        { id: "page", label: appLang === "en" ? "Page View" : "Vue de la page" },
    ];
</script>

{#if matrixData}
<div class="box mt-4">
    <h3 class="title is-5">Aligned Documents</h3>

    <div class="table-container">
        <table class="table is-fullwidth">
            <thead class="region-header">
                <tr>
                    {#each matrixData.regions as regionId}
                        <th class="is-vcentered">
                            <LegendItem id={regionId} meta={$documentNodes.get(regionId) || {}} clickable={false}/>
                        </th>
                    {/each}
                </tr>
            </thead>
            <tbody>
                {#each matrixData.rows as rowData}
                    <tr>
                        {#each matrixData.regions as regionId}
                            <td class="has-text-centered" style="vertical-align: top;">
                                {#if rowData[regionId]}
                                    {@const item = $imageNodes.get(rowData[regionId].id)}
                                    <RegionCard item={item} height={96} borderColor={getImageColor(rowData[regionId], imageOccurrences)}
                                                selectable={false} copyable={false}
                                                on:openModal={handleOpenModal}/>
                                    <div class="has-text-grey-dark mt-2">Page {rowData[regionId].page}</div>
                                {/if}
                            </td>
                        {/each}
                    </tr>
                {/each}
            </tbody>
        </table>
    </div>
</div>

<RegionModal items={modalItems} bind:currentIndex={modalIndex} bind:open={modalOpen}>
    <svelte:fragment let:item={currentItem}>
        <Tabs {tabs} let:activeTab>
            {#if activeTab === "region"}
                <div class="modal-region">
                    <RegionCard item={currentItem} height="full" isInModal={true}/>
                </div>
            {:else if activeTab === "page"}
                <PageView item={currentItem}/>
            {/if}
        </Tabs>
    </svelte:fragment>
</RegionModal>
{/if}

<style>
    .table-container {
        overflow-x: auto;
    }
    table {
        table-layout: fixed;
    }
    .region-header {
        border-color: var(--bulma-table-cell-border-color);
        border-style: var(--bulma-table-cell-border-style);
        border-width: 0 0 2px;
    }
</style>
