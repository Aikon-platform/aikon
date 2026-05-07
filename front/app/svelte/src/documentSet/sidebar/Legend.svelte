<script>
    import LegendItem from "./LegendItem.svelte";
    import {appLang} from "../../constants.js";
    import {i18n} from "../../utils.js";

    export let sortedDocs;
    export let docSort;
    export let selectedDocuments;
    export let toggleDoc;
    export let selectAllDocuments;

    let isExpanded = true;

    $: selectedDocs = sortedDocs.filter(([id]) => selectedDocuments.has(parseInt(id)));
</script>

<div>
    <h3 class="title mb-3">
        {appLang === "en" ? "Visible documents" : "Documents visibles"} ({selectedDocs.length || 0})
    </h3>
    <div class="level is-mobile mb-4">
        <div class="level-left">
            <div class="level-item">
                <div class="level-item mb-0 field has-addons is-small">
                    <p class="control mb-0" title={appLang === "en" ? "Sort documents by" : "Trier les documents par"}>
                        <span class="select is-small">
                            <select bind:value={$docSort}>
                                <option value="id">ID</option>
                                <option value="witnessId">{i18n('Witness')}</option>
                                <option value="title">{i18n('title')}</option>
                                <option value="date">{i18n('date')}</option>
                            </select>
                        </span>
                    </p>
                    <p class="control" title={appLang === "en" ? "Select all documents" : "Sélectionner tous les documents"}>
                        <button class="button is-small is-shadowless" on:click={() => selectAllDocuments()}>
                            {appLang === "en" ? "Select all" : "Tout sélectionner"}
                            <span class="icon is-small has-text-link pl-5 pr-1">
                                <i class="fas fa-check"/>
                            </span>
                        </button>
                    </p>
                </div>
            </div>
        </div>
        <div class="level-right">
            <div class="level-item" title={isExpanded ? "Minify legend" : "Expand legend"}>
                <button class="button is-small is-ghost" on:click={() => isExpanded = !isExpanded}
                        aria-label={isExpanded ? "Minify legend" : "Expand legend"}>
                    {#if isExpanded}
                        <span class="icon is-small">
                            <i class="fas fa-chevron-up"/>
                        </span>
                    {:else}
                        <span class="icon is-small">
                            <i class="fas fa-chevron-down"/>
                        </span>
                    {/if}
                </button>
            </div>
        </div>
    </div>

    <div class:is-condensed={!isExpanded} class:is-expanded={isExpanded}>
        {#each sortedDocs as [id, meta]}
            <LegendItem {id} {meta}
                isActive={selectedDocuments.has(parseInt(id))}
                toggle={() => toggleDoc(parseInt(id))}
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
