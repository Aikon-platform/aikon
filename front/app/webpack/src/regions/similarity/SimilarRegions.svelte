<script>
    import {getContext} from "svelte";

    import {appLang} from '../../constants';
    import {similarityStore} from "./similarityStore.js";
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
    const waitText =
        appLang === 'en' && !isPropagatedContext
            ? 'Retrieving similar regions...'
            : appLang === 'fr' && !isPropagatedContext
                ? 'Récupération des régions similaires...'
                : appLang === 'en' && isPropagatedContext
                    ? "Retrieving propagated regions..."
                    : "Récupération de similarités propagées...";

    $: noRegionsSelected =
        Object.values($selectedRegions).length === 0
        || $selectedRegions[currentPageId] === undefined
        || !Object.keys($selectedRegions[currentPageId]).length;

    /** @type {Array<{uuid:string, data: Array}>} all similarity images, defined when sImgsPromise is resolved */
    $: allSImgs = [];
    sImgsPromise.then((res) => {
        allSImgs = res.map(el => ({
            uuid: window.crypto.randomUUID(),
            data: el
        }))
    });

    /** @type {Array<{uuid:string, data: Array}>} allSImgs filtered by displaySimImg */
    $: filteredSImgs = filterSImgs(
        allSImgs,
        $selectedRegions,
        $excludedCategories,
        $similarityScoreCutoff,
        $propagateFilterByRegions
    );


    //////////////////////////////

    /**
     * @param {number|string} simImgScore
     * @param {number} cutoff
     */
    const isAboveCutoff = (simImgScore, cutoff) =>
        cutoff === undefined
            ? true
            : simImgScore != null && Number(simImgScore) >= cutoff;

    /**
     * @param {number} simImgCategory
     * @param {Array<number>} usersCategory
     * @param {Array<number>} _excludedCategories
     */
    const isNotInExcludedCategories = (simImgCategory, usersCategory, _excludedCategories) =>
        !_excludedCategories.includes(simImgCategory);

    /**
     * NOTE: the filtered images won't be updated if the user
     * sets a category on a `SimilarRegion` until the next refresh
     * expected behaviour
     *      the user sets a category => filters are
     *      recomputed and if the `SimilarRegion` belongs to one of
     *      $exludedCategories, the image is hidden for coherence.
     * current behaviour
     *      categories set in `SimilarRegion` won't affect the
     *      filtering done by displaySimImg until the next reload.
     * explanation
     *      fixing this would ask to re-fetch `sImgsPromise` from the
     *      backend: when setting a category in `SimilarRegion`, the
     *      database is updated, the object in `SimilarRegion` is
     *      updated, but the update is not transmitted to the parent
     *      (aka, the current component)
     *
     * @returns {boolean}
     */
    const displaySimImg = (
        simImgScore,
        simImgRegions,
        simImgCategory,
        usersCategory,
        _selectedRegions,
        _excludedCategories,
        _similarityScoreCutoff,
        _propagateFilterByRegions
    ) => isPropagatedContext
        ? true
        : isAboveCutoff(simImgScore, _similarityScoreCutoff)
        && isNotInExcludedCategories(simImgCategory, usersCategory, _excludedCategories);


    /**  run `displaySimImg` to filter `_allSimgs` */
    const filterSImgs = (_allSImgs, _selectedRegions, _excludedCategories, _similarityScoreCutoff, _propagateFilterByRegions) =>
        _allSImgs.filter(({
                              uuid,
                              data: [score, _, sImg, qRegions, sRegions, category, users, isManual, similarityType]
                          }) =>
            displaySimImg(
                score,
                sRegions,
                category,
                users,
                _selectedRegions,
                _excludedCategories,
                _similarityScoreCutoff,
                _propagateFilterByRegions
            ));

    const getSimilarityLabel = (isPropagated, lang, count) => {
        const isPlural = count > 1;

        if (isPropagated) {
            if (lang === "fr") {
                return isPlural ? "similarités propagées" : "similarité propagée";
            } else {
                return isPlural ? "propagated matches" : "propagated match";
            }
        } else {
            if (lang === "fr") {
                return isPlural ? "images similaires" : "image similaire";
            } else {
                return isPlural ? "similar images" : "similar image";
            }
        }
    };

</script>

{#if sImgsPromise}
    {#await sImgsPromise}
        <div class="faded is-center">{waitText}</div>
    {:then _}
        <div>
            <span class="m-2">{filteredSImgs.length} {getSimilarityLabel(isPropagatedContext, appLang, filteredSImgs.length)}</span>
            <div class="m-2 is-gap-2" class:grid={filteredSImgs.length > 0}>
                {#each filteredSImgs as {
                    uuid,
                    data: [score, _, sImg, qRegions, sRegions, category, users, isManual, similarityType]
                } (uuid)}
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
    {:catch error}
        <div class="faded is-center">
            {
                appLang === 'en' ?
                    `Error when retrieving similar regions: ${error}` :
                    `Erreur de recupération des régions similaires: ${error}`
            }
        </div>
    {/await}
{:else}
    <div class="faded is-center">{waitText}</div>
{/if}
