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
     * @param {number} simImgRegions
     * @param {Array<number>} _selectedRegions
    */
    const isInSelectedRegions = (simImgRegions, _selectedRegions) =>
        Object.keys(_selectedRegions[currentPageId])
        .map(k => _selectedRegions[currentPageId][k].id)
        .includes(simImgRegions);

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
    ) => {
        if ( isPropagatedContext ) {
            return true
        } else {
            // the commented filter seems useless ?
            let inSelectedRegions =
                // _propagateFilterByRegions
                // ? isInSelectedRegions(simImgRegions, _selectedRegions)
                // : true;
                true;
            return (
                isAboveCutoff(simImgScore, _similarityScoreCutoff)
                && isNotInExcludedCategories(simImgCategory, usersCategory, _excludedCategories)
                && inSelectedRegions
            );
        }
    }
</script>

{#if sImgsPromise}
    {#await sImgsPromise}
        <div class="faded is-center">{waitText}</div>
    {:then simImgs}
        {#each simImgs as [score, _, sImg, qRegions, sRegions, category, users, isManual, similarityType]}
            {#if displaySimImg(
                score,
                sRegions,
                category,
                users,
                $selectedRegions,
                $excludedCategories,
                $similarityScoreCutoff,
                $propagateFilterByRegions
            )}
                <SimilarRegion {qImg} {sImg} {score} {qRegions} {sRegions} {category} {users} {isManual} {similarityType}/>
            {/if}
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
