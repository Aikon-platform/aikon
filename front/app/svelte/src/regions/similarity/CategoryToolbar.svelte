<script>
    import CategoryButton from "./CategoryButton.svelte";


    /**
     * @typedef {Object} Props
     * @property {any} [visibleCategories]
     * @property {any} [toggleFct]
     * @property {any} [userToggleFct]
     * @property {number|number[]|null} [selectedCategory]
     * @property {boolean} [isSelectedByUser]
     * @property {boolean} [horizontal]
     */

    /** @type {Props} */
    let {
        visibleCategories = [1, 2, 3, 4, 5],
        toggleFct = () => null,
        userToggleFct = () => null,
        selectedCategory = null,
        isSelectedByUser = false,
        horizontal = true
    } = $props();

    let paddingStart = horizontal ? "pl-3 pr-2" : "pt-3 pb-2";
    let paddingEnd = horizontal ? "pl-2 pr-3" : "pt-2 pb-3";
</script>

<div class="tags is-dark" class:has-addons={horizontal} class:vertical-addons={!horizontal} class:is-center={horizontal}>
    {#each visibleCategories as cat, i}
        <CategoryButton category={cat}
            padding={i === 0 ? paddingStart : i === visibleCategories.length -1 ? paddingEnd : ""}
            isSelected={cat === 5 ? isSelectedByUser : [].concat(selectedCategory).includes(cat)}
            toggle={cat === 5 ? userToggleFct : toggleFct}/>
    {/each}
</div>
