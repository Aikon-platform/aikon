<script>
    import { appLang } from '../../constants';
    import { vectorizationStore } from './vectorizationStore.js';
    const { fetchVectorization } = vectorizationStore;
    import VectorizationPage from "./VectorizationPage.svelte";
</script>

<!--TODO choose what appear on hover: only svg, only image, etc-->
<!--TODO add button to download svg-->

{#await fetchVectorization}
    <div class="container faded is-center">
        {appLang === 'en' ? 'Retrieving vectorized regions...' : 'Récupération des régions vectorisées...'}
    </div>
{:then _}
    <VectorizationPage/>
{:catch error}
    <div class="container faded is-center">
        {#if appLang === 'en'}
            Error when retrieving vectorized regions: {error}
        {:else}
            Erreur lors de la récupération des régions vectorisées : {error}
        {/if}
    </div>
{/await}
