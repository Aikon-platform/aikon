<!-- an implementation of a subset of choices from Svelte-Select
    it implements specific styles and allows to provide an icon
    for each option.

    restrictions:
    - it is synchronous (no async data fetching)
    - it does not handle updates to props values
-->

<script>
import { onMount, onDestroy, createEventDispatcher } from "svelte";

import Choices from "choices.js";
import "choices.js/public/assets/styles/choices.css";

import { appLang } from "../constants";

/////////////////////////////////////////////////////

/**
 * @typedef DropdownChoice
 *    structure of the "choices"
 * @property {String} value:
 * @property {String} label:
 * @property {String?} group: group name for nested selects
 * @property {String?} icon: svg or iconify identifier for an icon to add to dropdown item
 * @property {Boolean?} iconify: if true, icon will be treated as an iconify id instead of an svg.
 */

 /**
 * @typedef DropdownChoiceArray
 * @type {DropdownChoice[]}
 */

export let choices;                    /** @type {DropdownChoiceArray} */
export let multiple;                   /** @type {Boolean} */
export let searchable = true;          /** @type {String} */
export let sort = true;                /** @type {Boolean} */
 /** @type {String} */
 export let placeholder = appLang === "fr" ? "Sélectionner une valeur" : "Select a value";

const dispatch = createEventDispatcher();
const htmlId = `input-dropdown-select-${window.crypto.randomUUID()}`;

$: selectedValues = [];  /** @type {DropdownChoice.value[]} */

/////////////////////////////////////////////////////

const toIconify = (iconifyId) => `<span class="iconify" data-icon=${iconifyId}/>`;

// generate a random UUID + add the icon.
const formatChoices = () => choices = choices.map(el => {
    el.id = `${window.crypto.randomUUID()}`;
    if ( el.hasOwnProperty("icon") && el.icon != null) {
        el.label = `<span>
            <span class="dropdown-icon-wrapper">${
                el.iconify===true ? toIconify(el.icon) : el.icon
            }</span>
            <span class="dropdown-icon-text">${el.label}</span>
        </span>`;
    }
    return el;
})

const onAddItem = (e) => {
    if ( multiple===true ) {
        const pos = selectedValues.indexOf(e.detail.value);
        pos === -1
        ? selectedValues.push(e.detail.value)
        : selectedValues.slice(pos, 1);
    } else {
        selectedValues = [e.detail.value];
    }
    dispatch("updateValues", selectedValues);
};

const onRemoveItem = (e) => {
    selectedValues = selectedValues.filter(s => s !== e.detail.value);
    dispatch("updateValues", selectedValues);
}

function initChoices() {
    const choicesTarget = document.getElementById(htmlId);
    new Choices(choicesTarget, {
        choices: choices,
        addChoices: false,
        addItems: false,
        removeItems: true,
        removeItemButton: true,
        searchEnabled: searchable,
        shouldSort: sort,
        allowHTML: choices.some(c => c.hasOwnProperty("icon") && c.icon != null),
        sorter: () => choices.label,  // idk
        placeholderValue: placeholder,
        classNames: {
            item: ["choices__item", "dropdown-item"]
        },
        loadingText: 'Loading...',
        noResultsText: appLang === "fr" ? "Pas de résultats" : 'No results found',
        noChoicesText: appLang === "fr" ? "Pas de choix pour faire la sélection" : 'No choices to choose from',
        itemSelectText: appLang === "fr" ? "Cliquer pour sélectionner" : 'Press to select',
        uniqueItemText: appLang === "fr" ? "Seules des valeurs uniques peuvent être ajoutées" : 'Only unique values can be added',
        customAddItemText: appLang === "fr" ? "Les valeurs ne répondent pas aux conditions attendues" : 'Only values matching specific conditions can be added',
        addItemText: (value) =>
            appLang === "fr"
            ? `Cliquer sur Entrer pour ajouter <b>${value}</b>`
            : `Press Enter to add <b>"${value}"</b>`,
    removeItemIconText: () => appLang === "fr" ? "Retirer l'item" : `Remove item`,
    removeItemLabelText: (value) =>
        appLang === "fr"
        ? `Retirer l'item: ${value}`
        : `Remove item: ${value}`,
    maxItemText: (maxItemCount) =>
        appLang === "fr"
        ? `Seulement ${maxItemCount} valeurs peuvent être ajoutées`
        : `Only ${maxItemCount} values can be added`
    })

    choicesTarget.addEventListener("addItem", onAddItem);  // TODO delete on destrooy
    choicesTarget.addEventListener("removeItem", onRemoveItem)
}

onMount(() => {
    formatChoices(choices);
    initChoices();
})
</script>


<div>
    {#if multiple }
        <select id={htmlId} multiple ></select>
    {:else }
        <select id={htmlId}></select>
    {/if}
</div>


<style>
/** basic styles */
:global(.choices__inner),
:global(.choiches__list--dropdown),
:global(.dropdown-item),
:global(.choices__inner .choices__input) {
    background-color: var(--bulma-body-background-color);
    color: var(--bulma-body-background);
    font-size: var(--bulma-body-font-size);
}
:global(.choices__list) {
    padding: 0;
}
/** selected items wrapper style */
:global(.choices__inner) {
    padding: 1px;
    padding-bottom: 1px !important;
    min-height: 30px;
    border: solid 1px var(--bulma-border);
    border-radius: var(--bulma-burger-border-radius);
}
/** selected item (single and multi) */
:global(.choices__inner .dropdown-item) {
    background-color: var(--default-color);
    color: var(--bulma-strong-color);
    border: var(--default-border);
    border-radius: 1rem;
    padding-left: 10px;
    font-weight: normal;
    font-size: 12px;
    margin: 3.75px;
}
/** selected item (multi placeholder) */
:global(.choices__item.choices__placeholder) {
    background-color: var(--bulma-body-background-color);
    color: var(--bulma-body-color);
    font-size: var(--bulma-body-font-size);
    border: none;
    margin: 0;
}
/** selected item (single placeholder) */
:global(.choices__input) {
    margin: 0;
    padding: 8px 0 8px 10px;
}
/** selected item (single) */
:global(.choices__list--single .choices__item) {
    width: fit-content;
}
:global(.choices__list--single .choices__button) {
    background-color: white;
}
/*
:global(.choices__inner .choices__item:not(-).choices__placeholder) {
    margin: 3.75px;
}
*/
/** dropdown style */
:global(.choices__list--dropdown) {
    z-index: 10 !important;
}
:global(.choices__list--dropdown .dropdown-item.is-highlighted) {
    background-color: var(--default-color) !important;
}

</style>
