<script>
    import { similarityStore } from './similarityStore.js';
    const { fetchSimilarity } = similarityStore;
    import Table from "../../Table.svelte";
    import SimilarityPage from "./SimilarityPage.svelte";
    import SimilarityBtn from "./SimilarityBtn.svelte";

    export let appLang = 'en';
    export let imgPrefix = '';
    export let manifest = '';
</script>

<!--TODO add field with autocomplete to ask for similarity for a new witness-->
<!--TODO toolbar -->
<!--TODO add input to add new region-->
<!--TODO create category button for similarity-->
<!--TODO add button to add other similar region-->
<!--TODO order similar regions by category then score-->
<!--TODO add button to indicate that this is no similar regions-->
<!--TODO order similar witnesses according to a metric-->

{#await fetchSimilarity}
    <Table>
        <tr class="faded is-center">
            {appLang === 'en' ? 'Retrieving similarities...' : 'Récupération des similarités...'}
        </tr>
    </Table>
{:then _}
    <SimilarityBtn {appLang} {imgPrefix}/>
    <SimilarityPage {appLang} {manifest}/>
{:catch error}
    <Table>
        <tr class="faded is-center">
            Error when retrieving similarities: {error}
        </tr>
    </Table>
{/await}
