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
import { appLang } from "../../constants.js";
import { shorten } from "../../utils.js";

import InputSlider from "../../ui/InputSlider.svelte";
import InputToggle from "../../ui/InputToggle.svelte";
import InputDropdown from "../../ui/InputDropdown.svelte";
import IconTooltip from "../../ui/IconTooltip.svelte";
import {onMount} from "svelte";
import Toolbar from "../../Toolbar.svelte";

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


function updateNavActionsHeight() {
    const navActions = document.getElementById("nav-actions");
    if (navActions) {
        document.documentElement.style.setProperty('--nav-actions-height', `${navActions.offsetHeight}px`);
    }
}
let resizeObserver;
onMount(() => {
    updateNavActionsHeight();

    resizeObserver = new ResizeObserver(() => {
        updateNavActionsHeight();
    });

    const navActions = document.getElementById("nav-actions");
    if (navActions) {
        resizeObserver.observe(navActions);
    }

    return () => {
        if (resizeObserver && navActions) {
            resizeObserver.unobserve(navActions);
            resizeObserver.disconnect();
        }
    };
});

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

/** @type {Promise<Array<number?>>}. will be updated every time $selectedRegions changes */
const similarityScoreRangePromise = fetchSimilarityScoreRange();

/** @type {number?} ensures that $similarityScoreCutoff matches a value in similarityScoreRangePromise. updated by fetchSimilarityScoreRange */
$: defaultSimilarityScoreCutoff = $similarityScoreCutoff || undefined

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

<svelte:window/>

<Toolbar>
    <div slot="toolbar-visible" class="ctrl-block-inputs">
        <div class="ctrl-input">
            {#if Object.keys($comparedRegionsChoices).length}
                <InputDropdown choicesItems={$comparedRegionsChoices}
                    multiple={true}
                    placeholder="..."
                    start={Object.keys($selectedRegions[currentPageId] || {})}
                    lightDisplay={true}
                    title={appLang==="fr" ? "Régions sélectionnées" : "Selected regions"}
                    selectAll={true}
                    on:updateValues={setComparedRegions}
                />
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
                    />
                {/if}
            {/await}
        </div>
    </div>
    <svelte:fragment slot="toolbar-hidden">
        <div class="ctrl-block-wrapper">
            <div class="ctrl-block">
                <div class="ctrl-block-title">
                    <span class="tag is-medium is-link">Similarity</span>
                </div>
                <div class="ctrl-block-inputs">
                    <div class="ctrl-input">
                        <InputDropdown choicesItems={categoriesChoices}
                            multiple={true}
                            placeholder="..."
                            start={$excludedCategories}
                            lightDisplay={true}
                            title={appLang==="fr" ? "Catégories masquées" : "Hidden categories"}
                            selectAll={true}
                            on:updateValues={setExcludedCategories}
                        />
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
                    />
                </div>
                <div class="ctrl-block-inputs">
                    <div class="ctrl-input">
                        <InputSlider title={ appLang==="fr" ? "Profondeur de récursion" : "Recursion depth" }
                            minVal={allowedPropagateDepthRange[0]}
                            maxVal={allowedPropagateDepthRange[1]}
                            start={$propagateRecursionDepth}
                            step={1}
                            on:updateSlider={setPropagateRecursionDepth}
                        />
                    </div>
                    <div class="ctrl-input">
                        <InputToggle toggleLabel="Filter by region"
                             on:updateChecked={setPropagateFilterByRegions}
                             start={$propagateFilterByRegions}
                             buttonDisplay={true}
                        />
                    </div>
                </div>
            </div>
        </div>
    </svelte:fragment>
</Toolbar>

<style>
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
    margin: 5px;
}
.ctrl-block-title {
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 1em;
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
    /** rule for .ctrl-block-inputs that contain only 1 child */
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
</style>
