<!-- a svelte implementation of Choices.js.

    it handles
    - single and multi-choice dropdowns,
    - pre-selected choices
    - prefixes or svg icon icons for each option
    - adds specific styles
    - provides a lightDisplay option, for a more discreet view

    restrictions:
    - it is synchronous (no async data fetching)
    - it does not handle updates to props update
    - when passing a `defaultSelection`, the values
        each item of `defaultSelection` and `choices`
        (type DropdownChoice.value) must be hashable
        so that values in `defaultSelection` can be matched
        with `choices` items.
-->

<script>
import { onMount, onDestroy, createEventDispatcher } from "svelte";

import Choices from "choices.js";
import "choices.js/public/assets/styles/choices.css";

import { appLang } from "../constants";
    import { loop_guard } from "svelte/internal";

/////////////////////////////////////////////////////

/**
 * @typedef DropdownChoice
 *    structure of the "choices"
 * @property {Any} value
 * @property {String} label
 * @property {String?} group: group name for nested selects
 * @property {String?} prefix: string, svg or iconify identifier prefix a dropdown item
 * @property {'text'|'iconify'|'svg'?} prefixType:
 *      - 'text': prefix will be displayed as a string literal
 *      - 'iconfify': prefix will be treated as an iconify id and the corresponding icon will be displayed
 *      - 'svg': prefix is an svg and will be rendered
 */

/**
 * @typedef DropdownChoiceArray
 * @type {DropdownChoice[]}
 */

/** @type {DropdownChoiceArray} */
export let choices;
/** @type {DropdownChoice.value[]} the items selected by default, represented as an array of DropdownChoice.value */
export let defaultSelection = [];
/** @type {Boolean} */
export let multiple;
/** @type {String} */
export let searchable = true;
/** @type {Boolean} */
export let sort = true;
/** @type {Boolean} if true, UI will be lighter */
export let lightDisplay = false;
/** @type {String} */
export let placeholder = appLang === "fr" ? "Sélectionner une valeur" : "Select a value";

const dispatch = createEventDispatcher();
const htmlId = `input-dropdown-select-${window.crypto.randomUUID()}`;

/** @type {DropdownChoice.value[]} */
$: selectedValues = [];

/////////////////////////////////////////////////////

const toIconify = (iconifyId) => `<span class="iconify" data-icon=${iconifyId}/>`;

const prefixToHtml = (prefix, prefixType) =>
    prefix != null && prefixType != null && prefix.length && prefixType.length
    ? `<span class="dropdown-prefix-wrapper">${
        prefixType==="iconify" ? toIconify(prefix) : prefix
    }</span>`
    : ""

/**
 * generate a random UUID + add the icon. [...arr] copies instead of modifying in place.
 * @param {DropdownChoiceArray} arr
 */
const formatChoices = (arr) => [...arr].map(el => {
    el.id = `dropdown-choice-${window.crypto.randomUUID()}`;;
    el.label = `<span>
        ${prefixToHtml(el.prefix || "",  el.prefixType || "")}
        <span class="dropdown-prefix-text">${el.label}</span>
    </span>`;
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

/**
 * @param {DropdownChoiceArray} allChoices: all the available choices
 * @param {DropdownChoiceArray} preSelectedChoices: the pre-selected ones
 */
function initChoices(allChoices, preSelectedChoices) {
    const choicesTarget = document.getElementById(htmlId);
    const choicesObj = new Choices(choicesTarget, {
        items: [],  // setting preSelectedChoices here does not work, so they are set programatically below.
        choices: allChoices,
        addChoices: false,
        addItems: false,
        removeItems: true,
        removeItemButton: true,
        searchEnabled: searchable,
        shouldSort: sort,
        allowHTML: true,  // choices.some(c => c.hasOwnProperty("icon") && c.icon != null),
        sorter: () => choices.label,  // idk
        placeholderValue: placeholder,
        classNames: {
            item: ["choices__item", "dropdown-item"]
        },
        loadingText: appLang === "fr" ? 'Chargement...' : 'Loading...',
        noResultsText: appLang === "fr" ? "Pas de résultats" : 'No results found',
        noChoicesText: appLang === "fr" ? "Pas de choix pour faire la sélection" : 'No choices to choose from',
        itemSelectText: appLang === "fr" ? "Cliquer pour sélectionner" : 'Press to select',
        uniqueItemText: appLang === "fr" ? "Seules des valeurs uniques peuvent être ajoutées" : 'Only unique values can be added',
        customAddItemText: appLang === "fr" ? "Les valeurs ne répondent pas aux conditions attendues" : 'Only values matching specific conditions can be added',
        removeItemIconText: appLang === "fr" ? "Retirer l'item" : `Remove item`,
        addItemText: (value) =>
            appLang === "fr"
            ? `Cliquer sur Entrer pour ajouter <b>${value}</b>`
            : `Press Enter to add <b>"${value}"</b>`,
        removeItemLabelText: (value) =>
            appLang === "fr"
            ? `Retirer l'item: ${value}`
            : `Remove item: ${value}`,
        maxItemText: (maxItemCount) =>
            appLang === "fr"
            ? `Seulement ${maxItemCount} items peuvent être ajoutées`
            : `Only ${maxItemCount} items can be added`
    })

    console.log("pre", choicesObj.getValue());
    choicesObj.setValue(preSelectedChoices);
    console.log("post", choicesObj.getValue());

    choicesTarget.addEventListener("addItem", onAddItem);
    choicesTarget.addEventListener("removeItem", onRemoveItem)
}

/////////////////////////////////////////////////////

onMount(() => {
    let reformattedChoices = [], reformattedDefaultChoices = [];
    formatChoices(choices).map(c =>
        defaultSelection.includes(c.value)
        ? reformattedDefaultChoices.push({ ...c, selected: true })
        : reformattedChoices.push(c))
    initChoices(reformattedChoices, reformattedDefaultChoices);
})

onDestroy(() => {
    const choicesTarget = document.getElementById(htmlId);
    choicesTarget.removeEventListener("addItem", onAddItem);
    choicesTarget.removeEventListener("removeItem", onRemoveItem);
})
</script>


<div class="input-dropdown-select { lightDisplay ? 'light-display' : ''}">
    {#if multiple }
        <select id={htmlId} multiple></select>
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
    max-height: 45px;
    overflow: scroll;
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
/** `lightDisplay` specific options:
    - if the selected item has a prefix, hide the label and only display the prefix
*/
:global(.input-dropdown-select.light-display .choices__inner .choices__item[aria-selected="true"]:has(.dropdown-prefix-wrapper) .dropdown-prefix-text) {
    display: none;
}
/** dropdown style */
:global(.choices__list--dropdown) {
    z-index: 10 !important;
}
:global(.choices__list--dropdown .dropdown-item.is-highlighted) {
    background-color: var(--default-color) !important;
}
</style>
