<script>
import { createEventDispatcher } from "svelte";

export let checkboxLabel;
const htmlId = `input-pill-checkbox-${window.crypto.randomUUID()}`;
const dispatch = createEventDispatcher();

$: isChecked = false

const toggleOnClick = () => {
    isChecked = !isChecked;
    dispatch("updateChecked", isChecked);
};
</script>

<div class="pill-checkbox checkbox-wrapper tag is-clickable
            { isChecked ? 'is-success' : 'is-link' }"
>
    <label for={htmlId} class=" is-clickable">{checkboxLabel}</label>
    <input type="checkbox"
           id={htmlId}
           name={htmlId}
           on:click={toggleOnClick}
    />
</div>


<style>
.pill-checkbox {
    transition: background-color var(--default-transition);
}
.pill-checkbox input {
    visibility: hidden;
    height: 0;
    width: 0;
}
</style>
