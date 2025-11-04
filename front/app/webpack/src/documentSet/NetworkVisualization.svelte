<script>
    import { onMount, onDestroy } from 'svelte';
    import { createNetwork } from './network.js';
    import Region from "../regions/Region.svelte";

    const width = 954;
    const height = 600;

    export let networkData;
    export let metadata;
    export let type;
    export let selectedNodes;
    export let updateSelectedNodes;

    let networkInstance;
    let container;

    $: if ($networkData && $networkData.nodes.length > 0 && container) {
        renderVisualization();
        console.log($networkData);
    }

    function renderVisualization() {
        if (networkInstance) {
            networkInstance.destroy();
        }

        if (type === "images") {
            networkInstance = createImageNetwork(container, $networkData);
        } else if (type === "documents") {
            networkInstance = createDocumentNetwork(container, $networkData);
        }
    }

    function createDocumentNetwork(div, networkData) {
        function onSelectionChange(selectedData) {
            updateSelectedNodes(selectedData);
        }
        return createNetwork(div, networkData.nodes, networkData.links, onSelectionChange);
    }

    function createImageNetwork(div, networkData) {
        function onSelectionChange(selectedData) {
            updateSelectedNodes(selectedData);
        }
        return createNetwork(div, networkData.nodes, networkData.links, onSelectionChange);
    }

    onDestroy(() => {
        networkInstance?.destroy();
    });
</script>

<div>
    <h2 class="title is-3 has-text-link">
        {type === "images" ? "Image regions network" : "Witness network"}
    </h2>

    <div bind:this={container} class="visualization-container"></div>

    {#if $selectedNodes.length > 0}
        <div class="selected-panel box mt-4">
            <h3 class="title is-5">Selected Nodes ({$selectedNodes.length})</h3>
            <div class="images-grid">
                {#each $selectedNodes as node (node.id)}
                    <Region item="{node}" selectable={false} copyable={false}/>
                {/each}
            </div>
        </div>
    {/if}
</div>

<style>
    .selected-panel {
        background-color: var(--bulma-scheme-main-bis);
    }

    .images-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
        gap: 1rem;
    }
</style>
