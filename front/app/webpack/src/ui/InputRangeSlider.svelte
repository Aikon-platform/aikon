<script>
import { onMount, createEventDispatcher } from "svelte";

import noUiSlider from "nouislider";
import 'nouislider/dist/nouislider.css';

//////////////////////////////////////////////

export let minVal;                  /** @type {Number} */
export let maxVal;                  /** @type {Number} */
export let step = 1;                /** @type {Number} */

let slider;
const dispatch = createEventDispatcher();

$: selectedRange = { min:minVal, max:maxVal };
$: noUiHandlesHtmlIds = [
    `noUi-handle-${window.crypto.randomUUID()}`,
    `noUi-handle-${window.crypto.randomUUID()}` ];

//////////////////////////////////////////////

const updateSelectedRange = ([_min, _max]) => {
    selectedRange = { min: _min, max: _max };
    console.log("called it", [_min, _max], selectedRange);
}

function initSlider() {
    noUiSlider.create(slider, {
        start: [ minVal, maxVal ],
        step: step,
        connect: true,
        range: selectedRange,
        handleAttributes: [
            { "id": noUiHandlesHtmlIds[0] },
            { "id": noUiHandlesHtmlIds[1] } ]
    });
    slider.noUiSlider.on("set", () => {
        let range = slider.noUiSlider.get(true);
        updateSelectedRange(range);
        dispatch("updateRange", range);
    })

}

//////////////////////////////////////////////

onMount(() => {
    initSlider()
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
}
:global(.noUi-horizontal .noUi-handle::before),
:global(.noUi-horizontal .noUi-handle::after) {
    all: unset;
}
</style>
