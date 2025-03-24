<script>
import { createEventDispatcher } from "svelte";

export let checkboxLabel;
const htmlId = `input-input-checkbox-wrapper-${window.crypto.randomUUID()}`;
const dispatch = createEventDispatcher();

$: isChecked = false;

const toggleOnClick = () => {
    isChecked = !isChecked;
    dispatch("updateChecked", isChecked);
};
</script>

<div class="input-checkbox-wrapper button is-clickable
            {isChecked ? 'is-checked' : ''}"
>
    <span class="switch-wrapper">
        <span class="switch">
            <span class="switch-control">
                <input type="checkbox"
                       class="is-clickable"
                       id={htmlId}
                       name={htmlId}
                       on:click={toggleOnClick}
                />
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
