<!-- an implementation of a subset of items from Svelte-Select
    it implements specific styles and allows to provide an icon
    for each option.

    restrictions:
    - it is synchronous (no async data fetching)
    - it does not handle updates to props values
-->

<script>
import { onMount } from "svelte";

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
export let items = [];                 /** @type {DropdownItemArray} */
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

function insertIcons() {
    items.forEach(item => {
        let iconValue, iconType;
        if ( Object.keys(item).includes("iconifyId") && item.iconifyId != null ) {
            iconValue = item.iconifyId;
            iconType = "iconify";
        } else if ( Object.keys(item).includes("iconSvg") && item.iconSvg != null ) {
            iconValue = item.iconSvg;
            iconType = "svg";
        };
        if ( iconValue && iconType )  {

        }
    })
}

onMount(() => {

})

</script>


<div>
    <Select {placeholder}
            {items}
            {searchable}
            {multiple}
            {/*closeListOnChange*/}
            closeListOnChange={false}
            {...makeConditionalAttributes()}
    ></Select>
</div>


<style>

</style>
