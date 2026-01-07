<script>
    import { onDestroy } from 'svelte';
    import { createCanvas } from './network-canvas.js';
    import { createSvg } from './network-svg.js';
    import Region from "../regions/Region.svelte";
    import AlignedMatrix from './AlignedMatrix.svelte';
    import { appLang } from '../constants.js';

    export let type = 'img';
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
    const render_threshold = 1000;

    $: networkData = type === 'img' ? imageNetwork : documentNetwork;

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

        const createNetwork = $networkData.nodes.length < render_threshold ? createSvg : createCanvas;

        networkInstance = createNetwork(
            container,
            $networkData.nodes,
            $networkData.links,
            onSelectionChange,
            (mode) => { selectionMode = mode; },
        );

        selectionMode = type === 'img';
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
        {#if type === 'img'}
        <div class="selected-panel box mt-4">
            <h3 class="title is-5">{appLang === "en" ? 'Selected regions' : 'Régions sélectionnées'} ({$selectedNodes.length})</h3>
            <div class="selected-nodes grid is-gap-2 mt-5">
                {#each $selectedNodes as node (node.id)}
                    <Region item="{node}" selectable={false} copyable={false}/>
                {/each}
            </div>
        </div>
        {:else if type === 'doc'}
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
