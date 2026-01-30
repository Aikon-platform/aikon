<script>
    import {i18n} from '../../utils.js';
    import DownloadPng from "../../ui/DownloadPng.svelte";
    import SplitLayout from "../../ui/SplitLayout.svelte";
    import DocumentSetMatrix from "./DocumentSetMatrix.svelte";
    import DocumentPairMatrix from "./DocumentPairMatrix.svelte";
    import PairDetailModal from "./PairDetailModal.svelte";

    export let documentSetStore;

    const {
        documentNodes, pairIndex, filteredDocPairStats, filteredDocStats,
        imageCountMap, visiblePairIds, normalizeByImages
    } = documentSetStore;

    const t = {
        title: {en: 'Document Matrix', fr: 'Matrice de documents'},
        byName: {en: 'By title', fr: 'Par titre'},
        byScore: {en: 'By score', fr: 'Par score'},
        noDocuments: {en: 'No documents available', fr: 'Aucun document disponible'},
        pageByPage: {en: 'Page-by-page similarity', fr: 'Similarité page par page'},
        selectCell: {en: 'Click a cell to view page-by-page similarity', fr: 'Cliquez sur une cellule pour voir la similarité page par page'},
        byPage: {en: 'By page', fr: 'Par page'},
        byImage: {en: 'By image', fr: 'Par image'},
        normalize: {en: 'Normalize', fr: 'Normaliser'},
        normalization: {en: 'Normalization by document image counts', fr: "Normalisation par le nombre d'images des documents"},
        allPairs: {en: 'All pairs in the document set', fr: 'Toutes les paires du corpus'},
        filteredPairs: {en: 'Filtered pairs', fr: 'Paires après filtrage'},
        filtering: {en: 'Source of image pairs for the visualizations', fr: "Source des paires d'images pour les visualisations"},
    };

    let selectedCell = null;
    let sortOrder = 'name';
    let scatterMode = 'page';
    let navState = null;
    let modalActive = false;
    let scatterData = null;

    $: documents = Array.from($documentNodes?.values() || []);
    $: pairsForSelection = selectedCell ? getPairsForCell(selectedCell, $visiblePairIds) : [];

    function getPairsForCell(cell, visibleIds) {
        const {doc1, doc2} = cell;
        const pairKey = doc1.id < doc2.id ? `${doc1.id}-${doc2.id}` : `${doc2.id}-${doc1.id}`;
        let pairs = $pairIndex.byDocPair.get(pairKey) || [];
        if (visibleIds.size > 0) pairs = pairs.filter(p => visibleIds.has(`${p.id_1}-${p.id_2}`));
        return pairs;
    }

    function handleCellSelect(e) {
        selectedCell = e.detail;
    }

    function handleScatterClick(e) {
        navState = {idx1: e.detail.idx1, idx2: e.detail.idx2};
        scatterData = e.detail.data;
        modalActive = true;
    }

    function handleModalNavigate(e) {
        navState = {...e.detail};
    }

    function handleModalClose() {
        modalActive = false;
    }
</script>

{#if !documents.length}
    <div class="container">
        <div class="notification is-info" style="width: 100%">{i18n('noDocuments', t)}</div>
    </div>
{:else}
    <SplitLayout>
        <div slot="left-title" class="is-flex is-justify-content-space-between">
            <h4 class="title is-6 mb-0">{i18n('title', t)}</h4>
            <div class="is-flex is-align-items-center" style="gap: 0.5rem;">
                <DownloadPng targetId="matrix-viz" filename="document-matrix.png" />
                <div class="control">
                    <div class="select is-small">
                        <select bind:value={sortOrder}>
                            <option value="name">{i18n('byName', t)}</option>
                            <option value="score">{i18n('byScore', t)}</option>
                        </select>
                    </div>
                </div>
                <label title={i18n('normalization', t)} class="checkbox is-size-7 is-flex is-align-items-center">
                    <input type="checkbox" checked={$normalizeByImages} on:change={e => normalizeByImages.set(e.target.checked)}>
                    <span class="pl-1">{i18n('normalize', t)}</span>
                </label>
            </div>
        </div>
        <div slot="left-scroll" id="matrix-viz">
            <DocumentSetMatrix
                {documents} {sortOrder}
                scoreData={$filteredDocPairStats.scoreCount}
                docStats={$filteredDocStats.scoreCount}
                imageCountMap={$imageCountMap}
                normalize={$normalizeByImages}
                on:cellselect={handleCellSelect}
            />
        </div>
        <div slot="right-title" class="is-flex is-justify-content-space-between">
            <h4 class="title is-6 mb-0">{i18n('pageByPage', t)}</h4>
            <div class="is-flex is-align-items-center" style="gap: 0.5rem;">
                {#if selectedCell}
                    <DownloadPng targetId="scatter-viz" filename="document-comparison.png"/>
                    <div class="control">
                        <div class="select is-small">
                            <select bind:value={scatterMode}>
                                <option value="page">{i18n('byPage', t)}</option>
                                <option value="image">{i18n('byImage', t)}</option>
                            </select>
                        </div>
                    </div>
                {/if}
            </div>
        </div>
        <div slot="right-scroll" id="scatter-viz">
            {#if selectedCell}
                <DocumentPairMatrix
                    doc1={selectedCell.doc1}
                    doc2={selectedCell.doc2}
                    pairs={pairsForSelection}
                    mode={scatterMode}
                    on:cellclick={handleScatterClick}
                />
            {:else}
                <p class="has-text-grey is-size-7">{i18n('selectCell', t)}</p>
            {/if}
        </div>
    </SplitLayout>
{/if}

<PairDetailModal
    active={modalActive} {scatterData} {navState}
    on:navigate={handleModalNavigate}
    on:close={handleModalClose}
/>
