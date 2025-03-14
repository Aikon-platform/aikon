<script>
import { onMount, createEventDispatcher } from "svelte";

import noUiSlider from "nouislider";
import 'nouislider/dist/nouislider.css';

//////////////////////////////////////////////

export let minVal;                  /** @type {Number} */
export let maxVal;                  /** @type {Number} */
export let step = 1;                /** @type {Number} */
// export let numberType = "integer";  /** @type {"integer"|"float"} */

let slider;
const dispatch = createEventDispatcher();

$: selectedRange = { min:minVal, max:maxVal };

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
        range: selectedRange
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

</style>
