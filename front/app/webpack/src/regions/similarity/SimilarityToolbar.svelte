<script>
/**
 * SimilarityToolbar defines individual filters that are then
 * applied that modify the content displayed (either using front-end
 * filtering when possible or backend queries).
 * front-end filtering is done is `SimilarRegions.svelte`
 */

import { derived } from "svelte/store";

import { similarityStore } from "./similarityStore.js";
import * as cat from './similarityCategory';
import { appLang, csrfToken } from "../../constants.js";
import { shorten } from "../../utils.js";

import InputSlider from "../../ui/InputSlider.svelte";
import InputToggleCheckbox from "../../ui/InputToggleCheckbox.svelte";
import InputDropdown from "../../ui/InputDropdown.svelte";
import IconTooltip from "../../ui/IconTooltip.svelte";

///////////////////////////////////////

const  {
    selectedRegions,
    comparedRegions,
    excludedCategories,
    similarityScoreCutoff,
    propagateRecursionDepth,
    propagateFilterByRegions,
    allowedPropagateDepthRange
} = similarityStore;

const currentPageId = window.location.pathname.match(/\d+/g).join('-');
const baseUrl = `${window.location.origin}${window.location.pathname}`;

const tooltipText =
    appLang==="en"
    ? "Propagated matches are exact matches to images that have an exact match with the current image. There may be up to 6 exact matches connecting the current image and propagated images."
    : "Les correspondances propagées correspondent à des correspondances exactes à des images ayant une correspondance exacte avec l'image actuelle. Il peut y avoir jusqu'à 6 images reliant l'image actuelle à une correspondance propagée.";

const categoriesChoices = [
    { value: 1, label: cat.exactLabel, prefix: cat.exactSvg, prefixType: "svg" },
    { value: 2, label: cat.partialLabel, prefix: cat.partialSvg, prefixType: "svg" },
    { value: 3, label: cat.semanticLabel, prefix: cat.semanticSvg, prefixType: "svg" },
    { value: 4, label: cat.noLabel, prefix: cat.noSvg, prefixType: "svg" },
    { value: 5, label: cat.userLabel, prefix: cat.userSvg, prefixType: "svg" },
];

const comparedRegionsChoices = derived(comparedRegions, (($comparedRegions) =>
    Object.entries($comparedRegions).map(([regionId, region]) => ({
        prefix: `#${region.id}`,  // the number of the region
        prefixType: "text",
        value: regionId,
        label: shorten(region.title.replace(/^[^|]+/, ""))
    }))));

/** @type {number[]}: category values */
const defaultExcludedCategories = $excludedCategories;
/** @type {string[]}: regions IDs */
const defaultRegions = Object.keys($selectedRegions[currentPageId] || {});
/** @type {number} */
const defaultRecursionDepth = $propagateRecursionDepth;
/** @type {boolean} */
const defaultFilterByRegions = $propagateFilterByRegions;

/** @type {Promise<Array<number?>>}. will be updated every time $selectedRegions changes */
const similarityScoreRangePromise = fetchSimilarityScoreRange();

/** @type {number?} ensures that $similarityScoreCutoff matches a value in similarityScoreRangePromise. updated by fetchSimilarityScoreRange */
$: defaultSimilarityScoreCutoff = $similarityScoreCutoff || undefined

/** @type {number} */
let innerWidth, innerHeight;
$: wideDisplay = innerWidth > 1200;
$: stickyTop = calcStickyTop(innerWidth, innerHeight);  // recalculated on window resize

///////////////////////////////////////

/** @returns {Promise<Array<number?>>} */
async function fetchSimilarityScoreRange() {
    let range = [];
    return await fetch(`${baseUrl}similarity-score-range`)
    .then(response => response.json())
    .then(data => {
        range = [data.min, data.max];
        if ( !range.every(x => typeof x === "number") ) {
            console.error(`fetchSimilarityScoreRange: expected '[number, number]', got '${range}'. Defaulting to '[]'`);
            range = [];
        } else {
            defaultSimilarityScoreCutoff =
                $similarityScoreCutoff && range[0] <= $similarityScoreCutoff && range[1] >= $similarityScoreCutoff
                ? $similarityScoreCutoff
                : range[0]
        }
        return range;
    })
    .catch(err => {
        console.error("Error on fetchSimilarityScoreRange:", err);
        errorMsg.set(err.message);
        return range
    })
}

const calcStickyTop = () =>
    document.querySelector("#nav-actions")?.offsetHeight;


const setSimilarityScoreCutoff = (e) => similarityScoreCutoff.set(e.detail.data);
const setExcludedCategories = (e) => excludedCategories.set(e.detail);
const setPropagateRecursionDepth = (e) => propagateRecursionDepth.set(e.detail.data);
const setPropagateFilterByRegions = (e) => propagateFilterByRegions.set(e.detail);
const setComparedRegions = (e) => {
    const selectedRegionsIds = e.detail;
    const newSelectedRegions = { [currentPageId] : {} }
    Object.keys($comparedRegions).forEach(key => {
        if ( selectedRegionsIds.includes(key) ) {
            newSelectedRegions[currentPageId][key] = $comparedRegions[key];
        }
    })
    selectedRegions.set(newSelectedRegions);
}

</script>


<svelte:window bind:innerWidth bind:innerHeight></svelte:window>

<div class="ctrl-wrapper is-flex is-justify-content-center is-align-items-center"
     style="{ stickyTop ? `top: ${stickyTop}px` : '' }"
>
    <form class="ctrl">
        <div class="ctrl-inputs columns">
            <div class="ctrl-block-wrapper column { wideDisplay ? 'is-three-fifths' : 'is-half' }">
                <div class="ctrl-block ctrl-similarity">
                    <div class="ctrl-block-title column is-2">
                        <span>Similarity</span>
                    </div>
                    <div class="ctrl-block-inputs column is-10 columns is-vcentered { wideDisplay ? '' : 'is-multiline' }">
                        <div class="column { wideDisplay ? 'mb-2 is-one-third' : '' }">
                            {#if Object.keys($comparedRegionsChoices).length}
                                <InputDropdown choices={$comparedRegionsChoices}
                                               multiple={true}
                                               placeholder="..."
                                               start={defaultRegions}
                                               lightDisplay={true}
                                               title={appLang==="fr" ? "Régions sélectionnées" : "Selected regions"}
                                               selectAll={true}
                                               on:updateValues={setComparedRegions}
                                ></InputDropdown>
                            {/if}
                        </div>
                        <div class="column { wideDisplay ? 'mb-2 is-one-third' : '' }">
                            <InputDropdown choices={categoriesChoices}
                                           multiple={true}
                                           placeholder="..."
                                           start={defaultExcludedCategories}
                                           lightDisplay={true}
                                           title={appLang==="fr" ? "Catégories masquées" : "Hidden categories"}
                                           selectAll={true}
                                           on:updateValues={setExcludedCategories}
                            ></InputDropdown>
                        </div>
                        <div class="column { wideDisplay ? 'is-one-third' : '' }">
                            {#await similarityScoreRangePromise then similarityScoreRange}
                                {#if similarityScoreRange.length}
                                    <InputSlider title={ appLang==="fr" ? "Score minimal" : "Minimal score" }
                                                 minVal={similarityScoreRange[0]}
                                                 maxVal={similarityScoreRange[1]}
                                                 start={defaultSimilarityScoreCutoff || similarityScoreRange[0]}
                                                 roundTo={3}
                                                 on:updateSlider={setSimilarityScoreCutoff}
                                    ></InputSlider>
                                {/if}
                            {/await}
                        </div>
                    </div>
                </div>
            </div>
            <div class="ctrl-block-wrapper column { wideDisplay ? 'is-two-fifths' : 'is-half' }">
                <div class="ctrl-block ctrl-propagation">
                    <div class="ctrl-block-title column is-2">
                        <span class="mr-1">Propagation</span>
                        <IconTooltip iconifyIcon="material-symbols:help-outline"
                                    altText={ appLang==="en" ? "Display help" : "Afficher une explication"}
                                    tooltipText={tooltipText}
                        ></IconTooltip>

                    </div>
                    <div class="ctrl-block-inputs column is-10 columns { wideDisplay ? '' : 'is-multiline' }">
                        <div class="column { wideDisplay ? 'is-two-thirds' : 'is-full' }">
                            <InputSlider title={ appLang==="fr" ? "Profondeur de récursion" : "Recursion depth" }
                                         minVal={allowedPropagateDepthRange[0]}
                                         maxVal={allowedPropagateDepthRange[1]}
                                         start={defaultRecursionDepth}
                                         step={1}
                                         on:updateSlider={setPropagateRecursionDepth}
                            ></InputSlider>
                        </div>
                        <div class="column is-flex is-align-items-center
                                    { wideDisplay ? 'is-one-third is-justify-content-center' : 'is-full is-justify-content-start' }">
                            <InputToggleCheckbox checkboxLabel="Filter by region"
                                                 on:updateChecked={setPropagateFilterByRegions}
                                                 start={defaultFilterByRegions}
                                                 buttonDisplay={true}
                            ></InputToggleCheckbox>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </form>
</div>


<style>
.ctrl-wrapper {
    width: 100%;
    height: 100%;
    margin: 0 0 5vh;
    position: sticky;
    background-color: var(--bulma-body-background-color);
    z-index: 2;
}
.ctrl {
    width: 100%;
    border: solid 1px var(--bulma-border);
    border-radius: 0 0 var(--bulma-burger-border-radius) var(--bulma-burger-border-radius);
    display: flex;
    flex-direction: row;
}
.ctrl-inputs {
    flex-grow: 2;
    margin-inline-start: 0;
    margin-inline-end: 0;
}
.ctrl-block-wrapper {
    margin: 12px 0;
}
.ctrl-block-wrapper:last-child {
    border-left: var(--default-border);
}
.ctrl-block {
    margin: 0;
}
.ctrl-block-title, .ctrl-block-inputs {
    margin-inline-start: 0;
}
.ctrl-block-title {
    min-width: 100px;
}
.ctrl-propagation > .ctrl-block-title {
    display: flex;
    justify-content: start;
    align-items: center;
}
.ctrl-block-title > span {
    font-weight: bold;
}
.ctrl-block-inputs {
    width: 100%;
}
.ctrl-block-inputs > * {
    height: fit-content;
}
:global(.ctrl-block-inputs .slider-outer-wrapper) {
    margin-bottom: 0;
}
</style>
