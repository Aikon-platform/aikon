<script>
    import { csrfToken } from '../../constants';
    import SimilarRegions from "./SimilarRegions.svelte";
    import { similarityStore } from "./similarityStore.js";

    export let qImg;
    let sImgsPromise;

    const { updateSimilarity, similarityToolbarParams } = similarityStore;
    const baseUrl = `${window.location.origin}${window.location.pathname}`;
    const currentPageId = window.location.pathname.match(/\d+/g).join('-');

    /** retrieve similar images to `qImg` */
    async function fetchSImgs(qImg, selection, excludedCategories) {
        console.log("fetchSImgs called");
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

    updateSimilarity.subscribe((newVal) => {
        // TODO run only if selectedRegions OR excludedCategories change
        const selectedRegions = $similarityToolbarParams.similarity.regions;
        const excludedCategories = $similarityToolbarParams.similarity.excludedCategories;
        sImgsPromise = fetchSImgs(qImg, selectedRegions, excludedCategories)
    });
</script>

<div class="grid is-gap-2">
    <SimilarRegions {qImg}
                    {sImgsPromise}
                    displayType="similarityMatches"
    ></SimilarRegions>
</div>


<style>

</style>
