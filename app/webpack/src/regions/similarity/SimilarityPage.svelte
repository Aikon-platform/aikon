<script>
    import { appLang } from '../../constants';
    import { similarityStore } from "./similarityStore.js";
    const { qImgs, pageQImgs, setPageQImgs, pageLength } = similarityStore;
    import Pagination from "../../Pagination.svelte";
    import Table from "../../Table.svelte";
    import SimilarityRow from "./SimilarityRow.svelte";
    import SimilarRegions from "./SimilarRegions.svelte";
</script>

<Pagination store={similarityStore} nbOfItems={$qImgs.length} {pageLength}/>

<Table>
    {#await $setPageQImgs}
        <tr class="faded is-center">
            {appLang === 'en' ? 'Retrieving similarity page...' : 'Récupération la page de similarité...'}
        </tr>
    {:then _}
        {#each $pageQImgs as qImg (qImg.id)}
            <SimilarityRow {qImg}>
                <SimilarRegions {qImg}/>
            </SimilarityRow>
        {:else}
            <tr class="faded is-center">
                {appLang === 'en' ? 'No similarity' : 'Pas de similarités'}
            </tr>
            <!--TODO add button for launching new similarities-->
        {/each}
    {:catch error}
        <tr>Error when retrieving similar regions: {error}</tr>
    {/await}
</Table>

<Pagination store={similarityStore} nbOfItems={$qImgs.length}/>
