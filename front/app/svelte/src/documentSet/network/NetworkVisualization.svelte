<script>
   import { run } from 'svelte/legacy';

    import { onDestroy } from "svelte";
    import { createCanvas } from "./network-canvas.js";
    import { createSvg } from "./network-svg.js";
    import { appLang } from "../../constants.js";
    import Matches from "../Matches.svelte";
    import DownloadPng from "../../ui/DownloadPng.svelte";

   /**
    * @typedef {Object} Props
    * @property {string} [type]
    * @property {any} documentSetStore
    * @property {any} clusterStore
    */

   /** @type {Props} */
   let { type = "img", documentSetStore, clusterStore } = $props();

   const {
       imageNetwork, documentNetwork, selectedNodes, updateSelectedNodes,
       buildMatchesForAnchor, buildNetworkMatches, hideEmpty, pairCat
   } = documentSetStore;

    let networkInstance;
    let container = $state();
    let selectionMode = $state(false);
    const render_threshold = 500;




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

        selectionMode = type === "img";
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
    let networkData = $derived(type === "img" ? imageNetwork : documentNetwork);
    let tableData = $derived(!$selectedNodes.length
        ? { matches: [], columns: [] }
        : type === "doc"
            ? buildMatchesForAnchor($selectedNodes[0], $selectedNodes.slice(1), null, true)
            : buildNetworkMatches({
                baseDocId: $selectedNodes[0].digit,
                docIds: new Set($selectedNodes.map(n => n.digit)),
                imageIds: new Set($selectedNodes.map(n => n.id)),
            }));
   run(() => {
       if ($networkData && container) renderVisualization();
   });
</script>

<div>
    <div class="is-flex is-align-items-center mb-3" style="gap: 0.5rem;">
        <button class="toggle-button button is-small is-link is-light mb-0" onclick={toggleSelectionMode}>
            {#if selectionMode}
            <span class="icon px-4">
                <i class="fas fa-hand-pointer"></i>
            </span>
            {:else}
            <span class="icon px-4">
                <i class="fas fa-crop-alt"></i>
            </span>
            {/if}
            Switch to {selectionMode ? "click" : "selection"} mode
        </button>
        {#if type === "doc"}
            <DownloadPng targetId="doc-network" filename="document-network"
                         svgExport={$networkData?.nodes.length < render_threshold}/>
        {/if}
    </div>


    <div bind:this={container} id="{type}-network" class="visualization-container"></div>

    {#if $selectedNodes.length > 0}
        <div class="box mt-4">
            <h3 class="title is-5">
                {type === "img"
                    ? (appLang === "en" ? "Selected regions" : "Régions sélectionnées")
                    : (appLang === "en" ? "Aligned documents" : "Documents alignés")}
                ({$selectedNodes.length})
            </h3>
            <Matches matches={tableData.matches} columns={tableData.columns}
                     hideEmpty={$hideEmpty} {clusterStore} pairCat={$pairCat}/>
        </div>
    {/if}
</div>
