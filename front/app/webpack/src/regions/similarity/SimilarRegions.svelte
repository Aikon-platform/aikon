<script>
    import { getContext } from "svelte";

    import { appLang } from '../../constants';
    import { similarityStore } from "./similarityStore.js";
    import SimilarRegion from "./SimilarRegion.svelte";

    export let qImg;
    export let sImgsPromise;

    const {
        selectedRegions,
        excludedCategories,
        similarityScoreCutoff,
        propagateFilterByRegions
    } = similarityStore;

    const isPropagatedContext = getContext("similarityPropagatedContext") || false;  // true if it's a propagation, false otherwise
    const currentPageId = window.location.pathname.match(/\d+/g).join('-');

    let errorMsg;

    $: noRegionsSelected =
        Object.values($selectedRegions).length === 0
        || $selectedRegions[currentPageId] === undefined
        || !Object.keys($selectedRegions[currentPageId]).length;


    /** @type {"loading"|"loaded"|"error"} updated when `sImgsPromise` is updated */
    $: loadingStatus = "loading";

    /** @type {Array<{uuid:string, data: [score, img1, img2, region_1, region_2, category, users, isManual, similarityType]}>}
     * all similarity images, defined sImgsPromise is resolved and then updated each time a new `sImgsPromise` is passed by the parent */
    $: allSImgs = [];

    /** @type {Array<{uuid:string, data: Array}>} allSImgs filtered by displaySimImg, updated when one of `allSImgs`, `$excludedCategories`, `$similarityScoreCutoff`, `$propagateFilterByRegions` are updated */
    $: filteredSImgs = filterSImgs(
        allSImgs,
        $excludedCategories,
        $similarityScoreCutoff,
        $propagateFilterByRegions
    );

    /**
     * LIFECYCLE / PROPS UPDATE: how do we react to the update of `sImgsPromise` ?
     * `sImgsPromise` is updated by the parent
     *      => 1) global state resetting:
     *          - `loadingStatus` is set to "loading"
     *          - `filteredSImgs` is emptied (else, the screen would flicker, displaying 1st, the previous `filteredSImgs` (when `sImgsPromise` is resolved, but before ``). 2nd: the new `filteredSImgs`)
     *          - `allSImgs` is emptied
     *      => 2) `sImgsPromise` is resolved in this component. we update state:
     *          => `loadingStatus` is set to "loaded"
     *          => `allSImgs` is updated to store the resolved value of `sImgsPromise`
     *              => `filteredSImgs` is updated using the new `allSImgs`
     */
    // 1) reset state
    $: ((_) => {
        loadingStatus = "loading";
        filteredSImgs = [];
        allSImgs = [];
     })(sImgsPromise);

    // 2) update state when `sImgsPromise` is resolved
    $: sImgsPromise.then((res) => {
        allSImgs = res.map(el => ({
            uuid: window.crypto.randomUUID(),
            data: el
        }))
        loadingStatus = "loaded";
    }).catch((e) => {
        errorMsg = e;
        loadingStatus = "error";
    });

    //////////////////////////////

    /**
     * Returns true if the similarity image score is above the cutoff,
     * or if the score is null (for manual pairs),
     * or if the cutoff is undefined
     * @param {number|string} simImgScore
     * @param {number} cutoff
     */
    const isAboveCutoff = (simImgScore, cutoff) => simImgScore === null || cutoff === undefined || Number(simImgScore) >= cutoff;

    /**
     * @param {number} simImgCategory
     * @param {Array<number>} usersCategory
     * @param {Array<number>} _excludedCategories
     */
    const isNotInExcludedCategories = (simImgCategory, usersCategory, _excludedCategories) =>
        !_excludedCategories.includes(simImgCategory);

    /**
     * NOTE: the filtered images won't be updated if the user sets a category on a `SimilarRegion` until the next refresh.
     *
     * expected behaviour:
     *      the user sets a category => filters are recomputed and if the `SimilarRegion` belongs to one of $excludedCategories, the image is hidden for coherence.
     * current behaviour:
     *      categories set in `SimilarRegion` won't affect the filtering done by displaySimImg until the next reload.
     * explanation:
     *      fixing this would ask to re-fetch `sImgsPromise` from the backend: when setting a category in `SimilarRegion`, the database is updated, the object in `SimilarRegion` is updated, but the update is not transmitted to the parent (aka, the current component)
     *
     * @returns {boolean}
     */
    const displaySimImg = (
        simImgScore,
        simImgCategory,
        usersCategory,
        _excludedCategories,
        _similarityScoreCutoff,
        _propagateFilterByRegions
    ) => isPropagatedContext
        ? true
        : isAboveCutoff(simImgScore, _similarityScoreCutoff)
            && isNotInExcludedCategories(simImgCategory, usersCategory, _excludedCategories);


    /**  run `displaySimImg` to filter `_allSimgs` */
    const filterSImgs = (_allSImgs, _excludedCategories, _similarityScoreCutoff, _propagateFilterByRegions) =>
        _allSImgs.filter(({uuid, data: [score, _, sImg, qRegions, sRegions, category, users, isManual, similarityType]}) =>
            displaySimImg(
                score,
                category,
                users,
                _excludedCategories,
                _similarityScoreCutoff,
                _propagateFilterByRegions
            )
        );

    const getSimilarityLabel = (isPropagated, count) => {
        const isPlural = count > 1;

        if (isPropagated) {
            if (appLang === "fr") {
                return isPlural ? "similarités propagées" : "similarité propagée";
            } else {
                return isPlural ? "propagated matches" : "propagated match";
            }
        } else {
            if (appLang === "fr") {
                return isPlural ? "images similaires" : "image similaire";
            } else {
                return isPlural ? "similar images" : "similar image";
            }
        }
    };

</script>

{#if sImgsPromise && loadingStatus==="loading"}
    <div class="faded is-center">{
        appLang === 'en' && !isPropagatedContext
        ? 'Retrieving similar regions...'
        : appLang === 'fr' && !isPropagatedContext
        ? 'Récupération des régions similaires...'
        : appLang === 'en' && isPropagatedContext
        ? "Retrieving propagated regions..."
        : "Récupération de similarités propagées..."
    }</div>
{:else if loadingStatus === "loaded"}
    <div>
        <span class="m-2">{filteredSImgs.length} {getSimilarityLabel(isPropagatedContext, filteredSImgs.length)}</span>
        <div class="m-2 is-gap-2" class:grid={filteredSImgs.length > 0}>
            {#each filteredSImgs as {uuid, data: [score, _, sImg, qRegions, sRegions, category, users, isManual, similarityType]} (uuid)}
                <SimilarRegion {qImg} {sImg} {score} {qRegions} {sRegions} {category} {users} {isManual} {similarityType}/>
            {:else}
                {#if noRegionsSelected }
                    <div class="faded is-center">
                        {appLang === 'en' ? 'No document selected. Select one to display results.' : 'Aucun document sélectionné. Sélectionnez-en un pour afficher les résultats.'}
                    </div>
                {:else}
                    <div class="faded is-center">
                        {appLang === 'en' ? 'No similar regions' : 'Pas de régions similaires'}
                    </div>
                {/if}
            {/each}
        </div>
    </div>
{:else if loadingStatus==="error"}
    <div class="faded is-center">
        {
            appLang === 'en' ?
            `Error when retrieving similar regions: ${errorMsg}` :
            `Erreur de recupération des régions similaires: ${errorMsg}`
        }
    </div>
{/if}
