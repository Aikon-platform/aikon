<script>
    import { appLang, csrfToken } from '../../constants';
    import { similarityStore } from "./similarityStore.js";
    const { selectedRegions, excludedCategories } = similarityStore;
    import SimilarRegion from "./SimilarRegion.svelte";

    export let qImg;
    const baseUrl = `${window.location.origin}${window.location.pathname}`;
    const currentPageId = window.location.pathname.match(/\d+/g).join('-');

    async function fetchSImgs(qImg, selection, excludedCategories) {
        const regionsIds = Object.values(selection).map(r => r.id);
        if (regionsIds.length === 0) {
            return {};
        }

        const response = await fetch(
            `${baseUrl}similar-images`,
            {
                method: "POST",
                body: JSON.stringify({
                    regionsIds: Object.values(selection[currentPageId]).map(r => r.id),
                    qImg: qImg,
                    topk: 10, // TODO retrieve this value from the user
                    excludedCategories: excludedCategories
                }),
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
            }
        );
        return await response.json()
    }

    $: sImgsPromise = fetchSImgs(qImg, $selectedRegions, $excludedCategories);
</script>

{#await sImgsPromise}
    <div class="faded is-center">
        {appLang === 'en' ? 'Retrieving similar regions...' : 'Récupération des régions similaires...'}
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
