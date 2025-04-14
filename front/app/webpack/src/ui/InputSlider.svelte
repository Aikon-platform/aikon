<!--
    a slider with 1 or 2 inputs.
    - if there's only 1 input, it behaves like a normal `input @type="range"`
    - if there are 2 inputs, it's a range slider that allows to select a min/max.

    number of inputs is determined by data passed to the props `start`:
    - if 1 number is provided, InputSlider is a 1-input slider.
    - if an array of [number, number] is provided, it's a 2-input slider.

    restrictions:
    - updates to props are not handled.

    good to know:
    - thanks to `createNewAndOld`, values are only emitted when there's
        a change between the previously set value and the newly set value.
-->
<script>
import { onMount, onDestroy, createEventDispatcher } from "svelte";

import noUiSlider from "nouislider";
import 'nouislider/dist/nouislider.css';

import TooltipGeneric from "./TooltipGeneric.svelte";

import { createNewAndOld, equalArrayShallow } from "../utils";

/** @typedef {import("../utils").NewAndOldType} NewAndOldType */

//////////////////////////////////////////////

/**
 * @type {number|number[]} SelectedValType:
 *      the currently selected value(s) on the slider. data structure
 *      changes slightly depending on if we're building a 1-input or 2-input slider:
 *      number if not isRange, [number, number] otherwise.
 */

/** @type {number} */
export let minVal;
/** @type {number} */
export let maxVal;
/** @type {number|number[]} : default, pre-selecteed values. if 1 value is provided, then it's a single input slider. if an array of 2 values are provided, it's a min/max 2 input range slider */
export let start;
/** @type {number?} */
export let step = undefined;
/** @type {number?} number of floating points to keep after the decimal */
export let roundTo = 2;
/** @type {string?} title to give to the slider */
export let title = "";
/** @type {boolean} if true, emit on set + on update. else, emit only on set */
export let emitOnUpdate = false;

//////////////////////////////////////////////

const dispatch = createEventDispatcher();

const sliderHtmlId = `slider-${window.crypto.randomUUID()}`;
const isRange = Array.isArray(start) && start.length === 2 && start.every(n => !isNaN(parseFloat(n)));  // true if number, number
const handleTooltips = [];
const handleHtmlIds = isRange
    ? [ `noUi-handle-${window.crypto.randomUUID()}`,
        `noUi-handle-${window.crypto.randomUUID()}` ]
    : [ `noUi-handle-${window.crypto.randomUUID()}` ];

/** @type {NewAndOldType} tracks changes on "set" */
const newAndOldSelectedVal = createNewAndOld();
newAndOldSelectedVal.setCompareFn(isRange ? equalArrayShallow : (x,y) => numRound(x)===numRound(y));
newAndOldSelectedVal.set(start);

/** @type {number} tracks changes on "update" */
$: selectedVal = start;
$: updateHandleTooltip(selectedVal);

//////////////////////////////////////////////

const numRound = n => Number((n).toFixed(roundTo))

/**
 * @param {number[]|number} val: if isRange, then array of 2 values. else, 1 value.
 * @param {"update"|"set"} caller: on which event the function is called: `newAndOldSelectedVal` is only updated on set.
 */
const updateSelectedValAndDispatch = (val, caller) => {
    const updateHook = (_val) => {
        newAndOldSelectedVal.set(_val);
        if ( !newAndOldSelectedVal.same() ) {
            dispatch("updateSlider", newAndOldSelectedVal.get());
        }
    }
    val = Array.isArray(val) ? val.map(numRound) : numRound(val);
    selectedVal = val;
    if (caller==="set" || (caller==="update" && emitOnUpdate)) {
        updateHook(val)
    }
}

// update the `TooltipGeneric.tooltipText` prop when selectedVal is updated.
function updateHandleTooltip(_selectedVal) {
    if ( handleTooltips.length ) {
        handleTooltips.map((tooltip, idx) =>
            tooltip.$set({ tooltipText: isRange ? _selectedVal[idx] : _selectedVal }));
    }
}

function initSlider() {
    const slider = document.getElementById(sliderHtmlId);
    let newVal;
    noUiSlider.create(slider, {
        start: start,
        step: step,
        connect: isRange ? true : "lower",
        range: { min: minVal, max: maxVal },
        handleAttributes: handleHtmlIds.map((_id) => ({"id": _id }))  // 1 html ID per handle
    });
    // `selectedVal` is updated on update, and the parent component receives a new value on set.
    slider.noUiSlider.on("update", () => {
        newVal = slider.noUiSlider.get(true);
        updateSelectedValAndDispatch(newVal, "update");
    });
    slider.noUiSlider.on("set", () => {
        newVal = slider.noUiSlider.get(true)
        updateSelectedValAndDispatch(newVal, "set");
    });
}

// the TooltipGenerics that are bound to the slider's handle must be created in a declarative way to be positionned correctly in the DOM
function initHandleTooltips() {
    handleHtmlIds.map((handleHtmlId, idx) => {
        handleTooltips.push(new TooltipGeneric({
            target: document.getElementById(handleHtmlId),
            props:
                isRange
                ? { tooltipText: selectedVal[idx] }
                : { tooltipText: selectedVal }
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
    if (document.getElementById(sliderHtmlId)) {
        document.getElementById(sliderHtmlId).innerHTML = "";
    }
})
</script>


<div>
    <span>{title} ({selectedVal})</span>
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
