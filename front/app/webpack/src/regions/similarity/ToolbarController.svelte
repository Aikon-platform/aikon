<script>
import { similarityStore } from "./similarityStore.js";
import * as cat from './similarityCategory';
import { appLang } from "../../constants.js";

import InputRangeSlider from "../../ui/InputRangeSlider.svelte";
import InputPillCheckbox from "../../ui/InputPillCheckbox.svelte";
import InputDropdownSelect from "../../ui/InputDropdownSelect.svelte";

const toolbarParams = similarityStore.toolbarParams;
const propagateParams = similarityStore.propagateParams
const allowedPropagateDepthRange = similarityStore.allowedPropagateDepthRange;

const categories = [
    { value: 1, label: cat.exactLabel, icon: cat.exactSvg },
    { value: 2, label: cat.partialLabel, icon: cat.partialSvg },
    { value: 3, label: cat.semanticLabel, icon: cat.semanticSvg },
    { value: 4, label: cat.noLabel, icon: cat.noSvg },
    { value: 5, label: cat.userLabel, icon: cat.userSvg },
];

const regions = [ ];

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
</script>


<div>
    <div class="ctrl-category">
        <InputDropdownSelect choices={categories}
                             multiple={false}
                             placeholder={appLang==="fr" ? "Filtrer par catégorie" : "Filter by category"}
        ></InputDropdownSelect>
    </div>
    <div class="ctrl-regions">
        <InputDropdownSelect choices={regions}
                             multiple={true}
                             placeholder={appLang==="fr" ? "Sélectionner des régions" : "Select regions"}
        ></InputDropdownSelect>
    </div>
    <div class="ctrl-propagation">
        <span><b>Propagation</b></span>
        <div class="columns is-flex is-vcentered ctrl-propagation-inputs">
            <div class="depth column is-two-thirds">
                <span>{ appLang==="fr" ? "Profondeur de récursion" : "Recursion depth" }</span>
                <InputRangeSlider minVal={allowedPropagateDepthRange[0]}
                                  maxVal={allowedPropagateDepthRange[1]}
                                  step={1}
                                  on:updateRange={setRecursionDepth}
                ></InputRangeSlider>
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
