<script>
    import {regionsStore} from "./stores/regionsStore.js";
    const { pageRegions, fetchPages } = regionsStore;
    import Region from "./Region.svelte";
    import Pagination from "../Pagination.svelte";
    import RegionsRow from "./RegionsRow.svelte";
    import Table from "../Table.svelte";
    import ExtractionButtons from "./ExtractionButtons.svelte";

    export let appLang = 'en';
    export let manifest = '';
    export let nbOfPages = 1;
    export let modules = [];
    export let witness = {};
    export let isItemCopied;
    export let handleCopyRef;

    const zeros = (n, l) => n.toString().padStart(l, '0');
    function toImgName(canvasNb){
        return `${imgPrefix}_${zeros(canvasNb, String(nbOfPages).length + 1)}`;
    }
</script>

<Pagination store={regionsStore} nbOfItems={nbOfPages}/>

<Table>
    {#await $fetchPages}
        <tr class="faded is-center">
            {appLang === 'en' ? 'Retrieving paginated regions...' : 'Récupération des pages...'}
        </tr>
    {:then _}
        {#if Object.values($pageRegions).length > 0}
            <!--TODO make empty canvases appear-->
            {#each Object.entries($pageRegions) as [canvasNb, items]}
                <RegionsRow canvasImg={toImgName(canvasNb)} {canvasNb} {manifest}>
                    {#each Object.values(items) as item (item.id)}
                        <Region {item} {appLang} isSquare={false}
                                isCopied={isItemCopied(item)}
                                on:copyRef={handleCopyRef}/>
                    {/each}
                </RegionsRow>
            {/each}
        {:else}
            <tr>
                <ExtractionButtons {appLang} {modules} {witness}/>
            </tr>
        {/if}
    {:catch error}
        <tr class="faded is-center">
            {appLang === 'en' ? `Error when retrieving paginated regions: ${error}` : `Erreur de récupération des pages : ${error}`}
        </tr>
    {/await}
</Table>

<Pagination store={regionsStore} nbOfItems={nbOfPages}/>
