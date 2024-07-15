<script>
    import {similarityStore} from "./similarityStore.js";
    const { comparedRegions, isSelected } = similarityStore;
    export let appLang = 'en';

    function toggleSelection(region) {
        console.log(region);
        if ($isSelected(region.ref)) {
            similarityStore.unselect(region.ref);
        } else {
            similarityStore.select(region);
        }
    }
</script>

{#each Object.entries($comparedRegions) as [regionId, region]}
    <span on:click={() => toggleSelection(region)} on:keyup={null}
          class="tag is-rounded is-small m-1 {$isSelected(regionId) ? 'is-link' : 'is-dark'}">
        {region.title}
    </span>
{/each}

<!--TODO add selection for all other regions existing-->

<style>
    span {
        cursor: pointer;
        transition: background-color 0.2s ease-out;
    }
</style>
