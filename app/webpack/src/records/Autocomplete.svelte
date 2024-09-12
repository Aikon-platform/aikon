<script>
    import { createEventDispatcher } from 'svelte';
    import { appLang } from "../constants.js";

    export let items = [];
    export let placeholder = `${appLang === 'en' ? 'Select' : 'Sélectionner'} ...`;
    export let name = '';
    export let id = '';

    let inputValue = '';
    let filteredItems = [];
    let isOpen = false;
    let selectedIndex = -1;

    // TODO when emptying field, reset selectedIndex + selected ID
    // TODO when clicking once on the option to select, make autocomplete list disappear

    const dispatch = createEventDispatcher();

    $: {
        if (inputValue.length > 0) {
            filteredItems = items.filter(item =>
                item.label.toLowerCase().includes(inputValue.toLowerCase())
            );
            isOpen = true;
        } else {
            filteredItems = [];
            isOpen = false;
        }
    }

    function handleInput() {
        selectedIndex = -1;
    }

    function handleKeydown(event) {
        if (event.key === 'ArrowDown') {
            event.preventDefault();
            selectedIndex = (selectedIndex + 1) % filteredItems.length;
        } else if (event.key === 'ArrowUp') {
            event.preventDefault();
            selectedIndex = selectedIndex <= 0 ? filteredItems.length - 1 : selectedIndex - 1;
        } else if (event.key === 'Enter' && selectedIndex !== -1) {
            event.preventDefault();
            selectItem(filteredItems[selectedIndex]);
        }
    }

    function selectItem(item) {
        inputValue = item.label;
        isOpen = false;
        dispatch('select', item);
    }
</script>

<div class="autocomplete">
    <input class="input is-small is-wide" {name} {id}
           bind:value={inputValue} on:input={handleInput} on:keydown={handleKeydown}
           {placeholder} autocomplete="off"
    />
    {#if isOpen}
        <ul class="autocomplete-list is-wide">
            {#each filteredItems as item, index}
                <li class:selected={index === selectedIndex}
                    on:click={() => selectItem(item)} on:keyup={null}>
                    {item.label}
                </li>
            {/each}
        </ul>
    {/if}
</div>

<style>
    .autocomplete {
        position: relative;
    }

    input {
        padding: 8px;
    }

    .autocomplete-list {
        text-align: left;
        position: absolute;
        max-height: 200px;
        overflow-y: auto;
        border: 1px solid var(--bulma-border);
        border-top: none;
        border-radius: 0 0 4px 4px;
        background-color: var(--bulma-background);
        z-index: 1000;
        left: -25px;
        top: 17px;
        font-size: smaller;
    }

    li {
        padding: 8px;
        cursor: pointer;
    }

    li:hover, li.selected {
        background-color: var(--selected);
    }
</style>
