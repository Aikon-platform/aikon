<script>
    import { csrfToken } from "../../constants";
    import SimilarRegions from "./SimilarRegions.svelte";
    import { similarityStore } from "./similarityStore.js";

    /** @typedef {import("./similarityStore").SelectedRegionsType} SelectedRegionsType*/

    /////////////////////////////////////////////

    export let qImg;
    let sImgsPromise;

    const { selectedRegions } = similarityStore;
    const baseUrl = `${window.location.origin}${window.location.pathname}`;
    const currentPageId = window.location.pathname.match(/\d+/g).join("-");

    let totalQueries = 0;
    $: console.log(`totalQueries: ${totalQueries}`);

    /////////////////////////////////////////////

    /**
     * @param {SelectedRegionsType} selection
     * @returns {number[]}
     */
    const getRegionsIds = (selection) =>
        Object.values(selection[currentPageId] || {}).map(r => r.id);

    /**
     * retrieve similar images to `qImg`
     * @param {String} qImg
     * @param {SelectedRegionsType} selection
     */
    async function fetchSImgs(qImg, selection) {
        totalQueries += 1;

        const regionsIds = getRegionsIds(selection);
        if (regionsIds.length === 0) {
            return {};
        }
        const response = await fetch(`${baseUrl}similar-images`, {
            method: "POST",
            body: JSON.stringify({
                regionsIds: regionsIds,
                qImg: qImg,
                topk: 10, // TODO retrieve this value from the user
            }),
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": csrfToken,
            },
        });
        return await response.json();
    }

    /////////////////////////////////////////////

    selectedRegions.subscribe((newSelectedRegions) => {
        sImgsPromise = fetchSImgs(qImg, newSelectedRegions);
    });
</script>

<div class="grid is-gap-2">
    <SimilarRegions {qImg} {sImgsPromise} displayType="similarityMatches"
    ></SimilarRegions>
</div>

<style>
</style>
