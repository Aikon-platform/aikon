<script>
    import { categoryInfo } from "./similarityCategory.js";

    export let selectedCategory = null;
    export let category;
    export let categorize = () => {};
    export let padding = "px-2";
</script>

<span class="tag py-4 {padding} {selectedCategory ? 'is-hoverable' : ''}" class:is-selected={selectedCategory === category}
      on:click={() => categorize(category)} on:keyup={null}
      title={categoryInfo[category].title}>
    {@html categoryInfo[category].svg}
</span>
