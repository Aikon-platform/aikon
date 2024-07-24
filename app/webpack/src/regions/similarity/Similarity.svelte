<script>
    import { appLang } from '../../constants';
    import { similarityStore } from './similarityStore.js';
    const { fetchSimilarity } = similarityStore;
    import Table from "../../Table.svelte";
    import SimilarityPage from "./SimilarityPage.svelte";
    import SimilarityBtn from "./SimilarityBtn.svelte";
    import Toolbar from "./Toolbar.svelte";
</script>

<!--TODO add field with autocomplete to ask for similarity for a new witness-->
<!--TODO order similar witnesses according to a metric-->

<Toolbar/>

{#await fetchSimilarity}
    <Table>
        <tr class="faded is-center">
            {appLang === 'en' ? 'Retrieving similarities...' : 'Récupération des similarités...'}
        </tr>
    </Table>
{:then _}
    <SimilarityBtn/>
    <SimilarityPage/>
{:catch error}
    <Table>
        <tr class="faded is-center">
            Error when retrieving similarities: {error}
        </tr>
    </Table>
{/await}
