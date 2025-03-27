<script>
    import { setContext } from "svelte";

    import SimilarRegions from "./SimilarRegions.svelte";

    import { appLang, csrfToken } from '../../constants.js';
    import { similarityStore } from "./similarityStore";

    ////////////////////////////////////

    export let qImg;

    const { propagateParams, selectedRegions } = similarityStore;
    const baseUrl = `${window.location.origin}${window.location.pathname}`;
    const currentPageId = window.location.pathname.match(/\d+/g).join('-');

    let propagatedMatchesPromise;

    setContext("similarityPropagatedContext", true);  // bool. true if it's a propagated similarity match, false if it's any other match

    ////////////////////////////////////

    /**
     * @param {boolean} filterByRegions
     * @param {number[]} recursionDepth
     * @param {RegionsType} selection
     */
    const getPropagatedMatches = async (filterByRegions, recursionDepth, selection) =>
        fetch(`${baseUrl}propagated-matches/${qImg}`, {
            method: "POST",
            body: JSON.stringify({
                regionsIds: Object.values(selection[currentPageId]).map(r => r.id),
                filterByRegions: filterByRegions,
                recursionDepth: recursionDepth
            }),
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },

        })
        .then(r => r.json())
        .catch(e => {
            console.error("SimilarityMatchesPropagated.getPropagatedMatches:", e);
            return []
        })

        propagateParams.subscribe((newPropagateParams) => {
            propagatedMatchesPromise = getPropagatedMatches(
                newPropagateParams.filterByRegions,
                newPropagateParams.recursionDepth,
                $selectedRegions
            )
        })
        selectedRegions.subscribe((newSelectedRegions) => {
            propagatedMatchesPromise = getPropagatedMatches(
                $propagateParams.filterByRegions,
                $propagateParams.recursionDepth,
                newSelectedRegions
            )
        })
</script>

<div class="block matches-suggestion-wrapper">
    <div class="matches-suggestion">
        <div class="block">
            {#await propagatedMatchesPromise then propagatedImgs}
                {#if appLang==="fr"}
                    {propagatedImgs.length} {propagatedImgs.length > 1 ? "similarités propagées" : "similarité propagée" }
                {:else}
                    {propagatedImgs.length} propagated match{propagatedImgs.length > 1 ? "es" : "" }
                {/if}
            {/await}
        </div>
        <div class="grid is-gap-2">
            <SimilarRegions qImg={qImg}
                           sImgsPromise={propagatedMatchesPromise}
                           displayType="suggestionMatches"
            ></SimilarRegions>
        </div>
    </div>
</div>

<style type="text/css">
.matches-suggestion-wrapper {
    border: 1px solid var(--bulma-border);
    border-radius: 1em;
}
.matches-suggestion {
    margin: 1.5rem;
}
</style>
