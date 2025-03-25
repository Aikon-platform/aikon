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
        similarityScoreCutoff
    } = similarityStore;

    const isPropagatedContext = getContext("similarityPropagatedContext") || false;  // true if it's a propagation, false otherwise
    const currentPageId = window.location.pathname.match(/\d+/g).join('-');

    //////////////////////////////

    /**
     * @param {Number|String} simImgScore
     * @param {Number} cutoff
     */
    const isAboveCutoff = (simImgScore, cutoff) =>
        cutoff === undefined
        ? true
        : simImgScore != null && Number(simImgScore) >= cutoff;

    /**
     * @param {Number} simImgCategory
     * @param {Array<Number>} usersCategory
     * @param {Array<Number>} _excludedCategories
     */
    const isNotInExcludedCategories = (simImgCategory, usersCategory, _excludedCategories) =>
        !_excludedCategories.includes(simImgCategory);

    /**
     * NOTE: the filtered images won't be updated if the user
     * sets a category on a `SimilarRegion`
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
    $: displaySimImg = (simImgScore, simImgCategory, usersCategory) =>
        isPropagatedContext  // the similarity filter won't affect the display of propagations
        || (isAboveCutoff(simImgScore, $similarityScoreCutoff)
            && isNotInExcludedCategories(simImgCategory, usersCategory, $excludedCategories));

    $: noRegionsSelected =
        Object.values($selectedRegions).length === 0
        || $selectedRegions[currentPageId] === undefined
        || !Object.keys($selectedRegions[currentPageId]).length;
</script>

{#await sImgsPromise}
    <div class="faded is-center">
        { appLang === 'en' && !isPropagatedContext
        ? 'Retrieving similar regions...'
        : appLang === 'fr' && !isPropagatedContext
        ? 'Récupération des régions similaires...'
        : appLang === 'en' && isPropagatedContext
        ? "Retrieving propagated regions..."
        : "Récupération de similarités propagées..."
        }
    </div>
{:then simImgs}
    {#each simImgs as [score, _, sImg, qRegions, sRegions, category, users, isManual]}
        {#if displaySimImg(score, category, users, $excludedCategories, $similarityScoreCutoff)}
            <SimilarRegion {qImg} {sImg} {score} {qRegions} {sRegions} {category} {users} {isManual}/>
        {/if}
    {:else}
        {#if noRegionsSelected }
            <div class="faded is-center">
                {appLang === 'en' ? 'No document selected' : 'Aucun document sélectionné'}
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
