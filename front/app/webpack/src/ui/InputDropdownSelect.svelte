<!-- an implementation of a subset of items from Svelte-Select.
    so far, it is synchronous (no async data fetching) and does
    not work with groups
-->

<script>
import Select  from "svelte-select";

import { appLang } from "../constants";

/////////////////////////////////////////////////////

/**
 * @typedef DropdownItem
 *    structure of the "items" that extends https://www.npmjs.com/package/svelte-select?activeTab=readme#props
 *    with the possibility to style an item
 * @property {String} value:
 * @property {String} label:
 * @property {String?} group: group name for nested selects
 * @property {String?} iconifyId: iconify identifier for an icon to add to dropdown item
 * @property {String?} iconSvg: svg-as-string of an icon
 */

 /**
 * @typedef DropdownItemArray
 * @type {DropdownItem[]}
 */

 /** @type {String} */
export let placeholder = appLang === "fr" ? "Sélectionner une valeur" : "Select a value";
export let items;                    /** @type {DropdownItemArray} */
export let multiple = false;           /** @type {Boolean} */
export let searchable = true;          /** @type {String} */
export let name;                       /** @type {String} */
export let closeListOnChange = true;   /** @type {Boolean} */

/////////////////////////////////////////////////////

// attributes that may be used if props but should not be used otherwise can be defined here
function makeConditionalAttributes() {
    let conditionalAttributes;
    if (multiple) conditionalAttributes.groupBy = (item) => item.group
    if (name) conditionalAttributes.name = name;
    return conditionalAttributes
}

</script>


<div>
    <Select {placeholder}
            {items}
            {searchable}
            {multiple}
            {closeListOnChange}
            {...makeConditionalAttributes()}
    ></Select>
</div>


<style>

</style>
