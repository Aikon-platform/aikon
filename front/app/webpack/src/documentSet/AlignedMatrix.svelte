<script>
    export let selectedDocuments = [];
    export let documentSetStore;
    const {
        networkStats,
        allPairs,
        regionsInfo,
        buildAlignedImageMatrix
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
    } else {
        matrixData = null;
    }

    function getImageColor(regionData, imageOccurrences) {
        if (!regionData) return "white";
        const imgUrl = regionData.img;

        if (imageOccurrences.get(imgUrl) === 1) return "white";
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
        <table class="table is-bordered is-fullwidth">
            <thead>
                <tr>
                    {#each matrixData.regions as regionId}
                        <th class="has-text-centered has-text-white"
                            style="background: {$regionsInfo[regionId]?.color || '#888888'}">
                            {$regionsInfo[regionId]?.title || `Region ${regionId}`}
                        </th>
                    {/each}
                </tr>
            </thead>
            <tbody>
                {#each matrixData.rows as rowData}
                    <tr>
                        {#each matrixData.regions as regionId}
                            <td class="has-text-centered" style="vertical-align: top; background: {getImageColor(rowData[regionId], imageOccurrences)}">
                                {#if rowData[regionId]}
                                    <img src={rowData[regionId].img} alt="Region {regionId}"
                                         style="width: 200px; height: auto; display: block; margin: 0 auto;">
                                    <div class="has-text-grey-dark mt-2" style="font-size: 12px">
                                        Page {rowData[regionId].page}
                                    </div>
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
</style>
