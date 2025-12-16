<script>
    import { getContext } from 'svelte';
    import { regionsStore } from "./regionsStore.js";
    const { pageRegions, fetchPages } = regionsStore;
    import Region from "./Region.svelte";
    import Pagination from "../Pagination.svelte";
    import Table from "../Table.svelte";
    import ExtractionButtons from "./ExtractionButtons.svelte";
    import { appLang } from '../constants';
    import {manifestToMirador, refToIIIF} from "../utils.js";
    import Row from "../Row.svelte";

    const nbOfPages = getContext('nbOfPages');
    const trailingZeros = getContext('trailingZeros');

    const zeros = (n, l) => n.toString().padStart(l, '0');
    function toImgName(canvasNb){
        // NOTE here sometimes the number of trailing zeros generated is not corresponding to the number of pages
        return `${imgPrefix}_${zeros(canvasNb, trailingZeros)}`;
    }
    const manifest = getContext('manifest');
</script>

<Pagination store={regionsStore} nbOfItems={nbOfPages}/>

<Table>
    {#await $fetchPages}
        <tr class="faded is-center">
            {appLang === 'en' ? 'Retrieving paginated regions...' : 'Récupération des pages...'}
        </tr>
    {:then _}
        {#if Object.values($pageRegions).length > 0}
            {#each Object.entries($pageRegions) as [canvasNb, items]}
                <Row>
                    <svelte:fragment slot="row-header">
                        <img src="{refToIIIF(toImgName(canvasNb), 'full', '250,')}" alt="Canvas {canvasNb}" class="mb-3 card">
                        <div class="is-center mb-1">
                            <a class="tag px-2 py-1 is-rounded is-hoverable" href="{manifestToMirador(manifest, canvasNb)}" target="_blank">
                                <i class="fa-solid fa-pen-to-square"></i>
                                Page {canvasNb}
                            </a>
                        </div>
                    </svelte:fragment>
                    <svelte:fragment slot="row-body">
                       {#each Object.values(items) as item (item.id)}
                            <Region {item} isSquare={true}/>
                        {/each}
                    </svelte:fragment>
                </Row>
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
