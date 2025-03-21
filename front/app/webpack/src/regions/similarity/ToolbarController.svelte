<script>
import { derived } from "svelte/store";

import { similarityStore } from "./similarityStore.js";
import * as cat from './similarityCategory';
import { appLang } from "../../constants.js";

import InputSlider from "../../ui/InputSlider.svelte";
import InputPillCheckbox from "../../ui/InputPillCheckbox.svelte";
import InputDropdownSelect from "../../ui/InputDropdownSelect.svelte";
    import { shorten } from "../../utils.js";

const toolbarParams = similarityStore.toolbarParams;
const propagateParams = similarityStore.propagateParams
const comparedRegions = similarityStore.comparedRegions;
const similarityScoreRange = similarityStore.similarityScoreRange
const qImgs = similarityStore.qImgs;
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


///////////////////////////////////////

const setRecursionDepth = (e) => {
    propagateParams.set({
        recursionDepth: e.detail,
        filterByRegion: $propagateParams.filterByRegion
    });
    console.log("setRecursionDepth :: $propagateParams", $propagateParams);
    console.log("setRecursionDepth :: $toolbarParams", $toolbarParams);
}
const setFilterByRegion = (e) => {
    propagateParams.set({
        recursionDepth: $propagateParams.recursionDepth,
        filterByRegion: e.detail
    })
    console.log("setFilterByRegion :: $propagateParams", $propagateParams);
    console.log("setFilterByRegion :: $toolbarParams", $toolbarParams);
}
const setCategory = (e) => {}
const setComparedRegions = (e) => {}
const setSelectedSimilarityScore = (e) => {}
</script>


<div>
    <div class="ctrl-category">
        <InputDropdownSelect choices={categoriesChoices}
                             multiple={true}
                             placeholder={appLang==="fr" ? "Filtrer par catégorie" : "Filter by category"}
        ></InputDropdownSelect>
    </div>
    <div class="ctrl-regions">
        {#if Object.keys($comparedRegionsChoices).length}
            <InputDropdownSelect choices={$comparedRegionsChoices}
                                 multiple={true}
                                 placeholder={appLang==="fr" ? "Sélectionner des régions" : "Select regions"}
            ></InputDropdownSelect>
        {/if}
    </div>
    <div class="ctrl-score">
        {#if $similarityScoreRange.length}
            <h1>{$similarityScoreRange}</h1>
            {$similarityScoreRange[0]}
            {$similarityScoreRange[1]}
            <InputSlider minVal={0}
                         maxVal={5}
                         start={3}
            ></InputSlider>

            <!--
            <InputSlider minVal={$similarityScoreRange[0]}
                         maxVal={$similarityScoreRange[1]}
                         start={$similarityScoreRange[1]}
            ></InputSlider>
            -->
        {/if}
    </div>
    <div class="ctrl-propagation">
        <span><b>Propagation</b></span>
        <div class="columns is-flex is-vcentered ctrl-propagation-inputs">
            <div class="depth column is-two-thirds">
                <span>{ appLang==="fr" ? "Profondeur de récursion" : "Recursion depth" }</span>
                <!--
                <InputSlider minVal={allowedPropagateDepthRange[0]}
                             maxVal={allowedPropagateDepthRange[1]}
                             start={allowedPropagateDepthRange}
                             step={1}
                             on:updateSlider={setRecursionDepth}
                ></InputSlider>
                -->
            </div>
            <div class="region column">
                <InputPillCheckbox checkboxLabel="Filter by region"
                                on:updateChecked={setFilterByRegion}
                ></InputPillCheckbox>
            </div>
        </div>
    </div>

</div>


<style>
.ctrl-propagation-inputs {
    margin: 10px;
    padding: 5px;
    gap: 2rem;
}
.ctrl-propagation-inputs > * {
}
</style>
