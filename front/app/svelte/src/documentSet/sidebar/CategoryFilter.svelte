<script>
    import CategoryButton from "../../regions/similarity/CategoryButton.svelte";

    export let categories;
    /** {category: nb of pairs} */
    export let counts = {};
    /** @type {Set<number>} */
    export let selected;
    export let toggle;
    export let disabled = false;
</script>

<div class="level is-mobile mb-0" class:is-disabled={disabled}>
    {#each categories as cat}
        <div class="level-item has-text-centered">
            <div>
                <CategoryButton category={cat} isSelected={selected.has(cat)} selectable={!disabled}
                                toggle={c => disabled || toggle(c)}/>
                <p class="is-size-7 mt-1">{counts[cat] || 0}</p>
            </div>
        </div>
    {/each}
</div>
