<!-- a svelte implementation of Choices.js.

    emits:
    - `updateValues`
        @type {Array<Any>}
        the array of selected values

    it handles
    - single and multi-choice dropdowns,
    - pre-selected choices
    - select all / unselect all choices in the dropdown
    - prefixes or svg icon icons for each option
    - adds specific styles
    - provides a lightDisplay option, for a more discreet view

    restrictions:
    - it is synchronous (no async data fetching)
    - values in each `choices` and `start` objects MUST be scalable to allow comparisons
    - it does not handle updates to props update. tried to fix this
        several times and it is REALLY difficult to avoid weird feedback
        loops where updates in InputDropdown will trigger the parent to update
        the choices props, thus re-modifying InputDropdown.

    good to know:
    - this component provides a "selectAll" props. choices.js handles this by
        adding all choices one by one, which creates a lot of intermediate states
        on this component. to mitigate this, when `selectAll` is clicked,
        the emitting of events is blocked for a `ispatchLockDuration` ms.
        `bufferedDispatch` handles the lifecycle.
-->

<script>
import { onMount, onDestroy, createEventDispatcher } from "svelte";

import Choices from "choices.js";
import "choices.js/public/assets/styles/choices.css";

import { appLang } from "../constants";
import { createNewAndOld, equalArrayShallow } from "../utils";

import TooltipGeneric from "./TooltipGeneric.svelte";

/////////////////////////////////////////////////////

/** @typedef {import("../utils").NewAndOldType} NewAndOldType */

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

const htmlId = `input-dropdown-select-${window.crypto.randomUUID()}`;
const counterHtmlId = `input-dropdown-counter-${window.crypto.randomUUID()}`;
const selectAllValue = `select-all-${window.crypto.randomUUID()}`;  // the value of "(un)select all" option is an UUID to ensure that the value is not a duplicate of an other item in `choices`
const unSelectAllValue = `unselect-all-${window.crypto.randomUUID()}`;
const dispatchLockDuration = 250;

const dispatch = createEventDispatcher();

/** @type {NewAndOldType} */
const newAndOldSelectedValues = createNewAndOld();
newAndOldSelectedValues.setCompareFn(equalArrayShallow);

/** @type {Array} array of DropdownChoiceItem.value */
$: selectedValues = start || [];

/** @type {Array} temprarily toggled in `useDispatchLock`. when true, will block all requests */
$: dispatchLock = false;

// dispatching of selected elements to the parent component happens when `selectedValues` is updated and `dispatchLock` is set to false. this avoids intermediate calls to `dispatch` when selecting all elements.
$: bufferedDispatch(selectedValues, dispatchLock);

/////////////////////////////////////////////////////

const useDispatchLock = () => {
    dispatchLock = true;
    setTimeout(() => dispatchLock = false, dispatchLockDuration);
}

const bufferedDispatch = (_selectedValues, _dispatchLock) => {
    if ( !_dispatchLock ) {
        newAndOldSelectedValues.set(_selectedValues);
        if ( !newAndOldSelectedValues.same()  ) {
            dispatch("updateValues", selectedValues);
        }
    }
};

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
 * generate a random UUID + add the icon + add select all/remove all options. [...arr] copies instead of modifying in place.
 * @param {DropdownChoiceArray} arr
 * @param {boolean} _selectAll
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
 * update the global `choicesObj` and set `selectedValues`, which will trigger a dispatch of `updateValues` (see `bufferedDispatch`). this also handles "Select All" and "Unselect All" cases.
 *
 * things get weird when the props `selectAll` is true and the "Select All" button is clicked:
 * - "select all" clicked
 *      => `onAddItem`  called
 *          => "select all" and any other items that were previously selected are programatically removed from the select items
 *              => `onRemoveItem` called, once per item to remove
 *          => all objects from `allChoices` are programatically added
 *              => `onAddItem` called, once per item in `allChoices`. but then, the `selectAllValue===false` branch is called, unlike in the original `onAddItem`
 * => in practice, onAddItem will add all items twice. to mitigate this, when clicking on `Select All`,
 *  - [...new Set()] is used to deduplicate `localSelectedValues`.
 *  - `dispatchLock` is used to block all the `dispatch("updateValues")` that would be called when adding each individual item to `localSelectedValues`, until all items have been added
 *  - `bufferedDispatch()` will be called to `dispatch("updateValues")`, one `dispatchLock` is freed and all items have been added.
 * @param {Object} e
 * @param {DropdownChoiceArray} allChoices
 * @param {Choices} choicesObj
 */
const onAddItem = (e, allChoices, choicesObj) => {
    let localSelectedValues = [...selectedValues];  // avoid triggering side effects of `selectedValues`
    if (e.detail.value === selectAllValue) {
        useDispatchLock();
        // set `selectedValues` + unselect all previous choices and reselect all choices except the Select/Unselect ones.
        allChoices = allChoices.map(c =>
            [selectAllValue, unSelectAllValue].includes(c.value)
            ? ({ ...c, selected: false })
            : ({ ...c, selected: true })
        );
        choicesObj
            .removeActiveItems()
            .clearChoices(true, true)  // removes all choices, selected or not. without that, `setValue` will extend existing choices with allChoices instead of replacing.
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
    selectedValues = [...new Set(localSelectedValues)];
};

const onRemoveItem = (e) => {
    selectedValues = selectedValues.filter(s => s !== e.detail.value);
}


/**
 * @param {DropdownChoiceArray} allChoices: all the available choices
 * @param {boolean} _selectAll
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
