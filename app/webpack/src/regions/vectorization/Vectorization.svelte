<script>
    import { appLang } from '../../constants';
    import { vectorizationStore } from './vectorizationStore.js';
    const { fetchVectorization } = vectorizationStore;
    import VectorizationPage from "./VectorizationPage.svelte";
</script>

<!--todo au survol pouvoir choisir le type de chose qui s'affiche (juste le svg, juste l'image)-->

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
