<script>
    import { i18n } from '../../utils.js';
    import { parseImgRef } from '../../regions/types.js';
    import SplitLayout from '../../ui/SplitLayout.svelte';
    import StemmaEditor from './StemmaEditor.svelte';
    import DocumentSetMatrix from '../document-matrix/DocumentSetMatrix.svelte';
    import DocumentPairMatrix from '../document-matrix/DocumentPairMatrix.svelte';
    import PairDetailModal from '../document-matrix/PairDetailModal.svelte';
    import { createStemmaStore } from './stemmaStore.js';
    import SpatialFrieze from "./SpatialFrieze.svelte";
    import ImageStemma from "./ImageStemma.svelte";

    export let documentSetStore;

    const {
        normalizeByImages, visiblePairs, documentNodes, imageNodes,
        filteredDocPairStats, filteredDocStats, imageCountMap
    } = documentSetStore;

    const stemmaStore = createStemmaStore(documentSetStore);
    const {
        selectedNodes, filteredDocuments, matrixScoreData, matrixDocStats,
        matrixImageCount, getFilteredPairsForDocPair, nodeTitles
    } = stemmaStore;

    const t = {
        title: { en: 'Stemma Builder', fr: 'Éditeur de stemma' },
        hint: { en: 'Drag to move • Scroll to zoom • Shift+drag to connect', fr: 'Glisser pour déplacer • Défiler pour zoomer • Maj+glisser pour connecter' },
        order: { en: 'Order', fr: 'Ordre' },
        edges: { en: 'Connections', fr: 'Connexions' },
        normalize: {en: 'Normalize', fr: 'Normaliser'},
        normalization: {en: 'Normalization by document image counts', fr: "Normalisation par le nombre d'images des documents"},
        noSelection: { en: 'Connect documents in the stemma to see visualizations', fr: 'Connectez des documents dans le stemma pour voir les visualisations' },
        noViz: { en: 'Select a visualization above', fr: 'Sélectionnez une visualisation ci-dessus' },
        byPage: { en: 'By page', fr: 'Par page' },
        byImage: { en: 'By image', fr: 'Par image' },
        selectedDocs: { en: 'Selected documents', fr: 'Documents sélectionnés' },
        fullDocSet: { en: 'Full document set', fr: 'Jeu de documents complet' },

        selectViz: { en: 'Select a visualization', fr: 'Choisir une visualisation' },
        docMatrix: { en: 'Document Matrix', fr: 'Matrice de documents' },
        spatialFrieze: { en: 'Spatial Frieze', fr: 'Frise spatiale' },
    };

    const vizOptions = [
        { id: 'spatialFrieze', label: t.spatialFrieze },
        { id: 'docMatrix', label: t.docMatrix },
    ];

    let selectedViz = '';
    let selectedCell = null;
    let selectedFriezeImage = null;
    let scatterMode = 'page';
    let friezeMode = 'image';
    let modalActive = false;
    let navState = null;
    let scatterData = null;
    let matrixScope = 'full';

    $: documentSetStore.updateSelectedNodes($selectedNodes.map(n => n.id));
    $: pairMatrixData = selectedCell ? {
        doc1: selectedCell.doc1,
        doc2: selectedCell.doc2,
        pairs: getFilteredPairsForDocPair(selectedCell.doc1.id, selectedCell.doc2.id)
    } : null;

    function handleCellSelect(e) {
        selectedCell = e.detail;
    }

    function handleScatterClick(e) {
        navState = { idx1: e.detail.idx1, idx2: e.detail.idx2 };
        scatterData = e.detail.data;
        modalActive = true;
    }

    function handleModalNavigate(e) {
        navState = { ...e.detail };
    }

    function handleModalClose() {
        modalActive = false;
    }

    function handleFriezeImageSelect(e) {
        selectedFriezeImage = e.detail;
    }

    $: fullDocuments = Array.from($documentNodes?.values() || []);
    $: fullScoreData = $filteredDocPairStats?.scoreCount || new Map();
    $: fullDocStats = $filteredDocStats?.scoreCount || new Map();
    $: friezeDocuments = matrixScope === 'full' ? fullDocuments : $selectedNodes;

    function handleVizChange() {
        selectedCell = null;
        selectedFriezeImage = null;
    }

    $: needsSelection = selectedViz && !$selectedNodes.length && matrixScope !== 'full';
</script>

<SplitLayout>
    <div slot="left-title" class="is-flex is-justify-content-space-between is-align-items-center">
        <h4 class="title is-6 mb-0">{i18n('title', t)}</h4>
        <span class="tag is-small">{i18n('hint', t)}</span>
    </div>
    <div slot="left-scroll" class="stemma-panel">
        {#if $selectedNodes.length}
            <div class="selection-bar mb-2">
                <span class="is-size-7 has-text-grey mr-2">{i18n('order', t)}:</span>
                <div class="is-flex is-flex-wrap-wrap" style="gap: 0.25rem;">
                    {#each $selectedNodes as node, idx (node.id)}
                        {@const title = $nodeTitles[node.id] || node.title}
                        <span class="tag is-small" style="background-color: {node.color}; color: #222;">
                            <span class="mr-1">{idx + 1}.</span>
                            {title.length > 12 ? title.slice(0, 10) + '…' : title}
                        </span>
                    {/each}
                </div>
            </div>
        {/if}

        <div class="canvas-wrapper">
            <StemmaEditor documents={$filteredDocuments} {stemmaStore}/>
        </div>
    </div>

    <div slot="right-title" class="is-flex is-align-items-center" style="gap: 0.5rem;">
        <div class="select is-small">
            <select bind:value={selectedViz} on:change={handleVizChange}>
                <option value="">{i18n('selectViz', t)}</option>
                {#each vizOptions as opt}
                    <option value={opt.id}>{i18n(opt.id, t)}</option>
                {/each}
            </select>
        </div>
        {#if selectedViz}
            <div class="select is-small">
                <select bind:value={matrixScope}>
                    <option value="selected">{i18n('selectedDocs', t)}</option>
                    <option value="full">{i18n('fullDocSet', t)}</option>
                </select>
            </div>
        {/if}
        {#if selectedViz === 'docMatrix'}
            <label title={i18n('normalization', t)} class="checkbox is-size-7 is-flex is-align-items-center">
                <input type="checkbox" bind:checked={$normalizeByImages}>
                <span class="pl-1">{i18n('normalize', t)}</span>
            </label>
        {:else if selectedViz === 'spatialFrieze'}
            <div class="select is-small">
                <select bind:value={friezeMode}>
                    <option value="page">{i18n('byPage', t)}</option>
                    <option value="image">{i18n('byImage', t)}</option>
                </select>
            </div>
        {/if}
    </div>

    <div slot="right-scroll">
        {#if !selectedViz}
            <p class="has-text-grey is-size-7">{i18n('noViz', t)}</p>
        {:else if needsSelection}
            <p class="has-text-grey is-size-7">{i18n('noSelection', t)}</p>
        {:else if selectedViz === 'docMatrix'}
            <DocumentSetMatrix
                documents={matrixScope === 'full' ? fullDocuments : $selectedNodes}
                scoreData={matrixScope === 'full' ? fullScoreData : $matrixScoreData}
                docStats={matrixScope === 'full' ? fullDocStats : $matrixDocStats}
                imageCountMap={matrixScope === 'full' ? $imageCountMap : $matrixImageCount}
                normalize={$normalizeByImages}
                on:cellselect={handleCellSelect}
            />
        {:else if selectedViz === 'spatialFrieze'}
            <SpatialFrieze
                documents={friezeDocuments}
                {visiblePairs}
                {documentNodes}
                {stemmaStore}
                mode={friezeMode}
                on:imageselect={handleFriezeImageSelect}
            />
        {/if}
    </div>

    <div slot="bottom-right-title" class="is-flex is-justify-content-space-between">
        {#if pairMatrixData}
            <h4 class="title is-6 mb-0">
                <span class="color-dot" style="background: {pairMatrixData.doc1.color}"/>
                <span class="has-text-grey">↔</span>
                <span class="color-dot" style="background: {pairMatrixData.doc2.color}"/>
            </h4>
            <div class="select is-small">
                <select bind:value={scatterMode}>
                    <option value="page">{i18n('byPage', t)}</option>
                    <option value="image">{i18n('byImage', t)}</option>
                </select>
            </div>
        {:else if selectedFriezeImage}
            {@const baseDoc = $selectedNodes.find(d => d.id === selectedFriezeImage.baseDocId)}
            {@const title = $nodeTitles[selectedFriezeImage.baseDocId] || baseDoc?.title}
            {@const imgData = parseImgRef(selectedFriezeImage.imageId)}
            <h4 class="title is-6 mb-0">
                <span>Image stemma from</span>
                <span class="color-dot" style="background: {baseDoc?.color}"></span>
                {title ?? 'Unknown'}
                (canvas {imgData.canvasNb})
            </h4>
        {/if}
    </div>
    <div slot="bottom-right-scroll">
        {#if pairMatrixData}
            <DocumentPairMatrix
                doc1={pairMatrixData.doc1}
                doc2={pairMatrixData.doc2}
                pairs={pairMatrixData.pairs}
                mode={scatterMode}
                on:cellclick={handleScatterClick}
            />
        {:else if selectedFriezeImage}
            <ImageStemma
                {stemmaStore}
                {visiblePairs}
                {imageNodes}
                documents={friezeDocuments}
                startImageId={selectedFriezeImage.imageId}
                baseDocId={selectedFriezeImage.baseDocId}
            />
        {/if}
    </div>
</SplitLayout>

<PairDetailModal
    active={modalActive} {scatterData} {navState}
    on:navigate={handleModalNavigate}
    on:close={handleModalClose}
/>

<style>
    .stemma-panel {
        display: flex;
        flex-direction: column;
        height: 100%;
    }
    .canvas-wrapper {
        flex: 1;
        min-height: 400px;
        position: relative;
    }
    .selection-bar {
        display: flex;
        align-items: center;
        flex-wrap: wrap;
        padding: 0.5rem;
        background: var(--bulma-scheme-main-bis);
        border-radius: 4px;
    }
    .color-dot {
        width: 10px;
        height: 10px;
        border-radius: 50%;
        display: inline-block;
    }
</style>
