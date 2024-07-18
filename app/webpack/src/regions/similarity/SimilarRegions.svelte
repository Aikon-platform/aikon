<script>
    import {appLang, csrfToken} from '../../constants';
    import { similarityStore } from "./similarityStore.js";
    const { selectedRegions } = similarityStore;
    import SimilarRegion from "./SimilarRegion.svelte";

    export let qImg;
    const baseUrl = `${window.location.origin}${window.location.pathname}`;

    async function fetchSImgs(qImg, selection) {
        const response = await fetch(
            `${baseUrl}similar-regions`,
            {
                method: "POST",
                body: JSON.stringify({
                    regionsIds: Object.values(selection).map(r => r.id),
                    qImg: qImg,
                    topk: 10, // TODO retrieve this value from the user
                    excludedCategories: [] // TODO retrieve this value from the toolbar
                }),
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
            }
        );
        return await response.json()
    }

    $: sImgsPromise = fetchSImgs(qImg, $selectedRegions);
</script>

{#await sImgsPromise}
    <div class="faded is-center">
        {appLang === 'en' ? 'Retrieving similar regions...' : 'Récupération des régions similaires...'}
    </div>
{:then simImgs}
    <!--TODO update on page change-->
    <!--TODO update with manually added Regions-->
    <!--TODO make querying by qImg instead of page-->
    <!--{#each Object.entries($pageSImgs) as [qImg, [score, _, sImg, qRegions, sRegions, category, users, isManual]]}-->
    <!--    <SimilarRegion {qImg} {sImg} {score} {qRegions} {sRegions} {category} {users} {isManual}/>-->
    <!--{/each}-->
    {#each simImgs as [score, _, sImg, qRegions, sRegions, category, users, isManual]}
        <SimilarRegion {qImg} {sImg} {score} {qRegions} {sRegions} {category} {users} {isManual}/>
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
