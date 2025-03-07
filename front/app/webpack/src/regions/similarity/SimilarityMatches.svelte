<script>
    import { csrfToken } from '../../constants';
    import SimilarRegions from "./SimilarRegions.svelte";
    import { similarityStore } from "./similarityStore.js";

    const { selectedRegions, excludedCategories } = similarityStore;
    const baseUrl = `${window.location.origin}${window.location.pathname}`;
    const currentPageId = window.location.pathname.match(/\d+/g).join('-');

    // retrieve similar images from `qImg`
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


    export let qImg;
    $: sImgsPromise = fetchSImgs(qImg, $selectedRegions, $excludedCategories);
</script>

<div class="grid is-gap-2">
    <SimilarRegions {qImg} {sImgsPromise}></SimilarRegions>
</div>


<style>

</style>
