<!-- a svelte implementation of Choices.js.

    it handles
    - single and multi-choice dropdowns,
    - pre-selected choices
    - select all / unselect all choices in the dropdown
    - prefixes or svg icon icons for each option
    - adds specific styles
    - provides a lightDisplay option, for a more discreet view

    restrictions:
    - it is synchronous (no async data fetching)
    - it does not handle updates to props update. tried to fix this
        several times and it is REALLY difficult to avoid weird feedback
        loops where updates in InputDropdown will trigger the parent to update
        the choices props, thus re-modifying InputDropdown.
    - when passing a `start`, the values
        each item of `start` and `choices`
        (type DropdownChoice.value) must be hashable
        so that values in `start` can be matched
        with `choices` items.
-->

<script>
import { onMount, onDestroy, createEventDispatcher } from "svelte";

import Choices from "choices.js";
import "choices.js/public/assets/styles/choices.css";

import { appLang } from "../constants";

import TooltipGeneric from "./TooltipGeneric.svelte";

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
export let start = [];
/** @type {Boolean} */
export let multiple;
/** @type {String} */
export let searchable = true;
/** @type {Boolean} if true, UI will be lighter */
export let lightDisplay = false;
/** @type {String} */
export let placeholder = appLang === "fr" ? "Sélectionner une valeur" : "Select a value";
/** @type {String?} */
export let title = undefined;
/** @type {Boolean} if True, extra "Select All" and "Unselect All" options will be preprended to `choices`. clicking on them will (un)select all choices. by default, true for multi-choice, false for single-choice */
export let selectAll = multiple ? true : false;

const dispatch = createEventDispatcher();

const htmlId = `input-dropdown-select-${window.crypto.randomUUID()}`;
const counterHtmlId = `input-dropdown-counter-${window.crypto.randomUUID()}`;
const selectAllValue = `select-all-${window.crypto.randomUUID()}`;  // the value of "(un)select all" option is an UUID to ensure that the value is not a duplicate of an other item in `choices`
const unSelectAllValue = `unselect-all-${window.crypto.randomUUID()}`;

/** @type {boolean} when true, this will block the dispatch of `updateValues` to parent. */
let blockEmit = false;

/** @type {DropdownChoice.value[]} */
$: selectedValues = start || [];
$: displayCountTooltip = false;

/////////////////////////////////////////////////////

const toIconify = (iconifyId) => `<span class="iconify" data-icon=${iconifyId}/>`;

const prefixToHtml = (prefix, prefixType) =>
    prefix != null && prefixType != null && prefix.length && prefixType.length
    ? `<span class="dropdown-prefix-wrapper">${
        prefixType==="iconify" ? toIconify(prefix) : prefix
    }</span>`
    : "";

const maybeAddSelectAllAndCopy = (arr, _selectAll) =>
    _selectAll
    ? [
        {
            value: selectAllValue,
            label: `<b>${appLang==="fr" ? "Tout sélectionner" : "Select all"}</b>`
        }, {
            value: unSelectAllValue,
            label: `<b>${appLang==="fr" ? "Tout retirer" : "Remove all"}</b>`
        }, ...arr]
    : [...arr];

/**
 * generate a random UUID + add the icon. [...arr] copies instead of modifying in place.
 * @param {DropdownChoiceArray} arr
 */
const formatChoices = (arr, _selectAll) =>
    maybeAddSelectAllAndCopy(arr, _selectAll)
    .map(el => {
        el.id = `dropdown-choice-${window.crypto.randomUUID()}`;;
        el.label = `<span>
            ${prefixToHtml(el.prefix || "",  el.prefixType || "")}
            <span class="dropdown-prefix-text">${el.label}</span>
        </span>`;
        return el;
    });

/**
 * emit "updateValues" when adding an item. this also handles "Select All" and "Unselect All" cases.
 *
 * things get weird when `selectAll` is true and the "Select All" button is clicked:
 * - "select all" clicked
 *      => `onAddItem`  called
 *          => "select all" and any other items that were previously selected are programatically removed from the select items (to avoid emitting them to the parent)
 *              => `onRemoveItem` called, once per item to remove
 *          => all objects from `allChoices` are programatically added
 *              => `onAddItem` called, once per item in `allChoices`. but then, the `selectAllValue===false` branch is called, unlike in the original `onAddItem`
 * => in practice, onAddItem will add all items twice, hence the use of [...new Set()] to deduplicate.
 * @param {Object} e
 * @param {DropdownChoiceArray} allChoices
 * @param {Choices} choicesObj
 */
const onAddItem = (e, allChoices, choicesObj) => {
    let localSelectedValues = [...selectedValues];  // avoid triggering side effects of `selectedValues`
    if (e.detail.value === selectAllValue) {
        blockEmit = true;
        setTimeout(() => blockEmit = false, 500);

        // set `selectedValues` + unselect all previous choices and reselect all choices except the Select/Unselect ones.
        allChoices = allChoices.map(c =>
            c.value !== selectAllValue && c.value !== unSelectAllValue
            ? ({ ...c, selected: true })
            : ({ ...c, selected: false })
        );
        choicesObj
            .removeActiveItems()
            .setValue(allChoices)
            .hideDropdown();
        localSelectedValues = [...new Set(
            allChoices
            .filter(c => c.selected===true)
            .map(c => c.value)
        )];
    } else if (e.detail.value === unSelectAllValue) {
        choicesObj
            .removeActiveItems()
            .hideDropdown();
        localSelectedValues = [];
    } else {
        localSelectedValues =
            multiple===true
            ? [...localSelectedValues, e.detail.value]
            : [e.detail.value];
    }

    // see docstring: when clicking on "Select All", further deduplication is needed
    selectedValues = [...new Set(localSelectedValues)];
    if ( !blockEmit ) {
        dispatch("updateValues", selectedValues);
    }
};

const onRemoveItem = (e) => {
    selectedValues = selectedValues.filter(s => s !== e.detail.value);
    dispatch("updateValues", selectedValues);
}


/**
 * @param {DropdownChoiceArray} allChoices: all the available choices
 */
function initChoices(allChoices, _selectAll) {
    // all items in allChoices with `selected: true` will be automatically pre-selected as items.
    allChoices = formatChoices(allChoices, _selectAll).map(c =>
        start.includes(c.value)
        ? ({ ...c, selected: true })
        : ({ ...c, selected: false })
    )

    const choicesTarget = document.getElementById(htmlId);
    const choicesObj = new Choices(choicesTarget, {
        items: [],
        choices: allChoices,
        addChoices: false,
        addItems: false,
        removeItems: true,
        removeItemButton: true,
        searchEnabled: searchable,
        allowHTML: true,
        shouldSort: _selectAll ? false : true,  // if selectAll, then "Select all" "Remove all" should be on top.
        sorter: (a,b) => a.label.localeCompare(b.label),  // alpanumeric sorting
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

    choicesTarget.addEventListener("addItem", (e) => onAddItem(e, allChoices, choicesObj));
    choicesTarget.addEventListener("removeItem", (e) => onRemoveItem(e))
}

/////////////////////////////////////////////////////

onMount(() => {
    initChoices(choices, selectAll);
})

onDestroy(() => {
    // const choicesTarget = document.getElementById(htmlId);
    // choicesTarget.removeEventListener("addItem", onAddItem);
    // choicesTarget.removeEventListener("removeItem", onRemoveItem);
})
</script>


<div class="input-dropdown-select-wrapper">
    {#if title!==undefined }
        <label for={htmlId}>{title}</label>
    {/if}
    <div class="input-dropdown-select
                { multiple ? 'is-multiple' : 'is-single' }
                { multiple && selectedValues.length ? 'is-flex is-justify-content-flex-start is-align-items-center' : ''}
                { lightDisplay ? 'light-display' : ''}"
    >
        {#if multiple }
            {#if selectedValues.length }
                <span class="is-relative">
                    <span id={counterHtmlId}
                        class="input-dropdown-count tag m-1"
                    >{ selectedValues.length }</span>
                    <TooltipGeneric
                        targetHtmlId={counterHtmlId}
                        tooltipText={`${selectedValues.length}
                                    ${ appLang==="fr" && selectedValues.length > 1
                                    ? "valeurs sélectionnées"
                                    : appLang==="fr" && selectedValues.length === 1
                                    ? "valeur sélectionnée"
                                    : appLang==="en" && selectedValues.length > 1
                                    ? "selected values"
                                    : "selected value"
                                    }`}
                    ></TooltipGeneric>
                </span>
            {/if }
            <select id={htmlId}
                    name={htmlId}
                    aria-label={title}
                    class="m-1"
                    multiple
            ></select>
        {:else }
            <select id={htmlId}
                    name={htmlId}
                    aria-label={title}
                    class="m-1"
            ></select>
        {/if}
    </div>

</div>


<style>
.input-dropdown-count {
    border-radius: 1rem;
    border: var(--default-border);
}
.input-dropdown-select.is-multiple :global(.choices) {
    flex-grow: 2;
}

/** CHOICES.JS STYLING */
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
:global(.choices__list--dropdown) {
    z-index: 7;
}
/** selected items wrapper style */
:global(.choices__inner) {
    padding: 1px;
    padding-bottom: 1px !important;
    min-height: 30px;
    max-height: 40px;
    overflow: scroll;
    border: solid 1px var(--bulma-border);
    border-radius: var(--bulma-burger-border-radius);
}
/** selected item (single and multi) */
:global(.choices__inner .dropdown-item) {
    background-color: var(--default-color);
    color: white;
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
    color: white;
}
</style>
