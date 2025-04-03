<script>
    import { setContext } from "svelte";

    import SimilarRegions from "./SimilarRegions.svelte";

    import { appLang, csrfToken } from '../../constants.js';
    import { similarityStore } from "./similarityStore";
    import { newAndOld, sameArrayScalar } from "../../utils";

    /** @typedef {import("./similarityStore").PropagateParamsType} PropagateParamsType */
    /** @typedef {import("../../utils").NewAndOldType} NewAndOldType */

    ////////////////////////////////////

    export let qImg;

    const { propagateParams, selectedRegions } = similarityStore;
    const baseUrl = `${window.location.origin}${window.location.pathname}`;
    const currentPageId = window.location.pathname.match(/\d+/g).join('-');

    let propagatedMatchesPromise;

    /** @type {NewAndOldType<PropagateParamsType>}*/
    const newAndOldPropagateParams = newAndOld.setCompareFn(sameArrayScalar);

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
        newAndOldPropagateParams
            .set(newPropagateParams.propagateRecursionDepth)
        if ( !newAndOld.same() ) {
            propagatedMatchesPromise =
                getPropagatedMatches(newPropagateParams.propagateRecursionDepth);
        }
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
