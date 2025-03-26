<script>
    import { csrfToken } from '../../constants';
    import SimilarRegions from "./SimilarRegions.svelte";
    import { similarityStore } from "./similarityStore.js";

    export let qImg;
    let sImgsPromise;

    const { selectedRegions } = similarityStore;
    const baseUrl = `${window.location.origin}${window.location.pathname}`;
    const currentPageId = window.location.pathname.match(/\d+/g).join('-');

    /**
     * retrieve similar images to `qImg`
     * @param {String} qImg
     * @param {SelectedRegionsType} selection
     */
    async function fetchSImgs(qImg, selection) {
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
                }),
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
            }
        );
        return await response.json()
    }

    selectedRegions.subscribe((newSelectedRegions) => {
        sImgsPromise = fetchSImgs(qImg, newSelectedRegions)
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
