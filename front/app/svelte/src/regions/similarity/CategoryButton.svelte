<script>
    import { categoryInfo } from "./similarityCategory.js";

    export let selectable = true;
    export let isSelected = false;
    export let category;
    export let toggle = () => {};
    export let padding = "px-2";
</script>

<span class="tag py-4 {padding} {selectable ? 'is-hoverable' : ''}" class:is-selected={isSelected}
      on:click={() => toggle(category)} on:keyup={null} title={categoryInfo[category].title}>
    {@html categoryInfo[category].svg}
</span>
