<script>
    import { getContext } from 'svelte';
    import { regionsStore } from "./regionsStore.js";
    const { pageRegionExtraction, fetchPages } = regionsStore;
    import Region from "./Region.svelte";
    import Pagination from "../Pagination.svelte";
    import RegionExtractionRow from "./RegionsRow.svelte";
    import Table from "../Table.svelte";
    import ExtractionButtons from "./ExtractionButtons.svelte";
    import { appLang } from '../constants';

    const nbOfPages = getContext('nbOfPages');
    const trailingZeros = getContext('trailingZeros');

    const zeros = (n, l) => n.toString().padStart(l, '0');
    function toImgName(canvasNb){
        // NOTE here sometimes the number of trailing zeros generated is not corresponding to the number of pages
        return `${imgPrefix}_${zeros(canvasNb, trailingZeros)}`;
    }
</script>

<Pagination store={regionsStore} nbOfItems={nbOfPages}/>

<Table>
    {#await $fetchPages}
        <tr class="faded is-center">
            {appLang === 'en' ? 'Retrieving paginated regions...' : 'Récupération des pages...'}
        </tr>
    {:then _}
        {#if Object.values($pageRegionExtraction).length > 0}
            {#each Object.entries($pageRegionExtraction) as [canvasNb, items]}
                <RegionExtractionRow canvasImg={toImgName(canvasNb)} {canvasNb}>
                    {#each Object.values(items) as item (item.id)}
                        <Region {item} isSquare={true} />
                    {/each}
                </RegionExtractionRow>
            {/each}
        {:else}
            <tr>
                <ExtractionButtons/>
            </tr>
        {/if}
    {:catch error}
        <tr class="faded is-center">
            {appLang === 'en' ? `Error when retrieving paginated regions: ${error}` : `Erreur de récupération des pages : ${error}`}
        </tr>
    {/await}
</Table>

<Pagination store={regionsStore} nbOfItems={nbOfPages}/>
