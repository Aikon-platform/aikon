<script>
    import { getContext } from "svelte";

    import { appLang } from '../../constants';
    import { similarityStore } from "./similarityStore.js";
    const { selectedRegions } = similarityStore;
    import SimilarRegion from "./SimilarRegion.svelte";

    export let qImg;
    export let sImgsPromise;

    const similaritySuggestionContext = getContext("similaritySuggestionContext") || false;  // true if it's a suggestion, false otherwise
</script>

{#await sImgsPromise}
    <div class="faded is-center">
        { appLang === 'en' && !similaritySuggestionContext
        ? 'Retrieving similar regions...'
        : appLang === 'fr' && !similaritySuggestionContext
        ? 'Récupération des régions similaires...'
        : appLang === 'en' && similaritySuggestionContext
        ? "Retrieving propagated regions..."
        : "Récupération de similarités propagées..."
        }
    </div>
{:then simImgs}
    {#each simImgs as [score, _, sImg, qRegions, sRegions, category, users, isManual]}
        <SimilarRegion {qImg} {sImg} {score} {qRegions} {sRegions} {category} {users} {isManual}/>
    {:else}
        {#if Object.values($selectedRegions).length === 0}
            <div class="faded is-center">
                {appLang === 'en' ? 'No document selected' : 'Aucun document sélectionné'}
            </div>
        {:else}
            <div class="faded is-center">
                {appLang === 'en' ? 'No similar regions' : 'Pas de régions similaires'}
            </div>
        {/if}
    {/each}
{:catch error}
    <div class="faded is-center">
        {
            appLang === 'en' ?
            `Error when retrieving similar regions: ${error}` :
            `Erreur de recupération des régions similaires: ${error}`
        }
    </div>
{/await}
