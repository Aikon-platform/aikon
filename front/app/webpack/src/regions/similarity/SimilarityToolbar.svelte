<script>
import { derived } from "svelte/store";

import { similarityStore } from "./similarityStore.js";
import * as cat from './similarityCategory';
import { appLang } from "../../constants.js";

import InputSlider from "../../ui/InputSlider.svelte";
import InputToggleCheckbox from "../../ui/InputToggleCheckbox.svelte";
import InputDropdown from "../../ui/InputDropdown.svelte";
import { shorten } from "../../utils.js";

///////////////////////////////////////

const  {
    selectedRegions,
    propagateParams,
    comparedRegions,
    excludedCategories,
    similarityScoreRange,
    similarityScoreCutoff,
    allowedPropagateDepthRange
} = similarityStore;

const currentPageId = window.location.pathname.match(/\d+/g).join('-');

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
        label: shorten(region.title)
    }))));

/** @type {Number[]}: category values */
const preSelectedExcludedCategories = $excludedCategories;
/** @type {string[]}: regions IDs */
const preSelectedRegions = Object.keys($selectedRegions[currentPageId]);

/** @type {Number} */
let innerWidth, innerHeight;
$: wideDisplay = innerWidth > 1200;

///////////////////////////////////////

const setPropagateRecursionDepth = (e) =>
    propagateParams.set({
        recursionDepth: e.detail.data,
        filterByRegions: $propagateParams.filterByRegions
    });
const setPropagateFilterByRegion = (e) =>
    propagateParams.set({
        recursionDepth: $propagateParams.recursionDepth,
        filterByRegions: e.detail
    });
const setExcludedCategories = (e) => {
    excludedCategories.set(e.detail);
    localStorage.setItem('excludedCategories', JSON.stringify($excludedCategories));
}
const setComparedRegions = (e) => {
    const selectedRegionsIds = e.detail;
    const newSelectedRegions = { [currentPageId] : {} }
    Object.keys($comparedRegions).forEach(key => {
        if ( selectedRegionsIds.includes(key) ) {
            newSelectedRegions[currentPageId][key] = $comparedRegions[key];
        }
    })
    selectedRegions.set(newSelectedRegions);
    localStorage.setItem("selectedRegions", JSON.stringify($selectedRegions));
}
const setSimilarityScoreCutoff = (e) => similarityScoreCutoff.set(e.detail.data);
</script>



<svelte:window bind:innerWidth bind:innerHeight></svelte:window>

<h1>{innerWidth}-{innerHeight} ({wideDisplay})</h1>
<div class="ctrl-wrapper is-flex is-justify-content-center is-align-items-center">
    <form class="ctrl">
        <div class="ctrl-inputs columns">
            <div class="ctrl-block-wrapper column { wideDisplay ? 'is-three-fifths' : 'is-half' }">
                <div class="ctrl-block ctrl-similarity">
                    <div class="ctrl-block-title column is-2">
                        <span>Similarity</span>
                    </div>
                    <div class="ctrl-block-inputs column is-10 columns is-vcentered { wideDisplay ? '' : 'is-multiline' }">
                        <div class="column { wideDisplay ? 'is-one-third' : '' }">
                            {#if Object.keys($comparedRegionsChoices).length}
                                <InputDropdown choices={$comparedRegionsChoices}
                                               multiple={true}
                                               placeholder={appLang==="fr" ? "Sélectionner des régions" : "Select regions"}
                                               defaultSelection={preSelectedRegions}
                                               lightDisplay={true}
                                               on:updateValues={setComparedRegions}
                                ></InputDropdown>
                            {/if}
                        </div>
                        <div class="column { wideDisplay ? 'is-one-third' : '' }">
                            <InputDropdown choices={categoriesChoices}
                                           multiple={true}
                                           placeholder={appLang==="fr" ? "Exclure les catégories" : "Exclude categories"}
                                           defaultSelection={preSelectedExcludedCategories}
                                           lightDisplay={true}
                                           on:updateValues={setExcludedCategories}
                            ></InputDropdown>
                        </div>
                        <div class="column { wideDisplay ? 'is-one-third' : '' }">
                            {#if $similarityScoreRange.length}
                                <InputSlider title={ appLang==="fr" ? "Score minimal" : "Minimal score" }
                                            minVal={$similarityScoreRange[0]}
                                            maxVal={$similarityScoreRange[1]}
                                            start={$similarityScoreRange[0]}
                                            roundTo={3}
                                            on:updateSlider={setSimilarityScoreCutoff}
                                ></InputSlider>
                            {/if}
                        </div>
                    </div>
                </div>
            </div>
            <div class="ctrl-block-wrapper column { wideDisplay ? 'is-two-fifths' : 'is-half' }">
                <div class="ctrl-block ctrl-propagation">
                    <div class="ctrl-block-title column is-2">
                        <span>Propagation</span>
                    </div>
                    <div class="ctrl-block-inputs column is-10 columns { wideDisplay ? '' : 'is-multiline' }">
                        <div class="column { wideDisplay ? 'is-two-thirds' : 'is-full' }">
                            <InputSlider title={ appLang==="fr" ? "Profondeur de récursion" : "Recursion depth" }
                                        minVal={allowedPropagateDepthRange[0]}
                                        maxVal={allowedPropagateDepthRange[1]}
                                        start={allowedPropagateDepthRange}
                                        step={1}
                                        on:updateSlider={setPropagateRecursionDepth}
                            ></InputSlider>
                        </div>
                        <div class="column is-flex is-align-items-center
                                    { wideDisplay ? 'is-one-third is-justify-content-center' : 'is-full is-justify-content-start' }">
                            <InputToggleCheckbox checkboxLabel="Filter by region"
                                            on:updateChecked={setPropagateFilterByRegion}
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
    margin: 5vh 0;
}
.ctrl {
    width: 100%;
    border: solid 1px var(--bulma-border);
    border-radius: var(--bulma-burger-border-radius);
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
