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

    /** @type {PropagateParamsType|undefined}*/
    let oldPropagateParams;

    $: currentRegionIds = Object.values($selectedRegions[currentPageId] || {}).map(r => r.id)

    /** @type {boolean} true if the child component inherits from PropagatedMatches, false otherwise. */
    setContext("similarityPropagatedContext", true);

    ////////////////////////////////////

    /**
     * @param {number[]} recursionDepth
     */
    const getPropagatedMatches = async (recursionDepth) =>
        fetch(`${baseUrl}propagated-matches/${qImg}`, {
            method: "POST",
            body: JSON.stringify({
                regionsIds: [],
                filterByRegions: false,
                recursionDepth: recursionDepth
            }),
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },

        })
        .then(r => r.json())
        .catch(e => {
            console.error("PropagatedMatches.getPropagatedMatches:", e);
            return []
        });

    ////////////////////////////////////

    propagateParams.subscribe((newPropagateParams) => {
        let newDepth = newPropagateParams.propagateRecursionDepth,
            oldDepth = oldPropagateParams?.propagateRecursionDepth,
            sameDepth =
                Array.isArray(newDepth) && Array.isArray(oldDepth)
                && newDepth.length===oldDepth.length
                && newDepth.every((e, idx) => e === oldDepth[idx]||undefined);
        if ( !sameDepth ) {
            propagatedMatchesPromise =
                getPropagatedMatches(newPropagateParams.propagateRecursionDepth);
        }
        oldPropagateParams = newPropagateParams;
    })

    // selectedRegions.subscribe((newSelectedRegions) => {
    //     propagatedMatchesPromise = getPropagatedMatches(
    //         $propagateParams.propagateFilterByRegions,
    //         $propagateParams.propagateRecursionDepth,
    //         newSelectedRegions
    //     )
    // })
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
