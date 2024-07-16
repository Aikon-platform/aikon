<script>
    import {similarityStore} from "./similarityStore.js";
    const { comparedRegions, isSelected } = similarityStore;
    // export let appLang = 'en';
    export let imgPrefix = '';

    function toggleSelection(region) {
        if ($isSelected(region.ref)) {
            similarityStore.unselect(region.ref);
        } else {
            similarityStore.select(region);
        }
    }

    function isSelf(regionId) {
        // is the region the same as the one being displayed on the current page?
        return regionId.startsWith(imgPrefix);
    }
</script>

<div class="field is-grouped is-grouped-multiline">
{#each Object.entries($comparedRegions) as [regionId, region]}
    <div class="tags has-addons mb-0 is-hoverable" on:click={() => toggleSelection(region)} on:keyup={null}>
        {#if isSelf(regionId)}
            <span class="tag is-dark">current</span>
        {/if}
        <span class="tag is-small {$isSelected(regionId) ? 'is-link' : 'is-contrasted'}">
            {region.title}
        </span>
    </div>
{/each}
</div>

<!--TODO add selection for all other regions existing-->
<!--TODO add button to toggle view for No-match similarities-->
<!--TODO add button to change number of displayed similarities-->

<style>
    span {
        cursor: pointer;
        transition: background-color 0.2s ease-out;
    }
</style>
