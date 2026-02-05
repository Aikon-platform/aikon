<!--
    emits:
    - "updateChecked" @type {boolean}

    good to know:
    - resetting is done by getting the `resetTrigger` context which holds a writable store, subscribing to it, and when it updates, triggering `resetInputCheckbox`
-->
<script>
    import { createEventDispatcher, getContext } from "svelte";

    ///////////////////////////////////////////

    /** @type {String} */
    export let toggleLabel;
    /** @type {Boolean} default value */
    export let start = false;
    /** @type {Boolean} button-like styling */
    export let buttonDisplay = false;

    const htmlId = `input-toggle-${window.crypto.randomUUID()}`;
    const dispatch = createEventDispatcher(resetInputCheckbox);

    const resetTriggerContext = getContext("resetTrigger") || undefined;
    resetTriggerContext?.subscribe(resetInputCheckbox);

    $: isChecked = start;
    $: dispatch("updateChecked", isChecked);

    ///////////////////////////////////////////

    const toggleOnClick = () => isChecked = !isChecked;

    function resetInputCheckbox() {
        isChecked = start;
    }
</script>

<button id={htmlId} name={htmlId}
        class="input-checkbox-wrapper is-flex is-align-items-center-is-justify-content-center p-2 pl-3 pr-3"
        class:is-checked={isChecked} class:is-clickable={buttonDisplay} class:button={buttonDisplay}
        aria-label={toggleLabel}
        on:click|preventDefault={toggleOnClick}
>
    <span class="switch mr-2">
        <span class="switch-control">
            <span class="switch-spot"></span>
        </span>
    </span>
    <span class="label">{toggleLabel}</span>
</button>

<style>
    .input-checkbox-wrapper {
        transition: background-color var(--default-transition);
    }
    .switch {
        /*display: inline-block;*/
        width: 35px;
        height: 17px;
        border-radius: 1rem;
        border: var(--default-border);
        background-color: var(--contrasted);
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .switch-control {
        background-color: white;
        display: inline-block;
        border-radius: 1rem;
        border: var(--default-border);
        height: 16px;
        width: 16px;
        transform: translateX(-60%);
        transition: transform .3s;
    }
    .is-checked .switch {
        background-color: var(--bulma-link);
    }
    .is-checked .switch-control {
        transform: translateX(55%);
    }
    .input-checkbox-wrapper .label {
        font-weight: var(--bulma-body-weight);
    }
</style>
