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
    export let checkboxLabel;
    /** @type {Boolean} default value */
    export let start = false;
    /** @type {Boolean} button-like styling */
    export let buttonDisplay = false;

    const htmlId = `input-input-checkbox-wrapper-${window.crypto.randomUUID()}`;
    const dispatch = createEventDispatcher(resetInputCheckbox);

    const resetTriggerContext = getContext("resetTrigger") || undefined;
    resetTriggerContext?.subscribe(resetInputCheckbox);

    $: isChecked = start;
    $: dispatch("updateChecked", isChecked);

    ///////////////////////////////////////////

    const toggleOnClick = () => isChecked = !isChecked;

    function resetInputCheckbox() {
        const el = document.getElementById(htmlId);
        if (el) el.checked = start;
    }
</script>

<div class="input-checkbox-wrapper
            { buttonDisplay ? 'button is-clickable' : 'is-flex is-align-items-center is-justify-content-center' }
            { isChecked ? 'is-checked' : '' }"
>
    <span class="switch-wrapper">
        <span class="switch">
            <span class="switch-control">
                {#if start===true }
                    <input type="checkbox"
                           class="is-clickable"
                           id={htmlId}
                           name={htmlId}
                           on:click={toggleOnClick}
                           checked
                    />
                {:else}
                    <input type="checkbox"
                           class="is-clickable"
                           id={htmlId}
                           name={htmlId}
                           on:click={toggleOnClick}
                     />
                {/if}
            </span>
        </span>
    </span>
    <label for={htmlId}
           class="is-clickable"
    >{checkboxLabel}</label>
</div>

<style>
    .input-checkbox-wrapper {
        transition: background-color var(--default-transition);
    }
    .switch {
        display: inline-block;
        width: 35px;
        height: 17px;
        border-radius: 1rem;
        border: var(--default-border);
        background-color: var(--contrasted);
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 5px;
        transform: background-color 0.7s;
    }
    .switch-control {
        background-color: white;
        display: inline-block;
        border-radius: 1rem;
        border: var(--default-border);
        height: 16px;
        width: 16px;
        transform: translateX(-60%);
        transition: transform var(--default-transition);
    }
    .is-checked .switch {
        background-color: var(--bulma-link);
    }
    .is-checked .switch-control {
        transform: translateX(55%);
    }
    .input-checkbox-wrapper input {
        opacity: 0;
        height: 100%;
        width: 100%;
    }
    .input-checkbox-wrapper label {
        font-weight: var(--bulma-body-weight);
    }
</style>
