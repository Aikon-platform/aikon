<script>
    import {similarityStore} from "./similarityStore.js";
    const { setPageSImgs } = similarityStore;
    import SimilarRegion from "./SimilarRegion.svelte";
    export let appLang = 'en';
    export let qImg;
</script>

{#await $setPageSImgs}
    <div class="faded is-center">
        {appLang === 'en' ? 'Retrieving similar regions...' : 'Récupération des régions similaires...'}
    </div>
{:then _}
    {#each similarityStore.getSimilarImgs(qImg) as [sImg, score]}
        <SimilarRegion {sImg} {score} {appLang}/>
    {/each}
{:catch error}
    <div class="faded is-center">
        Error when retrieving similar regions: {error}
    </div>
{/await}
