<script>
import { derived } from "svelte/store";

import { similarityStore } from "./similarityStore.js";
import * as cat from './similarityCategory';
import { appLang } from "../../constants.js";

import InputSlider from "../../ui/InputSlider.svelte";
import InputToggleCheckbox from "../../ui/InputToggleCheckbox.svelte";
import InputDropdownSelect from "../../ui/InputDropdownSelect.svelte";
import { shorten } from "../../utils.js";

///////////////////////////////////////

// const similarityToolbarParams = similarityStore.similarityToolbarParams;
const currentPageId = similarityStore.currentPageId;
const selectedRegions = similarityStore.selectedRegions;
const propagateParams = similarityStore.propagateParams;
const comparedRegions = similarityStore.comparedRegions;
const excludedCategories = similarityStore.excludedCategories;
const similarityScoreRange = similarityStore.similarityScoreRange;
const similarityScoreCutoff = similarityStore.similarityScoreCutoff;
const allowedPropagateDepthRange = similarityStore.allowedPropagateDepthRange;

const categoriesChoices = [
    { value: 1, label: cat.exactLabel, icon: cat.exactSvg },
    { value: 2, label: cat.partialLabel, icon: cat.partialSvg },
    { value: 3, label: cat.semanticLabel, icon: cat.semanticSvg },
    { value: 4, label: cat.noLabel, icon: cat.noSvg },
    { value: 5, label: cat.userLabel, icon: cat.userSvg },
];

const comparedRegionsChoices = derived(comparedRegions, (($comparedRegions) =>
    Object.entries($comparedRegions).map(([regionId, region]) => ({
        value: regionId,
        label: shorten(region.title)
    }))));

/** @type {Number[]}: category values */
const preSelectedExcludedCategories = $excludedCategories;
/** @type {string[]}: regions IDs */
const preSelectedRegions = Object.keys($selectedRegions[currentPageId]);

///////////////////////////////////////

const setPropagateRecursionDepth = (e) =>
    propagateParams.set({
        recursionDepth: e.detail,
        filterByRegion: $propagateParams.filterByRegion
    });
const setPropagateFilterByRegion = (e) =>
    propagateParams.set({
        recursionDepth: $propagateParams.recursionDepth,
        filterByRegion: e.detail
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


<div class="ctrl-wrapper is-flex is-justify-content-center is-align-items-center">
    <div class="ctrl">
        <div class="ctrl-inputs">
            <div class="ctrl-row-wrapper">
                <div class="ctrl-row ctrl-similarity columns">
                    <div class="ctrl-row-title column is-2 is-flex is-justify-content-center is-align-items-center">
                        <span>Similarity</span>
                    </div>
                    <div class="ctrl-row-inputs column is-10 columns is-multiline">
                        <div class="column">
                            {#if Object.keys($comparedRegionsChoices).length}
                                <InputDropdownSelect choices={$comparedRegionsChoices}
                                                    multiple={true}
                                                    placeholder={appLang==="fr" ? "Sélectionner des régions" : "Select regions"}
                                                    defaultSelection={preSelectedRegions}
                                                    on:updateValues={setComparedRegions}
                                ></InputDropdownSelect>
                            {/if}
                        </div>
                        <div class="column">
                            <InputDropdownSelect choices={categoriesChoices}
                                                multiple={true}
                                                placeholder={appLang==="fr" ? "Exclure les catégories" : "Exclude categories"}
                                                defaultSelection={preSelectedExcludedCategories}
                                                on:updateValues={setExcludedCategories}
                            ></InputDropdownSelect>
                        </div>
                        <div class="column">
                            {#if $similarityScoreRange.length}
                                <InputSlider minVal={$similarityScoreRange[0]}
                                            maxVal={$similarityScoreRange[1]}
                                            start={$similarityScoreRange[1]}
                                            roundTo={3}
                                            on:updateSlider={setSimilarityScoreCutoff}
                                ></InputSlider>
                            {/if}
                        </div>
                    </div>
                </div>
            </div>
            <div class="ctrl-row-wrapper">
                <div class="ctrl-row ctrl-propagation columns">
                    <div class="ctrl-row-title column is-2 is-flex is-justify-content-center is-align-items-center">
                        <span>Propagation</span>
                    </div>
                    <div class="ctrl-row-inputs column is-10 columns">
                        <div class="column is-two-thirds">
                            <span>{ appLang==="fr" ? "Profondeur de récursion" : "Recursion depth" }</span>
                            <InputSlider minVal={allowedPropagateDepthRange[0]}
                                        maxVal={allowedPropagateDepthRange[1]}
                                        start={allowedPropagateDepthRange}
                                        step={1}
                                        on:updateSlider={setPropagateRecursionDepth}
                            ></InputSlider>
                        </div>
                        <div class="column is-flex is-justify-content-center is-align-items-center">
                            <InputToggleCheckbox checkboxLabel="Filter by region"
                                            on:updateChecked={setPropagateFilterByRegion}
                            ></InputToggleCheckbox>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        <div class="ctrl-submit is-flex is-justify-content-center is-align-items-end">
            <input type="submit"
                   class="button"
                   value={ appLang==="fr" ? "Valider" : "Submit"}
            />
        </div>
    </div>
</div>


<style>
.ctrl-wrapper {
    width: 100%;
    height: 100%;
    margin: 5vh 0;
}
.ctrl {
    width: min(90%, 1200px);
    border: solid 1px var(--bulma-border);
    border-radius: var(--bulma-burger-border-radius);
    display: flex;
    flex-direction: row;
}
.ctrl-inputs {
    flex-grow: 2;
    display: grid;
    grid-template-columns: 100%;
    grid-template-rows: 50% 50%;
}
.ctrl-row-wrapper {
    margin: 20px 0;
}
.ctrl-row {
    margin: 0;
}
.ctrl-row-title, .ctrl-row-inputs {
    margin-inline-start: 0;
}
.ctrl-row-title {
    min-width: 100px;
}
.ctrl-row-title > span {
    font-weight: bold;
}
.ctrl-row-inputs {
    padding-left: 5px;
    border-left: solid 1px var(--bulma-border);
}
.ctrl-submit > * {
    margin: 20px;
}
</style>
