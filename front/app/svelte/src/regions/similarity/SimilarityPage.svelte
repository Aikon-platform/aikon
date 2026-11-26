<script>
    import { appLang } from "../../constants";
    import { similarityStore } from "./similarityStore.js";
    const { qImgs, pageQImgs, setPageQImgs, pageLength } = similarityStore;
    import Pagination from "../../Pagination.svelte";
    import Table from "../../Table.svelte";
    import SimilarityRow from "./SimilarityRow.svelte";

    export let witnessStore;
</script>


<div>
    <Pagination store={similarityStore} nbOfItems={$qImgs.length} {pageLength} />

    <Table>
        {#await $setPageQImgs}
            <tr class="faded is-center">
                <td>{appLang === "en"
                    ? "Retrieving similarity page..."
                    : "Récupération la page de similarité..."
                }</td>
            </tr>
        {:then _}
            {#each $pageQImgs as qImg (qImg.id)}
                <SimilarityRow {qImg} {witnessStore}/>
            {:else}
                <tr class="faded is-center">
                    <td>{appLang === "en" ? "No similarity" : "Pas de similarités"}</td>
                </tr>
                <!--TODO add button for launching new similarities-->
            {/each}
        {:catch error}
            <tr><td>Error when retrieving similar regions: {error}</td></tr>
        {/await}
    </Table>

    <Pagination store={similarityStore} nbOfItems={$qImgs.length} {pageLength} />
</div>
