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
-->
<script>
    import { onMount, onDestroy, createEventDispatcher, getContext } from "svelte";
    import noUiSlider from "nouislider";
    import 'nouislider/dist/nouislider.css';
    import TooltipGeneric from "./TooltipGeneric.svelte";

    /** @type {number} */
    export let minVal;
    /** @type {number} */
    export let maxVal;
    /** @type {number|number[]}
     * default, pre-selected values. if 1 value is provided, then it's a single input slider.
     * if an array of 2 values is provided, it's a min/max 2 input range slider */
    export let start;
    /** @type {number?} */
    export let step = undefined;
    /** @type {number?} number of floating points to keep after the decimal */
    export let roundTo = 2;
    /** @type {string?} title to give to the slider */
    export let title = "";
    /** @type {boolean} if true, emit on set + on update. else, emit only on set */
    export let emitOnUpdate = false;

    const dispatch = createEventDispatcher();
    const sliderHtmlId = `slider-${crypto.randomUUID()}`;
    const isRange = Array.isArray(start) && start.length === 2 && start.every(n => !isNaN(parseFloat(n)));  // true if number, number
    const handleHtmlIds = isRange
        ? [crypto.randomUUID(), crypto.randomUUID()].map(id => `noUi-handle-${id}`)
        : [`noUi-handle-${crypto.randomUUID()}`];

    /** @type {writable} the `resetTrigger` context stores a writable. we subscribe to the writable,
     * and when its value is updated, reset InputSlider */
    const resetTriggerContext = getContext("resetTrigger");
    resetTriggerContext?.subscribe(() => slider?.noUiSlider?.reset());

    let slider;
    let handleTooltips = [];
    let selectedVal = start;
    let prevValue = null;
    let prevStart = start;
    let prevRange = { min: minVal, max: maxVal };

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

    // update range if minVal/maxVal change in the parent component
    $: if (slider?.noUiSlider && (minVal !== prevRange.min || maxVal !== prevRange.max)) {
        prevRange = { min: minVal, max: maxVal };
        slider.noUiSlider.updateOptions({ range: { min: minVal, max: maxVal } }, false);
        // NOTE if the minVal/maxVal are updated through reactive props
        // NOTE after the start value is set AND if the start value is above the maxVal
        // NOTE then the start is defaulted to maxVal by noUiSlider
        // NOTE if you receive range after initial value,
        // NOTE better set min and max first way above expected start value
    }

    // update start if value passed to props change in the parent component
    $: if (slider?.noUiSlider && !valuesEqual(roundVal(start), roundVal(prevStart))) {
        prevStart = start;
        slider.noUiSlider.set(start, false);
        selectedVal = roundVal(start);
    }

    $: handleTooltips.forEach((tooltip, i) =>
        tooltip.$set({ tooltipText: isRange ? selectedVal[i] : selectedVal })
    );

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

        handleTooltips = handleHtmlIds.map((id, i) => new TooltipGeneric({
            target: document.getElementById(id),
            props: { tooltipText: isRange ? selectedVal[i] : selectedVal }
        }));
    });

    onDestroy(() => slider?.noUiSlider?.destroy());
</script>

<div>
    <span>{title} ({selectedVal})</span>
    <div class="slider-outer-wrapper is-flex flex-direction-row">
        <span class="range-marker">{minVal}</span>
        <div class="slider-wrapper">
            <div class="slider" id={sliderHtmlId}/>
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
