<script>
    import { onMount } from 'svelte';
    import {appLang, modules} from '../../constants';
    import { similarityStore } from './similarityStore.js';
    // const fetchSimilarityScoreRange = similarityStore.fetchSimilarityScoreRange;
    import {errorMsg, loading} from "../../utils.js";

    import Table from "../../Table.svelte";
    import SimilarityPage from "./SimilarityPage.svelte";
    import SimilarityToolbar from "./SimilarityToolbar.svelte";

    const { fetchSimilarity, comparedRegions } = similarityStore;

    onMount(() => {
        if (modules.includes("similarity")){
            fetchSimilarity();
            // fetchSimilarityScoreRange();
        }
    });
</script>

<!--TODO add field with autocomplete to ask for similarity for a new witness-->
<!--TODO order similar witnesses according to a metric-->

{#if modules.includes("similarity")}
    {#if Object.keys($comparedRegions).length }
        <SimilarityToolbar></SimilarityToolbar>
    {/if}
    {#if $loading}
        <Table>
            <tr class="faded is-center">
                {appLang === 'en' ? 'Retrieving similarities...' : 'Récupération des similarités...'}
            </tr>
        </Table>
    {:else if $errorMsg}
        <Table>
            <tr class="faded is-center">
                {#if appLang === 'en'}
                    Error when retrieving similarities: {$errorMsg}
                {:else}
                    Erreur lors de la récupération des similarités : {$errorMsg}
                {/if}
            </tr>
        </Table>
    {:else}
        <SimilarityPage/>
    {/if}
{/if}
