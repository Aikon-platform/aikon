<script>
    import { setContext, getContext } from "svelte";

    import SimilarRegions from "./SimilarRegions.svelte";

    import { csrfToken } from '../../constants.js';
    import { similarityStore } from "./similarityStore";
    import { createNewAndOld, equalArrayShallow } from "../../utils";

    /** @typedef {import("./similarityStore").PropagateParamsType} PropagateParamsType */
    /** @typedef {import("./similarityStore").SelectedRegionsType} SelectedRegionsType */
    /** @typedef {import("../../utils").NewAndOldType} NewAndOldType */

    ////////////////////////////////////

    export let qImg;

    const { propagateParams, selectedRegions } = similarityStore;
    const baseUrl = `${window.location.origin}${window.location.pathname}`;
    const currentPageId = window.location.pathname.match(/\d+/g).join('-');

    const isInModal = getContext("isInModal") || false;

    let propagatedMatchesPromise;

    /** @type {NewAndOldType}*/
    const newAndOldPropagateParams = createNewAndOld();
    newAndOldPropagateParams.setCompareFn((x,y) =>
        [x,y].every(_ =>
            _ && _.hasOwnProperty("propagateRecursionDepth") && _.hasOwnProperty("propagateFilterByRegions"))
        ? x.propagateRecursionDepth === y.propagateRecursionDepth
            && x.propagateFilterByRegions === y.propagateFilterByRegions
        : false
    );
    /** @type {NewAndOldType} */
    const newAndOldSelectedRegions = createNewAndOld();
    newAndOldSelectedRegions.setCompareFn(equalArrayShallow);

    /** @type {boolean} true if the child component inherits from PropagatedMatches, false otherwise. */
    setContext("similarityPropagatedContext", true);

    ////////////////////////////////////

    /**
     * extract regions ids for the selected regions of the current witness
     * @type {SelectedRegionsType} _selectedRegions
     * @returns {number[]|[]} the IDs of each regions
     */
    const getRegionsIds = (_selectedRegions) =>
        Object.keys(_selectedRegions).includes(currentPageId)
        ? Object.values(_selectedRegions[currentPageId]).map(v => v.id)
        : [];

    /**
     * if `isInModal`, no filtering by regions
     * @param {PropagateParamsType} _propagateParams
     * @param {number[]|[]} regionsForWitness regions to filter by
     * @param {boolean} _isInModal
     */
    const getPropagatedMatches = async (_propagateParams, regionsForWitness, _isInModal ) =>
        fetch(`${baseUrl}propagated-matches/${qImg}`, {
            method: "POST",
            body: JSON.stringify({
                regionsIds: _isInModal ? [] : regionsForWitness,
                filterByRegions: _isInModal ? false : _propagateParams.propagateFilterByRegions,
                recursionDepth: _propagateParams.propagateRecursionDepth
            }),
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            }
        })
        .then(r => r.json())
        .catch(e => {
            console.error("PropagatedMatches.getPropagatedMatches:", e);
            return []
        });

    ////////////////////////////////////

    // for some reason, grouping `propagateParams` and `selectedRegions` in a single derived doesn't work, so we use 2 subscribes instead
    propagateParams.subscribe((newPropagateParams) => {
        newAndOldPropagateParams.set(newPropagateParams);
        if ( !newAndOldPropagateParams.same() ) {
            propagatedMatchesPromise =
                getPropagatedMatches(newAndOldPropagateParams.get(), getRegionsIds($selectedRegions), isInModal);
        }
    })
    selectedRegions.subscribe((newSelectedRegions) => {
        newAndOldSelectedRegions.set(getRegionsIds(newSelectedRegions));
        if ( $propagateParams.propagateFilterByRegions === true && !newAndOldSelectedRegions.same() ) {
            propagatedMatchesPromise =
                getPropagatedMatches($propagateParams, newAndOldSelectedRegions.get(), isInModal);
        }
    })

</script>

<div class="block matches-suggestion-wrapper">
    <div class="matches-suggestion">
        <SimilarRegions qImg={qImg} sImgsPromise={propagatedMatchesPromise}/>
    </div>
</div>

<style>
    .matches-suggestion-wrapper {
        border: 1px solid var(--bulma-border);
        border-radius: 1em;
    }
    .matches-suggestion {
        margin: 1.5rem;
    }
</style>
