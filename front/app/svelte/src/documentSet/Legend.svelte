<script>
    import LegendItem from "./LegendItem.svelte";
    import {appLang} from "../constants.js";

    export let documentNodes;
    export let selectedRegions;
    export let toggleRegion;

    let isExpanded = true;
</script>

<div>
    <div class="level is-mobile mb-3">
        <div class="level-left">
            <div class="level-item">
                <h3 class="title mb-0">
                    {appLang === 'en' ? 'Visible documents' : 'Documents visibles'}
                </h3>
            </div>
        </div>
        <div class="level-right">
            <div class="level-item" title={isExpanded ? 'Minify legend' : 'Expand legend'}>
                <button class="button is-small is-ghost" on:click={() => isExpanded = !isExpanded}
                        aria-label={isExpanded ? 'Minify legend' : 'Expand legend'}>
                    {#if isExpanded}
                        <span class="icon is-small">
                            <i class="fas fa-chevron-up"></i>
                        </span>
                    {:else}
                        <span class="icon is-small">
                            <i class="fas fa-chevron-down"></i>
                        </span>
                    {/if}
                </button>
            </div>
        </div>
    </div>

    <div class:is-condensed={!isExpanded} class:is-expanded={isExpanded}>
        {#each Array.from(documentNodes || new Map()) as [id, meta]}
            <LegendItem {id} {meta}
                isActive={selectedRegions.has(parseInt(id))}
                toggle={() => toggleRegion(parseInt(id))}
                onlyColor={!isExpanded}/>
        {/each}
    </div>
</div>

<style>
    .is-condensed {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(24px, 1fr));
        gap: 0.5rem;
    }
    .is-expanded {
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
    }
</style>
