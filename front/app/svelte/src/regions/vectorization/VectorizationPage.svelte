<script>
    import { appLang } from '../../constants';
    import { vectorizationStore } from "./vectorizationStore.js";
    const { vectImgs, pageVectImgs, setPageVectImgs, pageLength } = vectorizationStore;
    import Pagination from "../../Pagination.svelte";
    import VectorizedRegions from "./VectorizedRegions.svelte";
    import ExportButtons from "./ExportButtons.svelte";
    let regionsRef = "";
</script>

<Pagination store={vectorizationStore} nbOfItems={$vectImgs.length} {pageLength}/>

<div class="grid is-gap-2 mx-5">
    {#await $setPageVectImgs}
        <div class="faded is-center">
            {appLang === 'en' ? 'Retrieving vectorization page...' : 'Récupération la page de vectorisation...'}
        </div>
    {:then _}
        {#each $pageVectImgs as vectImg (vectImg.id)}
            <VectorizedRegions svgPath={vectImg}/>
        {:else}
            <div class="faded is-center">
                {appLang === 'en' ? 'No vectorization' : 'Pas de vectorisation'}
            </div>
            <!--TODO add button for launching vectorization-->
        {/each}
    {:catch error}
        <div class="faded is-center">
            {#if appLang === 'en'}
                Error when retrieving vectorized regions: {error}
            {:else}
                Erreur lors de la récupération des régions vectorisées : {error}
            {/if}
        </div>
    {/await}
</div>

<Pagination store={vectorizationStore} nbOfItems={$vectImgs.length} {pageLength}/>

<style>
    .grid {
        --bulma-grid-column-min: 12rem;
    }
</style>
