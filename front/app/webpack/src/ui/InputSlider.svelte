<!--
    a slider with 1 or 2 inputs.
    - if there's only 1 input, it behaves like a normal `input @type="range"`
    - if there are 2 inputs, it's a range slider that allows to select a min/max.

    number of inputs is determined by data passed to the props `start`:
    - if 1 number is provided, InputSlider is a 1-input slider.
    - if an array of [Number, Number] is provided, it's a 2-input slider.

    restrictions:
    - updates to props are not handled.
-->
<script>
import { onMount, onDestroy, createEventDispatcher } from "svelte";

import noUiSlider from "nouislider";
import 'nouislider/dist/nouislider.css';

import TooltipGeneric from "./TooltipGeneric.svelte";

//////////////////////////////////////////////

/**
 * @typedef SelectedValType:
 *      the currently selected value(s) on the slider. data structure
 *      changes slightly depending on if we're building a 1-input or 2-input slider.
 * @type {Object}
 * @property {Boolean} isRange
 * @property {Number|Number[]} val:
 *      Number if not isRange, [Number, Number] otherwise.
 */

/** @type {Number} */
export let minVal;
/** @type {Number} */
export let maxVal;
/** @type {Number|Number[]} : default, pre-selecteed values. if 1 value is provided, then it's a single input slider. if an array of 2 values are provided, it's a min/max 2 input range slider */
export let start;
/** @type {Number?} */
export let step = undefined;
/** @type {Number?} number of floating points to keep after the decimal */
export let roundTo = 2;
/** @type {String?} title to give to the slider */
export let title = "";

//////////////////////////////////////////////

const dispatch = createEventDispatcher();

const sliderHtmlId = `slider-${window.crypto.randomUUID()}`;
const isRange = Array.isArray(start) && start.length === 2 && start.every(n => !isNaN(parseFloat(n)));  // true if Number, Number
const handleTooltips = [];
const oldSelectedVal = {
    isRange: isRange,
    data: start
};
const handleHtmlIds = isRange
    ? [ `noUi-handle-${window.crypto.randomUUID()}`,
        `noUi-handle-${window.crypto.randomUUID()}` ]
    : [ `noUi-handle-${window.crypto.randomUUID()}` ];

/** @type {SelectedValType} */
$: selectedVal = {
    isRange: isRange,
    data: start
};
$: updateHandleTooltip(selectedVal);  // run updateHandleTooltip when `selectedVal` changes

//////////////////////////////////////////////

const numRound = n => Number((n).toFixed(roundTo))

/** @param {Number[]|Number}: if isRange, then array of 2 values. else, 1 value. */
const updateSelectedRange = (val) => {
    oldSelectedVal.data = selectedVal.data || undefined;
    selectedVal = {
        isRange: isRange,
        data: Array.isArray(val) ? val.map(numRound) : numRound(val)
    };
}

// update the `TooltipGeneric.tooltipText` prop when selectedVal is updated.
function updateHandleTooltip() {
    if (
        isRange
        && handleTooltips.length
        && selectedVal.data[0] !== oldSelectedVal.data[0]
    ) {
        handleTooltips[0].$set({ tooltipText: selectedVal.data[0] })
    } else if (
        isRange
        && handleTooltips.length
        && selectedVal.data[1] !== oldSelectedVal.data[1]
    ) {
        handleTooltips[1].$set({ tooltipText: selectedVal.data[1] })
    } else if (
        !isRange
        && handleTooltips.length
        && selectedVal.data !== oldSelectedVal.data
    ) {
        handleTooltips[0].$set({ tooltipText: selectedVal.data })
    }
}

function initSlider() {
    const slider = document.getElementById(sliderHtmlId);
    noUiSlider.create(slider, {
        start: start,
        step: step,
        connect: isRange ? true : "lower",
        range: { min: minVal, max: maxVal },
        handleAttributes: handleHtmlIds.map((_id) => ({"id": _id }))  // 1 html ID per handle
    });
    // `selectedVal` is updated on update, and the parent component receives a new value on set.
    slider.noUiSlider.on("update", () => {
        let newVal = slider.noUiSlider.get(true);
        updateSelectedRange(newVal);
    });
    slider.noUiSlider.on("set", () => {
        // let newVal = slider.noUiSlider.get(true);
        dispatch("updateSlider", selectedVal);
    });
}

// the TooltipGenerics that are bound to the slider's handle must be created in a declarative way to be positionned correctly in the DOM
function initHandleTooltips() {
    handleHtmlIds.map((handleHtmlId, idx) => {
        handleTooltips.push(new TooltipGeneric({
            target: document.getElementById(handleHtmlId),
            props:
                isRange
                ? { tooltipText: idx===0 ? selectedVal.data[0] : selectedVal.data[1] }
                : { tooltipText: selectedVal.data }
        }));
    })
}

//////////////////////////////////////////////

onMount(() => {
    initSlider();
    initHandleTooltips();
})
onDestroy(() => {
    // very dirty destroy
    if (document.getElementById(sliderHtmlId))
        document.getElementById(sliderHtmlId).innerHTML = "";
})
</script>


<div>
    <span>{title} ({selectedVal.data})</span>
    <div class="slider-outer-wrapper is-flex flex-direction-row">
        <span class="range-marker">{ minVal }</span>
        <div class="slider-wrapper">
            <div class="slider" id={sliderHtmlId}></div>
        </div>
        <span class="range-marker">{ maxVal }</span>
    </div>
</div>


<style>
.slider-outer-wrapper {
    margin: 10px;
}
.slider-wrapper {
    min-height: 15px;
    width: 100%;
    margin: 0 15px;
}
.range-marker {
    transform: translateY(-40%);
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
