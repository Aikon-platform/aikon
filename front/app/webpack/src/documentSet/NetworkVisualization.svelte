<script>
    import { onDestroy } from 'svelte';
    import { createNetwork } from './network.js';
    import Region from "../regions/Region.svelte";
    import AlignedMatrix from './AlignedMatrix.svelte';
    import { appLang } from '../constants.js';

    const width = 954;
    const height = 600;

    export let type = 'image';
    export let documentSetStore;
    const {
        imageNetwork,
        documentNetwork,
        selectedNodes,
        updateSelectedNodes,
    } = documentSetStore;

    let networkInstance;
    let container;
    let selectionMode = false;

    $: networkData = type === 'image' ? imageNetwork : documentNetwork;

    $: if ($networkData && container) {
        renderVisualization();
    }

    function renderVisualization() {
        if (networkInstance) {
            networkInstance.destroy();
            updateSelectedNodes([]);
        }

        function onSelectionChange(selectedData) {
            updateSelectedNodes(selectedData);
        }

        networkInstance = createNetwork(
            container,
            $networkData.nodes,
            $networkData.links,
            $networkData.stats,
            onSelectionChange,
            (mode) => { selectionMode = mode; },
            type
        );

        selectionMode = type === 'image';
        if (selectionMode) {
            networkInstance.toggleSelectionMode();
        }
    }

    function toggleSelectionMode() {
        if (networkInstance) {
            selectionMode = networkInstance.toggleSelectionMode();
        }
    }

    onDestroy(() => {
        networkInstance?.destroy();
    });
</script>

<div>
    <button class="toggle-button button is-small is-link mb-3"
        class:is-active={selectionMode}
        on:click={toggleSelectionMode}>
        {#if selectionMode}
            <span class="icon px-4">
                <i class="fas fa-hand-pointer"></i>
            </span>
        {:else}
            <span class="icon px-4">
                <i class="fas fa-crop-alt"></i>
            </span>
        {/if}
        Switch to {selectionMode ? 'click' : 'selection'} mode
    </button>

    <div bind:this={container} class="visualization-container"></div>

    {#if $selectedNodes.length > 0}
        {#if type === 'image'}
        <div class="selected-panel box mt-4">
            <h3 class="title is-5">{appLang === "en" ? 'Selected regions' : 'Régions sélectionnées'} ({$selectedNodes.length})</h3>
            <div class="selected-nodes grid is-gap-2 mt-5">
                {#each $selectedNodes as node (node.id)}
                    <Region item="{node}" selectable={false} copyable={false}/>
                {/each}
            </div>
        </div>
        {:else if type === 'document'}
            <AlignedMatrix selectedDocuments={$selectedNodes} {documentSetStore}/>
        {/if}
    {/if}
</div>

<style>
    .selected-panel {
        background-color: var(--bulma-scheme-main-bis);
    }

    .selected-nodes {
        grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
    }
</style>
