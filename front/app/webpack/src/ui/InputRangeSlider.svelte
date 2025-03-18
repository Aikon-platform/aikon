<script>
import { onMount, createEventDispatcher } from "svelte";

import noUiSlider from "nouislider";
import 'nouislider/dist/nouislider.css';

import TooltipGeneric from "./TooltipGeneric.svelte";

//////////////////////////////////////////////

export let minVal;                  /** @type {Number} */
export let maxVal;                  /** @type {Number} */
export let step = 1;                /** @type {Number} */

let slider;
const dispatch = createEventDispatcher();
const handleTooltips = [];
const oldSelectedRange = { min: undefined, max: undefined };
const handleHtmlIds = [
    `noUi-handle-${window.crypto.randomUUID()}`,
    `noUi-handle-${window.crypto.randomUUID()}` ];

$: selectedRange = { min:minVal, max:maxVal };
$: updateHandleTooltip(selectedRange);  // run updateHandleTooltip when `selectedRange` changes

//////////////////////////////////////////////

function initSlider() {
    noUiSlider.create(slider, {
        start: [ minVal, maxVal ],
        step: step,
        connect: true,
        range: selectedRange,
        handleAttributes: [
            { "id": handleHtmlIds[0] },
            { "id": handleHtmlIds[1] } ],
        pips: {
            mode: "steps",
            filter: (value, type) => [minVal,maxVal].includes(value) ? 1 : -1  // only display min/max values on the slider
        }
    });
    slider.noUiSlider.on("set", () => {
        let range = slider.noUiSlider.get(true);
        updateSelectedRange(range);
        dispatch("updateRange", range);
    })
}

// the TooltipGenerics that are bound to the slider's handle must be created in a declarative way to be positionned correctly in the DOM
function initHandleTooltips() {
    handleHtmlIds.map((htmlId, idx) => {
        handleTooltips.push(new TooltipGeneric({
            target: document.getElementById(htmlId),
            props: { tooltipText: idx===0 ? selectedRange.min : selectedRange.max }
        }));
    })
}

const updateSelectedRange = ([_min, _max]) => {
    oldSelectedRange.min = selectedRange.min;
    oldSelectedRange.max = selectedRange.max;
    selectedRange = { min: _min, max: _max };
}

// update the `TooltipGeneric.tooltipText` prop when a new value is set.
function updateHandleTooltip() {
    if ( handleTooltips.length && oldSelectedRange.min !== selectedRange.min )
        handleTooltips[0].$set({ tooltipText: selectedRange.min })
    if ( handleTooltips.length && oldSelectedRange.max !== selectedRange.max )
        handleTooltips[1].$set({ tooltipText: selectedRange.max })
}

//////////////////////////////////////////////

onMount(() => {
    initSlider();
    initHandleTooltips();
})
</script>


<div>
    <div class="slider-wrapper">
        <div class="slider" bind:this={slider}></div>
    </div>
</div>


<style>
.slider-wrapper {
    min-height: 15px;
    margin: 10px;
}
:global(.noUi-horizontal) {
    height: 5px;
}
:global(.noUi-horizontal .noUi-connects) {
    outline: solid 1px white;
}
:global(.noUi-horizontal .noUi-connect) {
    background-color: var(--default-color);
}
:global(.noUi-horizontal .noUi-handle) {
	width: 15px;
	height: 15px;
	right: -10px;
	top: -6px;
    border-radius: 1rem;
    background-color: var(--default-color);
    border: solid 2px white;
    box-shadow: none;
    cursor: grab;
}
:global(.noUi-horizontal .noUi-handle::before),
:global(.noUi-horizontal .noUi-handle::after) {
    all: unset;
}
</style>
