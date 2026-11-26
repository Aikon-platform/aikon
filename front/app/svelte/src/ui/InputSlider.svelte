<!--
    a slider with 1 or 2 inputs.
    - if there's only 1 input, it behaves like a normal `input @type="range"`
    - if there are 2 inputs, it's a range slider that allows to select a min/max.
    - number of inputs is determined by data passed to the props `start`:
        - if 1 number is provided, InputSlider is a 1-input slider.
        - if an array of [number, number] is provided, it's a 2-input slider.

    features:
    - define min, max, start values, step, round floats
    - emit on value update or on value set, thanks to props `emitOnUpdate`
    - complete UI interface, with title, tooltips etc
    - resetting the slider to its start state, using contexts (see below).

    emits:
    - "updateSlider" @type{number[]}. an array of 1 or 2 nu;bers, depending on if it's a 1 or 2 input slider

    good to know:
    - how is value resetting handled ?
        - an ancestor creates a `setContext` that holds a `writable`. by updating the `writable's` value, this component is reset
        - if several instances of `InputSlider` inherit the same component, they will all be reset when the parent sets a new value on `resetTrigger`
        - technical details: there are several more or less hacky patterns to trigger an update in a child component from the parent, from exporting a function in the child so that it can be called in the parent, to listening to prop changes, using stores etc (see: https://www.reddit.com/r/sveltejs/comments/np9qc0/send_event_from_a_parent_to_child/).
            using the context API has some advantages:
                - you can batch trigger functions in child components with a common ancestor: all child component auto-inherit from their ancestor's context. this fits our use case: in forms, we want a single `reset` button to reset all form inputs at once.
                - contrary to resetting using stores, resetting is isolated: several components can set their own `resetTrigger` contexts, and they will affect their descendant components only.`InputSlider` inheriting from other components will not be affected.
                - the context is just a trigger and is implementation independent. this means that the same trigger can be used to reset different inputs. in fact, `InputSlider`, `InputDropdown` and `InputToggle` all use the sane `resetTrigger`
                - the only problem will be if 2 ancestor components of a single input both call `setContext("resetTrigger")`. in those cases, the 2 ancestors will trigger a resetting of the same input,

    NOTE if the minVal/maxVal are updated through reactive props
        after the start value is set AND if the start value is above the maxVal
        then the start is defaulted to maxVal by noUiSlider
        if you receive range after initial value,
        better set min and max first way above expected start value
-->
<script>
    import { run } from 'svelte/legacy';
    import { onMount, onDestroy, createEventDispatcher, getContext, mount } from "svelte";

    import "nouislider/dist/nouislider.css";
    import noUiSlider from "nouislider";

    import TooltipGeneric from "./TooltipGeneric.svelte";
    import {makeTooltipGenericState} from "./tooltipGenericState.svelte";

    /** @typedef {import("./tooltipGenericState.svelte").TooltipGenericState} TooltipGenericState */

    /**
     * @typedef {Object} Props
     * @property {number} minVal
     * @property {number} maxVal
     * @property {number|number[]} start
     * @property {number?} [step]
     * @property {number?} [roundTo]
     * @property {string?} [title]
     * @property {boolean} [emitOnUpdate]
     */

    /** @type {Props} */
    let {
        minVal,
        maxVal,
        start,
        step = undefined,
        roundTo = 2,
        title = "",
        emitOnUpdate = false
    } = $props();

    const dispatch = createEventDispatcher();
    const sliderHtmlId = `slider-${crypto.randomUUID()}`;
    const isRange = Array.isArray(start) && start.length === 2 && start.every(n => !isNaN(parseFloat(n)));  // true if number, number

    const handleHtmlIds = isRange
        ? [crypto.randomUUID(), crypto.randomUUID()].map(id => `noUi-handle-${id}`)
        : [`noUi-handle-${crypto.randomUUID()}`];

    // noUiSlider object
    let slider = $state();
    // defined in onMount
    let handleTooltips = $state([]);

    /** @type {number | number[]} if isRange, [min,max] ; otherwise, 1 number*/
    let selectedVal = $state(start);

    /**
     * HTML IDs mapped to state, to dynamically update the tooltip's value whenever `selectedVal` changes
     * @type {{ [x: string]: TooltipGenericState }}
     */
    const tooltipStates = Object.fromEntries(
        handleHtmlIds.map(htmlId => [htmlId, makeTooltipGenericState()])
    )

    // when `selectedVal` is updated, update `tooltipStates`.
    $effect(() => {
        const values = Array.isArray(selectedVal) ? selectedVal : [selectedVal];
        handleHtmlIds.forEach((htmlId, i) =>
            tooltipStates[htmlId].tooltipText = values[i]
        );
    })

    let prevValue = null;
    let prevStart = $state(start);
    let prevRange = $state({ min: minVal, max: maxVal });

    // helpers

    /** @type {writable} the `resetTrigger` context stores a writable. we subscribe to the writable,
     * and when its value is updated, reset InputSlider
     */
    const resetTriggerContext = getContext("resetTrigger");
    resetTriggerContext?.subscribe(() => slider?.noUiSlider?.reset());

    const round = n => Number(n.toFixed(roundTo));
    const roundVal = v => Array.isArray(v) ? v.map(round) : round(v);
    const valuesEqual = (a, b) => isRange
        ? a?.[0] === b?.[0] && a?.[1] === b?.[1]
        : a === b;

    function handleSliderEvent(caller) {
        const val = roundVal(slider.noUiSlider.get(true));
        selectedVal = val;
        if (caller === "set" || emitOnUpdate) {
            if (!valuesEqual(val, prevValue)) {
                prevValue = val;
                dispatch("updateSlider", val);
            }
        }
    }

    // handle props being updated by parent

    // update range if minVal/maxVal change in the parent component
    $effect(() => {
        if (slider?.noUiSlider && (minVal !== prevRange.min || maxVal !== prevRange.max)) {
            prevRange = { min: minVal, max: maxVal };
            slider.noUiSlider.updateOptions({ range: { min: minVal, max: maxVal } }, false);
        }
    });

    // update start if the parent changes `start`
    $effect(() => {
        if (slider?.noUiSlider && !valuesEqual(roundVal(start), roundVal(prevStart))) {
            prevStart = start;
            slider.noUiSlider.set(start, false);
            selectedVal = roundVal(start);
        }
    });

    onMount(() => {
        slider = document.getElementById(sliderHtmlId);
        noUiSlider.create(slider, {
            start,
            step,
            connect: isRange ? true : "lower",
            range: { min: minVal, max: maxVal },
            handleAttributes: handleHtmlIds.map(id => ({ id }))
        });
        slider.noUiSlider.on("update", () => handleSliderEvent("update"));
        slider.noUiSlider.on("set", () => handleSliderEvent("set"));

        handleTooltips = handleHtmlIds.map((id, i) => mount(TooltipGeneric, {
            target: document.getElementById(id),
            props: { tooltipState: tooltipStates[id] }
        }));
    });

    onDestroy(() => slider?.noUiSlider?.destroy());
</script>

<div>
    <span>{title} ({selectedVal})</span>
    <div class="slider-outer-wrapper is-flex flex-direction-row">
        <span class="range-marker">{minVal}</span>
        <div class="slider-wrapper">
            <div class="slider" id={sliderHtmlId}></div>
        </div>
        <span class="range-marker">{maxVal}</span>
    </div>
</div>

<style>
    .slider-outer-wrapper {
        margin: 10px 10px 0;
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
        outline: solid 1px var(--accent);
    }

    :global(.noUi-horizontal .noUi-connect) {
        background-color: var(--bulma-link);
        transform: scale(1, 1.1);
    }

    :global(.noUi-horizontal .noUi-handle) {
        width: 15px;
        height: 15px;
        right: -10px;
        top: -5px;
        border-radius: 1rem;
        background-color: var(--bulma-link);
        border: solid 2px var(--bulma-border-weak);
        box-shadow: none;
        cursor: grab;
    }

    :global(.noUi-horizontal .noUi-handle::before),
    :global(.noUi-horizontal .noUi-handle::after) {
        all: unset;
    }

    :global(.noUi-target) {
        border: var(--bulma-border-weak) !important;
    }
</style>
