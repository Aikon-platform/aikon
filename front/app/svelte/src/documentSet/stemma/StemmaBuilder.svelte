<script>
    import { i18n } from '../../utils.js';
    import SplitLayout from '../../ui/SplitLayout.svelte';
    import StemmaVisualization from './StemmaVisualization.svelte';
    import DocumentSetMatrix from '../document-matrix/DocumentSetMatrix.svelte';
    import DocumentPairMatrix from '../document-matrix/DocumentPairMatrix.svelte';
    import PairDetailModal from '../document-matrix/PairDetailModal.svelte';
    import { createStemmaStore } from './stemmaStore.js';

    export let documentSetStore;

    const { normalizeByImages } = documentSetStore;

    const stemmaStore = createStemmaStore(documentSetStore);
    const {
        selectedNodes, edges, filteredDocuments, matrixScoreData,
        matrixDocStats, matrixImageCount, getFilteredPairsForDocPair
    } = stemmaStore;

    const t = {
        title: { en: 'Stemma Builder', fr: 'Éditeur de stemma' },
        hint: { en: 'Drag to move • Scroll to zoom • Shift+drag to connect', fr: 'Glisser pour déplacer • Défiler pour zoomer • Maj+glisser pour connecter' },
        order: { en: 'Order', fr: 'Ordre' },
        edges: { en: 'Connections', fr: 'Connexions' },
        normalize: {en: 'Normalize', fr: 'Normaliser'},
        normalization: {en: 'Normalization by document image counts', fr: "Normalisation par le nombre d'images des documents"},
        selectViz: { en: 'Select a visualization', fr: 'Choisir une visualisation' },
        docMatrix: { en: 'Document Matrix', fr: 'Matrice de documents' },
        noSelection: { en: 'Connect documents in the stemma to see visualizations', fr: 'Connectez des documents dans le stemma pour voir les visualisations' },
        noViz: { en: 'Select a visualization above', fr: 'Sélectionnez une visualisation ci-dessus' },
        byPage: { en: 'By page', fr: 'Par page' },
        byImage: { en: 'By image', fr: 'Par image' },
    };

    const vizOptions = [
        { id: 'docMatrix', label: t.docMatrix },
    ];
    const viz2Options = [
        //{ id: 'pairMatrix', label: t.pairMatrix },
    ];

    let selectedViz = '';
    let selectedViz2 = '';
    let selectedCell = null;
    let scatterMode = 'page';
    let modalActive = false;
    let navState = null;
    let scatterData = null;

    $: documentSetStore.updateSelectedNodes($selectedNodes.map(n => n.id));
    $: pairMatrixData = selectedCell ? {
        doc1: selectedCell.doc1,
        doc2: selectedCell.doc2,
        pairs: getFilteredPairsForDocPair(selectedCell.doc1.id, selectedCell.doc2.id)
    } : null;

    function handleEdgeCreate(e) {
        const { source, target } = e.detail;
        const srcDoc = $filteredDocuments.find(d => d.id === source);
        const tgtDoc = $filteredDocuments.find(d => d.id === target);
        stemmaStore.addEdge(source, target, srcDoc, tgtDoc);
    }

    function removeEdge(source, target) {
        stemmaStore.removeEdge(source, target);
    }

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
                        <span class="tag is-small" style="background-color: {node.color}; color: #222;">
                            <span class="mr-1">{idx + 1}.</span>
                            {node.title.length > 12 ? node.title.slice(0, 10) + '…' : node.title}
                        </span>
                    {/each}
                </div>
            </div>
        {/if}

        {#if $edges.length}
            <div class="edges-bar mb-2">
                <span class="is-size-7 has-text-grey mr-2">{i18n('edges', t)}:</span>
                <div class="is-flex is-flex-wrap-wrap" style="gap: 0.25rem;">
                    {#each $edges as edge}
                        <span class="tag is-small">
                            <span class="edge-dot" style="background: {edge.sourceColor}"></span>
                            →
                            <span class="edge-dot" style="background: {edge.targetColor}"></span>
                            <button class="delete is-small ml-1" on:click={() => removeEdge(edge.source, edge.target)}></button>
                        </span>
                    {/each}
                </div>
            </div>
        {/if}

        <div class="canvas-wrapper">
            <StemmaVisualization
                documents={$filteredDocuments}
                selectedNodes={$selectedNodes}
                edges={$edges}
                on:edgecreate={handleEdgeCreate}
            />
        </div>
    </div>

    <div slot="right-title" class="is-flex is-align-items-center" style="gap: 0.5rem;">
        <div class="select is-small">
            <select bind:value={selectedViz}>
                <option value="">{i18n('selectViz', t)}</option>
                {#each vizOptions as opt}
                    <option value={opt.id}>{i18n(opt.id, t)}</option>
                {/each}
            </select>
        </div>
        <div class="select is-small">
            <select bind:value={selectedViz2}>
                <option value="">{i18n('selectViz', t)}</option>
                {#each viz2Options as opt}
                    <option value={opt.id}>{i18n(opt.id, t)}</option>
                {/each}
            </select>
        </div>
        <label title={i18n('normalization', t)} class="checkbox is-size-7 is-flex is-align-items-center">
            <input type="checkbox" bind:checked={$normalizeByImages}>
            <span class="pl-1">{i18n('normalize', t)}</span>
        </label>
    </div>

    <div slot="right-scroll">
        {#if !selectedViz}
            <article class="message is-warning">
                <div class="message-body">{i18n('noViz', t)}</div>
            </article>
        {:else if !$selectedNodes.length}
            <article class="message is-warning">
                <div class="message-body">{i18n('noSelection', t)}</div>
            </article>
        {:else if selectedViz === 'docMatrix'}
            <!-- TODO order by selected documents-->
            <DocumentSetMatrix
                documents={$selectedNodes}
                scoreData={$matrixScoreData}
                docStats={$matrixDocStats}
                imageCountMap={$matrixImageCount}
                normalize={$normalizeByImages}
                on:cellselect={handleCellSelect}
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
    .selection-bar, .edges-bar {
        display: flex;
        align-items: center;
        flex-wrap: wrap;
        padding: 0.5rem;
        background: var(--bulma-scheme-main-bis);
        border-radius: 4px;
    }
    .edge-dot, .color-dot {
        width: 10px;
        height: 10px;
        border-radius: 50%;
        display: inline-block;
    }
    .edge-dot { margin: 0 2px; }
</style>
