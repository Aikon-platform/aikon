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

    restrictions:
    - updates to props are not handled.

    good to know:
    - thanks to `createNewAndOld`, values are only emitted when there's a change between the previously set value and the newly set value.
    - how is value resetting handled ?
        - an ancestor creates a `setContext` that holds a `writable`. by updating the `writable's` value, this component is reset
        - if several instances of `InputSlider` inherit the same component, they will all be reset when the parent sets a new value on `resetTrigger`
        - technical details: there are several more or less hacky patterns to trigger an update in a child component from the parent, from exporting a fumction in the child so that it can be called in the parent, to listening to prop changes, using stores etc (see: https://www.reddit.com/r/sveltejs/comments/np9qc0/send_event_from_a_parent_to_child/).
            using the context API has some advantages:
                - you can batch trigger functions in child components with a common ancestor: all child component auto-inherit from their ancestor's context. this fits our use case: in forms, we want a single `reset` button to reset all form inputs at once.
                - contrary to resetting using stores, resetting is isolated: several components can set their own `resetTrigger` contexts, and they will affect their descendant components only.`InputSlider` inheriting from other compomnents will not be affected.
                - the context is just a trigger and is implementation independant. this means that the same trigger can be used to reset different inputs. in fact, `InputSlider`, `InputDropdown` and `InputToggle` all use the sane `resetTrigger`
                - the only problem will be if 2 ancestor components of a single input both call `setContext("resetTrigger")`. in those cases, the 2 ancestors will trigger a resetting of the same input,
-->
<script>
    import { onMount, onDestroy, createEventDispatcher, getContext } from "svelte";

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

    /** @type {writable} the `resetTrigger` context stores a writable. we subscribe to the writable, and when its value is updated, reset InputSlider */
    const resetTriggerContext = getContext("resetTrigger") || undefined;
    resetTriggerContext?.subscribe(resetInputSlider);

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
        val = Array.isArray(val) ? val.map(numRound) : numRound(val);
        selectedVal = val;
        if (caller==="set" || (caller==="update" && emitOnUpdate)) {
            newAndOldSelectedVal.set(val);
            if ( !newAndOldSelectedVal.same() ) {
                dispatch("updateSlider", newAndOldSelectedVal.get());
            }
        }
    }

    // update the `TooltipGeneric.tooltipText` prop when selectedVal is updated.
    function updateHandleTooltip(_selectedVal) {
        if ( handleTooltips.length ) {
            handleTooltips.map((tooltip, idx) =>
                tooltip.$set({ tooltipText: isRange ? _selectedVal[idx] : _selectedVal }));
        }
    }

    function resetInputSlider() {
        const slider = document.getElementById(sliderHtmlId);
        if ( slider?.noUiSlider ) { slider.noUiSlider.reset(); }
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
        margin-bottom: 0;
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
