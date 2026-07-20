<script>
    import CategoryButton from "./CategoryButton.svelte";

    export let visibleCategories = [1, 2, 3, 4, 5];
    export let toggleFct = () => null;
    export let userToggleFct = () => null;
    export let selectedCategory = null;
    export let isSelectedByUser = false;
    export let horizontal = true;

    let paddingStart = horizontal ? "pl-3 pr-2" : "pt-3 pb-2";
    let paddingEnd = horizontal ? "pl-2 pr-3" : "pt-2 pb-3";
</script>

<div class="tags is-dark" class:has-addons={horizontal} class:vertical-addons={!horizontal} class:is-center={horizontal}>
    {#each visibleCategories as cat, i}
        <CategoryButton category={cat}
            padding={i === 0 ? paddingStart : i === visibleCategories.length -1 ? paddingEnd : ""}
            isSelected={cat === 5 ? isSelectedByUser : selectedCategory === cat}
            toggle={cat === 5 ? userToggleFct : toggleFct}/>
    {/each}
</div>
