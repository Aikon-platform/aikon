<script>
    import { similarityStore } from "./similarityStore.js";
    const { setPageSImgs } = similarityStore;
    import SimilarRegion from "./SimilarRegion.svelte";
    export let appLang = 'en';
    export let qImg;

    const baseUrl = window.location.origin;

    async function fetchPageSimilarity(qImg) {
        await $setPageSImgs;

        const similarImgs = similarityStore.getSimilarImgs(qImg);
        const imgPairs = similarImgs.map(([sImg, _]) => `${qImg}|${sImg}`);

        const response = await fetch(`${baseUrl}/get-categories`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': CSRF_TOKEN
            },
            body: JSON.stringify({ img_pairs: imgPairs })
        });

        if (!response.ok) {
            throw new Error('Failed to fetch categories');
        }

        const categories = await response.json();

        return {
            similarImgs,
            categories
        };
    }

    let pageSimilarityPromise = fetchPageSimilarity(qImg);
</script>

{#await pageSimilarityPromise}
    <div class="faded is-center">
        {appLang === 'en' ? 'Retrieving similar regions...' : 'Récupération des régions similaires...'}
    </div>
{:then { similarImgs, categories }}
    {#each similarImgs as [sImg, score]}
        <SimilarRegion {qImg} {sImg} {score} {appLang} regionsCategory={categories[`${qImg}|${sImg}`]}/>
    {/each}
{:catch error}
    <div class="faded is-center">
        Error when retrieving similar regions: {error}
    </div>
{/await}
