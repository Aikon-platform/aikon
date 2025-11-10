<script>
    import Region from "../regions/Region.svelte";
    import LegendItem from "./LegendItem.svelte";

    export let selectedDocuments = [];
    export let documentSetStore;
    const {
        networkStats,
        allPairs,
        buildAlignedImageMatrix,
        regionsMetadata
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

    $: if (selectedDocuments.length > 0 && $networkStats && $allPairs) {
        const selectionOrder = selectedDocuments.map(n => n.id);
        const regionImages = $networkStats.documentNodes;
        matrixData = buildAlignedImageMatrix(selectionOrder, regionImages, $allPairs);

        console.log(matrixData, selectedDocuments, $networkStats, $allPairs);
    } else {
        matrixData = null;
    }

    function getImageColor(regionData, imageOccurrences) {
        if (!regionData) return undefined;
        const imgUrl = regionData.img;

        if (imageOccurrences.get(imgUrl) === 1) return undefined;
        if (!imageColorMap.has(imgUrl)) {
            imageColorMap.set(imgUrl, generateDistinctColor(imgUrl));
        }
        return imageColorMap.get(imgUrl);
    }

    const imageColorMap = new Map();

    $: imageOccurrences = matrixData ? (() => {
        const map = new Map();
        matrixData.rows.forEach(rowData => {
            Object.values(rowData).forEach(imgData => {
                map.set(imgData.img, (map.get(imgData.img) || 0) + 1);
            });
        });
        return map;
    })() : new Map();
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
                            <LegendItem id={regionId} meta={$regionsMetadata[regionId] || {}} clickable={false}/>
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
                                    {@const item = $networkStats.imageNodes.get(rowData[regionId].img)}
                                    <Region {item} selectable={false} copyable={false} borderColor={getImageColor(rowData[regionId], imageOccurrences)} isSquare={false}/>
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
