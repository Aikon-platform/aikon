<script>
    import { onMount, getContext } from "svelte";

    import { csrfToken } from "../../constants";
    import SimilarRegions from "./SimilarRegions.svelte";
    import { similarityStore } from "./similarityStore.js";

    /** @typedef {import("./similarityStore").SelectedRegionsType} SelectedRegionsType*/

    /////////////////////////////////////////////

    export let qImg;
    let sImgsPromise;

    const isInModal = getContext("isInModal") || false;
    const { selectedRegions, comparedRegions } = similarityStore;
    const baseUrl = `${window.location.origin}${window.location.pathname}`;
    const currentPageId = window.location.pathname.match(/\d+/g).join("-");

    /////////////////////////////////////////////

    /**
     * if `_isInModal`, we retrieve similarities for all possible regions. else, only for regions defined by the user.
     * @param {SelectedRegionsType} selection
     * @param {boolean} _isInModal
     * @returns {number[]}
     */
    const getRegionsIds = (selection, _isInModal) =>
        _isInModal
        ? Object.keys($comparedRegions).map((k) => $comparedRegions[k].id)
        : Object.values(selection[currentPageId] || {}).map(r => r.id);

    /**
     * retrieve similar images to `qImg`
     * @param {String} qImg
     * @param {SelectedRegionsType} selection
     * @returns {Promise<array>}
     */
    async function fetchSImgs(qImg, selection, _isInModal) {
        const regionsIds = getRegionsIds(selection, _isInModal);
        if (regionsIds.length === 0) {
            return [];
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

    // in modals, we retrieve similarities for all possible regions. outside of modals, we retrieve similarities only for the user-defined regions.
    // => if !isInModal, listening to changes of `selectedRegions` is useless.
    if ( isInModal ) {
        sImgsPromise = fetchSImgs(qImg, $selectedRegions, isInModal);
    } else {
        selectedRegions.subscribe((newSelectedRegions) => {
            sImgsPromise = fetchSImgs(qImg, newSelectedRegions, isInModal);
        });
    }
</script>

<div>
    <SimilarRegions {qImg}
                    {sImgsPromise}
    ></SimilarRegions>
</div>

<style>
</style>
