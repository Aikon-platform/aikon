<script>
    import { appLang } from '../../constants';
    import { vectorizationStore } from "./vectorizationStore.js";
    const { vectImgs, pageVectImgs, setPageVectImgs, pageLength } = vectorizationStore;
    import Pagination from "../../Pagination.svelte";

    console.log($vectImgs);
</script>

<Pagination store={vectorizationStore} nbOfItems={$vectImgs.length} {pageLength}/>

<div class="grid is-gap-2">
    {#await $setPageVectImgs}
        <tr class="faded is-center">
            {appLang === 'en' ? 'Retrieving vectorization page...' : 'Récupération la page de vectorisation...'}
        </tr>
    {:then _}
        {#each $pageVectImgs as vectImg (vectImg.id)}
            <p>{vectImg}</p>
        {:else}
            <tr class="faded is-center">
                {appLang === 'en' ? 'No vectorization' : 'Pas de vectorisation'}
            </tr>
            <!--TODO add button for launching vectorization-->
        {/each}
    {:catch error}
        <tr>Error when retrieving similar regions: {error}</tr>
    {/await}
</div>

<Pagination store={vectorizationStore} nbOfItems={$vectImgs.length} {pageLength}/>
