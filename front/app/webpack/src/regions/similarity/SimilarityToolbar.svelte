<script>
/**
 * SimilarityToolbar defines individual filters that are then
 * applied that modify the content displayed (either using front-end
 * filtering when possible or backend queries).
 * front-end filtering is done is `SimilarRegions.svelte`
 */

import { derived } from "svelte/store";
import { slide } from 'svelte/transition';

import { similarityStore } from "./similarityStore.js";
import * as cat from './similarityCategory';
import { appLang } from "../../constants.js";
import { shorten } from "../../utils.js";

import InputSlider from "../../ui/InputSlider.svelte";
import InputToggleCheckbox from "../../ui/InputToggleCheckbox.svelte";
import InputDropdown from "../../ui/InputDropdown.svelte";
import IconTooltip from "../../ui/IconTooltip.svelte";
import TooltipGeneric from "../../ui/TooltipGeneric.svelte";

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

$: toolbarExpanded = false;
$: toggleToolbarText =
    appLang === "fr" && toolbarExpanded
    ? "Refermer le menu de recherche"
    : appLang === "fr" && !toolbarExpanded
    ? "Ouvrir le menu de recherche"
    : appLang === "en" && toolbarExpanded
    ? "Collapse the toolbar"
    : "Expand the toolbar";

///////////////////////////////////////


const toggleToolbarExpanded = () => toolbarExpanded = !toolbarExpanded;

const calcStickyTop = () =>
    document.querySelector("#nav-actions")?.offsetHeight;

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

const setSimilarityScoreCutoff = (e) => similarityScoreCutoff.set(e.detail);
const setExcludedCategories = (e) => excludedCategories.set(e.detail);
const setPropagateRecursionDepth = (e) => propagateRecursionDepth.set(e.detail);
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

<div class="ctrl-wrapper is-flex is-justify-content-center is-align-items-center
            { toolbarExpanded ? 'toolbar-expanded' : 'toolbar-collapsed' }"
     style="{ stickyTop ? `top: ${stickyTop}px` : '' }"
>
    <form class="ctrl">
        <div class="ctrl-base">
            <div class="ctrl-block-wrapper">
                <div class="ctrl-block">
                    <div class="ctrl-block-inputs">
                        <div class="ctrl-input">
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
                        <div class="ctrl-input">
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
        </div>
        {#if toolbarExpanded }
            <div transition:slide={{axis: "y"}}
                 class="ctrl-extra">
                <div class="ctrl-block-wrapper">
                    <div class="ctrl-block">
                        <div class="ctrl-block-title">
                            <span class="tag is-medium is-link">Similarity</span>
                        </div>
                        <div class="ctrl-block-inputs">
                            <div class="ctrl-input">
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
                        </div>
                    </div>
                </div>
                <div class="ctrl-block-wrapper">
                    <div class="ctrl-block">
                        <div class="ctrl-block-title">
                            <span class="tag is-medium is-link mr-1">Propagation</span>
                            <IconTooltip iconifyIcon="material-symbols:help-outline"
                                        altText={ appLang==="en" ? "Display help" : "Afficher une explication"}
                                        tooltipText={tooltipText}
                            ></IconTooltip>
                        </div>
                        <div class="ctrl-block-inputs">
                            <div class="ctrl-input">
                                <InputSlider title={ appLang==="fr" ? "Profondeur de récursion" : "Recursion depth" }
                                            minVal={allowedPropagateDepthRange[0]}
                                            maxVal={allowedPropagateDepthRange[1]}
                                            start={defaultRecursionDepth}
                                            step={1}
                                            on:updateSlider={setPropagateRecursionDepth}
                                ></InputSlider>
                            </div>
                            <div class="ctrl-input">
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
        {/if}
        <!--
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
        -->
        <div class="ctrl-toggle">
            <button on:click|preventDefault={toggleToolbarExpanded}
                    class="button is-link"
            >
                <svg style={`transform: rotate(${toolbarExpanded ? "180" : "0"}deg)`}
                     xmlns="http://www.w3.org/2000/svg"
                     width="24"
                     height="24"
                     viewBox="0 0 24 24"
                >
                    <path fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 3v18m0 0l8.5-8.5M12 21l-8.5-8.5"></path>
                </svg>
                <TooltipGeneric tooltipText={toggleToolbarText}></TooltipGeneric>
            </button>
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
    margin-bottom: max(15vh, 200px);
}
.ctrl {
    position: absolute;
    top: 0;
    width: 100%;
    background-color: var(--bulma-body-background-color);
    border: solid 1px var(--bulma-border);
    border-radius: 0 0 var(--bulma-burger-border-radius) var(--bulma-burger-border-radius);
    box-shadow: 0 3px;
    display: flex;
    flex-direction: column;
}
.toolbar-collapsed .ctrl {
    box-shadow: var(--bulma-border-weak) 0 3px;
}
.toolbar-expanded .ctrl {
    box-shadow: var(--bulma-border-active) 0 3px;
}
.ctrl-base {

}
.ctrl-block-wrapper {
    width: 100%;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    border-bottom: solid 1px var(--bulma-border);
}
.ctrl-block {
    width: 70%;
    display: flex;
    flex-direction: row;
    align-items: center;
    justify-content: space-around;
    /*margin: 10px 20px;*/
    margin: 5px;
}
.ctrl-extra .ctrl-block {
    width: 100%;
    display: grid;
    grid-template-rows: 100%;
    grid-template-columns: 1fr 5.7fr; /** make items seem horizontally centered with .ctrl-base .ctrl-block */
}
.ctrl-block-title {
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 1em 0;
}
.ctrl-block-inputs {
    display: flex;
    flex-direction: row;
    align-items: center;
    justify-content: start;
    width: 100%;
    margin: 5px 0;
}
.ctrl-block-inputs:has(> :last-child:nth-child(1)) {
    /** .ctrl-block-inputs contains only 1 child */
    align-items: flex-start;
}
.ctrl-input {
    width: 100%;
    max-width: max(350px, 30vw);
    margin: 0 20px;
}
.ctrl-input:nth-child(1) {
    margin-left: 0;
}
.ctrl-toggle {
    height: 0;
    display: flex;
    align-items: center;
    justify-content: center;
}
.ctrl-toggle > button {
    border: var(--default-border);
    border-radius: 2rem;
    height: 40px;
    width: 40px;
    position: relative;
}
.ctrl-toggle > button svg {
    height: 100%;
    transition: transform .5s;
}

/*
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
*/
</style>
