<script>
    import { getContext } from 'svelte';
    import { appLang } from '../../constants';
    import { similarityStore } from "./similarityStore.js";
    const { comparedRegions, isSelected } = similarityStore;

    const imgPrefix = getContext('imgPrefix');

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
            <span class="tag is-dark">{appLang === 'en' ? 'current' : 'courant'}</span>
        {/if}
        <span class="tag is-small {$isSelected(regionId) ? 'is-selected' : 'is-contrasted'}">
            {region.title}
        </span>
    </div>
{/each}
</div>

<!--TODO add selection for all other regions existing-->
<!--TODO add button to change number of displayed similar images (topk)-->
<!--TODO add a button to set a threshold for displayed score-->

<style>
    span {
        cursor: pointer;
        transition: background-color 0.2s ease-out;
    }
</style>
