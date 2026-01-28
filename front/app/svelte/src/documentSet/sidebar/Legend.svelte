<script>
    import LegendItem from "./LegendItem.svelte";
    import {appLang, model2title} from "../../constants.js";

    export let documentNodes;
    export let selectedRegions;
    export let toggleRegion;
    export let selectAllRegions;

    let isExpanded = true;

    let sortBy = 'id'; // 'id' | 'witnessId' | 'title'
    const sortWith = {
        id: (a, b) => a[0] - b[0],
        witnessId: (a, b) => (a[1].witnessId || 0) - (b[1].witnessId || 0),
        title: (a, b) => (a[1].title || '').localeCompare(b[1].title || '')
    };
    $: sortedDocs = Array.from(documentNodes || new Map()).sort(sortWith[sortBy]);
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
            <div class="level-item mb-0 field has-addons is-small">
                <p class="control mb-0" title={appLang === 'en' ? 'Sort documents by' : 'Trier les documents par'}>
                    <span class="select is-small">
                        <select bind:value={sortBy}>
                            <option value="id">ID</option>
                            <option value="witnessId">{model2title.Witness}</option>
                            <option value="title">{appLang === 'en' ? 'Title' : 'Titre'}</option>
                        </select>
                    </span>
                </p>
                <p class="control" title={appLang === 'en' ? 'Select all documents' : 'Sélectionner tous les documents'}>
                    <button class="button is-small is-shadowless" on:click={() => selectAllRegions()}>
                        <span class="icon is-small has-text-link pl-2">
                            <i class="fas fa-check"></i>
                        </span>
                    </button>
                </p>
            </div>
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
        {#each sortedDocs as [id, meta]}
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
