<script>
    import { similarityStore } from './similarityStore.js';
    import Pagination from "../Pagination.svelte";
    import Table from "../Table.svelte";
    import SimilarityRow from "./SimilarityRow.svelte";
    import SimilarRegion from "./SimilarRegion.svelte";
    const { fetchSimilarity, fetchSimilarityPage, nbOfPages, pageQImgs, getSimilarImg } = similarityStore;

    export let appLang = 'en';
</script>

<!--TODO display all compared witnesses-->
<!--TODO add field with autocomplete to ask for similarity for a new witness-->
<!--TODO make tag witnesses toggle for selection-->
<!--TODO toolbar -->
<!--TODO add all regions paginated + input to add new region-->
<!--TODO create category button for similarity-->
<!--TODO add button to add other similar region-->
<!--TODO order similar regions by category then score-->
<!--TODO add button to indicate that this is no similar regions-->
<!--TODO order similar witnesses according to a metric-->

<Pagination store={similarityStore} {$nbOfPages}/>

{#await fetchSimilarity}
    <Table>
        <tr class="faded is-center">
            {appLang === 'en' ? 'Retrieving similarities...' : 'Récupération des similarités...'}
        </tr>
    </Table>
{:then _}
    <Table>
        {#each Object.values($pageQImgs) as qImg (qImg.id)}
            <SimilarityRow {qImg} {appLang}>
                {#await fetchSimilarityPage}
                    <tr class="faded is-center">
                        {appLang === 'en' ? 'Retrieving similar regions...' : 'Récupération des régions similaires...'}
                    </tr>
                {:then _}
                    {#each $getSimilarImg(qImg) as [sImg, score]}
                        <SimilarRegion {sImg} {score} {appLang}/>
                    {/each}
                {:catch error}
                    <tr>Error when retrieving similar regions: {error}</tr>
                {/await}
            </SimilarityRow>
        {:else}
            <tr class="faded is-center">
                {appLang === 'en' ? 'No similarity' : 'Pas de similarités'}
            </tr>
            <!--TODO add button for launching new similarities-->
        {/each}
    </Table>
{:catch error}
    <Table>
        <tr>Error when retrieving similarities: {error}</tr>
    </Table>
{/await}
