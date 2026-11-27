<script>
    import { appLang } from "../../constants";
    import { similarityStore } from "./similarityStore.js";
    const { qImgs, pageQImgs, setPageQImgs, pageLength } = similarityStore;
    import Pagination from "../../Pagination.svelte";
    import Table from "../../Table.svelte";
    import SimilarityRow from "./SimilarityRow.svelte";

    let {witnessStore} = $props();
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
            <!-- `(i)` makes it a keyed each block, which allows dynamic
             updates when toolbar query parameters are updated (notably "Hidden categories").
             https://svelte.dev/docs/svelte/each#Keyed-each-blocks
            -->
            {#each $pageQImgs as qImg, i (i)}
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
